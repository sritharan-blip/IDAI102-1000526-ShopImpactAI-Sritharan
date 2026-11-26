"""Google sign-in and account-scoped workspace persistence."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from time import time

import streamlit as st

GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
GOOGLE_METADATA = "https://accounts.google.com/.well-known/openid-configuration"
LIST_FIELDS = ("purchases", "wishlist", "comparison_basket", "saved_swaps")
PREF_FIELDS = ("monthly_budget", "monthly_target", "appearance", "high_contrast", "reduce_motion",
               "account_personalization")
SCHEMA_VERSION = 1


class SaveConflict(Exception):
    """A newer revision was saved by another session."""


def cloud_settings():
    """Use demo mode locally unless account mode is requested or secrets are present."""
    required = os.environ.get("SHOPIMPACT_REQUIRE_ACCOUNT") == "1"
    try:
        auth = st.secrets.get("auth", {})
        database = st.secrets.get("cloud", {})
    except FileNotFoundError:
        auth, database = {}, {}
    if not (required or auth or database):
        return None
    if (not all(auth.get(key) for key in ("client_id", "client_secret", "cookie_secret", "redirect_uri"))
            or auth.get("server_metadata_url") != GOOGLE_METADATA
            or not database.get("dsn")):
        st.error("Google sign-in and cloud storage still need to be configured for this deployment.")
        st.stop()
    return database["dsn"]


def account_id(user) -> str | None:
    # Google guarantees the subject is stable for an account. An email address can change.
    if not user.is_logged_in or user.get("iss") not in GOOGLE_ISSUERS:
        return None
    subject, expires = user.get("sub"), user.get("exp")
    if not isinstance(subject, str) or not subject or not isinstance(expires, (int, float)) or not expires > time():
        return None
    return sha256(f"google:{subject}".encode("utf-8")).hexdigest()


def workspace(state) -> dict:
    return {
        "version": SCHEMA_VERSION,
        **{key: state.get(key, []) for key in LIST_FIELDS},
        "cart": state.get("cart", {}),
        # Keep the demo order history, but leave delivery address fields in the session.
        "orders": [{key: value for key, value in order.items() if key not in ("city", "postal_code")}
                   for order in state.get("orders", [])],
        **{key: state[key] for key in PREF_FIELDS if key in state},
    }


def restore_workspace(state, payload: dict) -> None:
    if payload and payload.get("version") != SCHEMA_VERSION:
        raise ValueError("Unsupported workspace version")
    for key in (*LIST_FIELDS, "cart", "orders", *PREF_FIELDS):
        if key in payload:
            state[key] = payload[key]


def _connect(dsn: str):
    import psycopg

    return psycopg.connect(dsn, connect_timeout=5, sslmode="verify-full", sslrootcert="system",
                           options="-c statement_timeout=5000")


def load_workspace(dsn: str, owner: str) -> tuple[int, dict]:
    with _connect(dsn) as conn:
        row = conn.execute(
            "SELECT revision, payload FROM shopimpact_workspaces WHERE owner = %s",
            (owner,),
        ).fetchone()
    return row if row is not None else (0, {})


def write_workspace(dsn: str, owner: str, revision: int, snapshot: str) -> int:
    # The revision check and write are atomic, including the first save in a new account.
    with _connect(dsn) as conn:
        if revision == 0:
            result = conn.execute(
                "INSERT INTO shopimpact_workspaces (owner, revision, payload) VALUES (%s, 1, %s::jsonb) "
                "ON CONFLICT (owner) DO NOTHING RETURNING revision",
                (owner, snapshot),
            )
        else:
            result = conn.execute(
                "UPDATE shopimpact_workspaces SET revision = revision + 1, payload = %s::jsonb "
                "WHERE owner = %s AND revision = %s RETURNING revision",
                (snapshot, owner, revision),
            )
        row = result.fetchone()
        if row is None:
            raise SaveConflict
    return row[0]


def _snapshot() -> str:
    return json.dumps(workspace(st.session_state), sort_keys=True, separators=(",", ":"), allow_nan=False)


def open_workspace(dsn: str, owner: str) -> None:
    state = st.session_state
    if state.get("_cloud_owner") == owner:
        return
    # Authentication starts a new session. Clear existing values if an identity ever changes in-place.
    if state.get("_cloud_owner") is not None:
        state.clear()
    try:
        revision, payload = load_workspace(dsn, owner)
        restore_workspace(state, payload)
        state._cloud_snapshot = _snapshot()
        state._cloud_revision = revision
        state._cloud_owner = owner
    except Exception:
        st.error("Your cloud workspace could not be opened. Try again in a moment.")
        st.button("Retry cloud connection")
        st.stop()


def save_workspace(dsn: str, owner: str, status) -> bool:
    state = st.session_state
    if state.get("_cloud_conflict"):
        return False
    try:
        snapshot = _snapshot()
        if snapshot != state._cloud_snapshot:
            state._cloud_revision = write_workspace(dsn, owner, state._cloud_revision, snapshot)
            state._cloud_snapshot = snapshot
    except SaveConflict:
        state._cloud_conflict = True
        status.error("This account changed in another tab. Your changes here have not synced. Download a backup before reloading.")
        return False
    except Exception:
        status.warning("Cloud save failed. Keep this tab open and use Retry cloud save in the sidebar.")
        return False
    status.caption("Cloud save is up to date.")
    return True
