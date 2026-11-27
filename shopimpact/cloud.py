"""Account-scoped workspace persistence."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st

LIST_FIELDS = ("purchases", "wishlist", "comparison_basket", "saved_swaps")
PREF_FIELDS = ("monthly_budget", "monthly_target", "appearance", "high_contrast", "reduce_motion",
               "account_personalization")
SCHEMA_VERSION = 1


class SaveConflict(Exception):
    """A newer revision was saved by another session."""


class CloudConfigurationError(Exception):
    """This deployment requires credentials that haven't been configured."""


def cloud_settings():
    """Allow the demo when no account configuration is present."""
    required = os.environ.get("SHOPIMPACT_REQUIRE_ACCOUNT") == "1"
    try:
        database = st.secrets.get("cloud", {})
    except FileNotFoundError:
        database = {}
    if not (required or database):
        return None
    if not database.get("dsn"):
        raise CloudConfigurationError
    return database["dsn"]


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


@contextmanager
def _connect(dsn: str):
    import certifi
    import psycopg

    database = st.secrets.get("cloud", {})
    certificate = database.get("ca_certificate", "")
    with TemporaryDirectory(prefix="shopimpact-db-") as directory:
        root = certifi.where()
        if certificate:
            root = str(Path(directory) / "provider-ca.pem")
            Path(root).write_text(certificate, encoding="ascii")
        # Set the timeout after connecting so database proxies can handle startup normally.
        with psycopg.connect(dsn, connect_timeout=12, sslmode="verify-full", sslrootcert=root) as conn:
            conn.execute("SET LOCAL statement_timeout = '5s'")
            yield conn


def load_workspace(dsn: str, owner: str) -> tuple[int, dict]:
    with _connect(dsn) as conn:
        row = conn.execute(
            "SELECT revision, payload FROM shopimpact_private.shopimpact_workspaces WHERE owner = %s",
            (owner,),
        ).fetchone()
    return row if row is not None else (0, {})


def write_workspace(dsn: str, owner: str, revision: int, snapshot: str) -> int:
    # The revision check and write are atomic, including the first save in a new account.
    with _connect(dsn) as conn:
        if revision == 0:
            result = conn.execute(
                "INSERT INTO shopimpact_private.shopimpact_workspaces (owner, revision, payload) VALUES (%s, 1, %s::jsonb) "
                "ON CONFLICT (owner) DO NOTHING RETURNING revision",
                (owner, snapshot),
            )
        else:
            result = conn.execute(
                "UPDATE shopimpact_private.shopimpact_workspaces SET revision = revision + 1, payload = %s::jsonb "
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
