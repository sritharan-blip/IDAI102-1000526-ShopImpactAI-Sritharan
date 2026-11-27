"""ShopImpact app."""
from __future__ import annotations

import logging

import streamlit as st
from .catalog import MONTHLY_CO2_TARGET
from .navigation import _load_demo_data
from .data import _make_data_backup, _parse_data_backup
from .insights import _render_analytics, _render_overview, _render_rewards, _render_swap_studio
from .marketplace import _render_cart, _render_catalog, _render_help_and_returns, _render_orders, _render_profile
from .ledger import _render_purchase_view
from .wishlist import _render_wishlist
from .theme import apply_custom_css
from .accounts import AccountInputError, authenticate
from .cloud import CloudConfigurationError, cloud_settings, open_workspace, save_workspace
from .earth import render_earth, render_earth_background


def _keep_appearance_selected() -> None:
    """Segment controls can be deselected; keep appearance a two-way choice."""
    mode = st.session_state.get('appearance')
    if mode is None:
        st.session_state.appearance = st.session_state.get('last_appearance', 'Daylight')
    else:
        st.session_state.last_appearance = mode
    st.session_state.dark_mode = st.session_state.appearance == 'Midnight'


def main() -> None:
    st.set_page_config(page_title="ShopImpact | A little more intentional", page_icon=":material/eco:",
                       layout="wide", initial_sidebar_state="expanded")
    try:
        dsn = cloud_settings()
    except CloudConfigurationError:
        _render_sign_in(None)
        return
    if dsn is None:
        if st.session_state.get("_demo_entry"):
            _render_dashboard()
        else:
            _render_sign_in(None, demo_available=True)
        return

    owner = st.session_state.get("_account_id")
    if owner is None:
        _render_sign_in(dsn)
        return
    open_workspace(dsn, owner)

    with st.sidebar:
        if st.button("Sign out", icon=":material/logout:", key="account_sign_out", width="stretch"):
            if save_workspace(dsn, owner, st.empty()):
                st.session_state.clear()
                st.rerun()
            st.warning("Your session is open so you can recover any unsaved changes.")
        if st.session_state.get("_cloud_conflict"):
            st.error("Cloud sync is paused. Another tab saved a newer version.")
            if st.button("Discard this tab’s edits and reload from cloud", key="cloud_reload"):
                name = st.session_state._account_name
                st.session_state.clear()
                st.session_state._account_id = owner
                st.session_state._account_name = name
                st.rerun()
        else:
            st.button("Retry cloud save", key="cloud_retry", width="stretch")
        status = st.empty()
    # Streamlit's immediate reruns still execute finally, so checkout and restore
    # changes are saved along with ordinary widget changes.
    crashed = False
    try:
        _render_dashboard()
    except Exception:
        crashed = True
        raise
    finally:
        if not crashed:
            save_workspace(dsn, owner, status)


def _render_sign_in(dsn: str | None, *, demo_available: bool = False) -> None:
    apply_custom_css(False)
    render_earth_background("Sign in", False)
    _, card, _ = st.columns([1, 3.6, 1])
    with card, st.container(border=True, key="shopimpact_signin"):
        st.title("Sign in to ShopImpact")
        if dsn is None:
            st.warning("Account storage is offline. Sign-in and account creation are unavailable until the database is connected.")
        mode = st.radio("Account", ["Sign in", "Create account"], horizontal=True, label_visibility="collapsed")
        registering = mode == "Create account"
        with st.form("account_credentials", clear_on_submit=True):
            name = st.text_input("Name", max_chars=80) if registering else None
            email = st.text_input("Email", max_chars=254)
            password = st.text_input("Password", type="password", max_chars=128,
                                     help="Use at least 15 characters and a password unique to ShopImpact." if registering else None)
            submit = st.form_submit_button(mode, type="primary", width="stretch", disabled=dsn is None)
        if submit and dsn:
            try:
                owner, display_name = authenticate(dsn, email, password, st.context.ip_address, name=name)
            except AccountInputError as exc:
                st.error(str(exc))
            except Exception as exc:
                # Log the failure category without credentials, user data, or raw driver messages.
                detail = str(exc).lower()
                checks = (("certificate", "TLS"), ("password authentication failed", "credentials"),
                          ("timeout", "timeout"), ("does not exist", "database or schema"),
                          ("permission denied", "database permissions"), ("could not connect", "network"))
                category = next((label for marker, label in checks if marker in detail), type(exc).__name__)
                logging.getLogger(__name__).warning("Account storage failure: %s (SQLSTATE %s)",
                                                    category, getattr(exc, "sqlstate", None) or "none")
                st.error("Account storage is unavailable right now. Please try again shortly.")
            else:
                st.session_state.clear()
                st.session_state._account_id = owner
                st.session_state._account_name = display_name
                st.rerun()
        if demo_available and st.button("Explore the demo", key="start_demo", width="stretch"):
            st.session_state._demo_entry = True
            st.rerun()
        if demo_available:
            st.caption("Demo changes are kept for this session.")
        render_earth(on_login=True)


def _render_dashboard() -> None:
    st.session_state.setdefault("purchases", [])
    st.session_state.setdefault("last_added_id", None)
    st.session_state.setdefault("wishlist", [])
    st.session_state.setdefault("cart", {})
    st.session_state.setdefault("orders", [])
    st.session_state.setdefault("return_requests", [])
    st.session_state.setdefault("support_requests", [])
    st.session_state.setdefault("profile", None)
    st.session_state.setdefault("dark_mode", False)
    st.session_state.setdefault("high_contrast", False)
    st.session_state.setdefault("reduce_motion", False)
    st.session_state.setdefault("appearance", "Daylight")
    st.session_state.setdefault("monthly_budget", 600.0)
    st.session_state.setdefault("monthly_target", MONTHLY_CO2_TARGET)
    # Paint the active palette before emitting any interactive UI on each rerun.
    st.session_state.dark_mode = st.session_state.get('appearance', 'Daylight') == 'Midnight'
    apply_custom_css(st.session_state.dark_mode, st.session_state.high_contrast, st.session_state.reduce_motion)
    heading, quick, appearance = st.columns([1.35, .7, 1])
    with heading:
        st.html('<div class="si-topline"><span class="si-live-dot"></span>SHOPIMPACT <span>/</span> YOUR PERSONAL IMPACT SPACE</div>')
    with quick:
        with st.popover('Quick actions', icon=':material/bolt:', width='stretch'):
            from .navigation import _navigate_to
            for destination, label in [('Log purchase', 'Log a purchase'), ('Discover', 'Explore smart matches'),
                                       ('Decision lab', 'Open Decision lab'), ('Wishlist', 'Open wishlist')]:
                st.button(label, key='quick_' + destination, on_click=_navigate_to, args=(destination,), width='stretch')
    with appearance:
        st.segmented_control("Appearance", ["Daylight", "Midnight"],
                             key="appearance", selection_mode="single", width="stretch",
                             on_change=_keep_appearance_selected)

    views = [
        "Overview",
        "Discover",
        "Decision lab",
        "Log purchase",
        "Wishlist",
        "Cart & checkout",
        "My orders",
        "Impact analytics",
        "Swap studio",
        "Eco rewards",
        "Help & returns",
        "Profile",
    ]
    view_labels = {
        "Overview": "Overview",
        "Discover": "Discover products",
        "Decision lab": "Decision lab",
        "Log purchase": "Log a purchase",
        "Wishlist": f"Mindful wishlist · {len(st.session_state.wishlist)}",
        "Cart & checkout": f"Cart & checkout · {sum(st.session_state.cart.values())}",
        "My orders": f"Orders & tracking · {len(st.session_state.orders)}",
        "Impact analytics": "Impact analytics",
        "Swap studio": "Swap studio",
        "Eco rewards": "Eco rewards",
        "Help & returns": "Help & returns",
        "Profile": "My profile",
    }
    pending_view = st.session_state.pop("pending_view", None)
    if pending_view in views:
        st.session_state.view = pending_view
    if st.session_state.get("view") not in views:
        st.session_state.view = "Overview"

    with st.sidebar:
        st.html('<div class="si-logo"><span class="si-logo-mark">✳</span>ShopImpact<span style="color:var(--si-accent)">.</span></div><div class="si-wordmark">Live a little lighter</div>')
        st.markdown("**Your pages**")
        st.radio(
            "Navigate ShopImpact",
            views,
            key="view",
            format_func=lambda value: view_labels[value],
            label_visibility="collapsed",
        )
        st.markdown("---")
        with st.expander("Display & accessibility", icon=":material/tune:"):
            st.toggle("High contrast", key="high_contrast", help="Strengthens text and border contrast.")
            st.toggle("Reduce motion", key="reduce_motion", help="Pause decorative animations and transitions. Your operating-system preference is also respected.")
        st.markdown("**Your monthly goals**")
        monthly_budget = st.number_input("Shopping budget ($)", min_value=25.0, max_value=100000.0, step=25.0, key="monthly_budget")
        monthly_target = st.number_input("CO2e goal (kg)", min_value=1.0, max_value=1000.0, step=1.0, key="monthly_target")
        st.markdown("**Demo controls**")
        if st.button("Load demo data", icon=":material/auto_awesome:", width="stretch", key="load_demo"):
            _load_demo_data()
            st.toast("Demo purchases loaded. Explore your shopping studio.", icon=":material/check_circle:")
        if st.button("Clear my ledger", icon=":material/delete_outline:", width="stretch", key="clear_ledger"):
            st.session_state.purchases = []
            st.session_state.last_added_id = None
            st.toast("Your session ledger is clear.", icon=":material/delete_outline:")
        with st.expander("Data backup", icon=":material/backup:"):
            st.caption("Download a portable copy of your ledger and wishlist, including their recorded footprint estimates.")
            st.download_button(
                "Download ledger + wishlist",
                data=_make_data_backup(
                    st.session_state.purchases, st.session_state.wishlist
                ),
                file_name="shopimpact-backup.json",
                mime="application/json",
                icon=":material/download:",
                key="download_data_backup",
                on_click="ignore",
            )
            backup_file = st.file_uploader(
                "Restore a ShopImpact backup",
                type=["json"],
                key="restore_backup_upload",
            )
            replace_confirmed = st.checkbox(
                "I understand restore replaces my current ledger and wishlist.",
                key="confirm_backup_restore",
                disabled=backup_file is None,
            )
            if st.button(
                "Validate and restore",
                icon=":material/restore:",
                disabled=backup_file is None or not replace_confirmed,
                key="restore_data_backup",
            ):
                restored, backup_issues = _parse_data_backup(backup_file)
                if backup_issues:
                    st.error("Nothing was restored. " + " ".join(backup_issues[:5]))
                elif restored is not None:
                    st.session_state.purchases = restored["purchases"]
                    st.session_state.wishlist = restored["wishlist"]
                    st.session_state.last_added_id = None
                    st.toast("Ledger and wishlist restored.", icon=":material/check_circle:")
                    st.rerun()
        st.markdown("---")
        st.caption("Estimates are directional. Commerce, payments, tracking, and support are local demo flows.")

    view = st.session_state.view
    render_earth_background(view, st.session_state.reduce_motion, st.session_state.high_contrast)
    purchases = st.session_state.purchases
    transition_key = f"page_transition_{view.replace(' ', '_').replace('&', 'and')}"
    with st.container(key=transition_key):
        if view == "Overview":
            _render_overview(purchases, st.session_state.dark_mode, monthly_budget, monthly_target)
        elif view == "Discover":
            _render_catalog(purchases)
        elif view == "Decision lab":
            from .decisions import render_decision_lab
            render_decision_lab(purchases)
        elif view == "Wishlist":
            _render_wishlist()
        elif view == "Cart & checkout":
            _render_cart()
        elif view == "My orders":
            _render_orders()
        elif view == "Log purchase":
            _render_purchase_view(purchases, st.session_state.dark_mode)
        elif view == "Impact analytics":
            _render_analytics(purchases, st.session_state.dark_mode, monthly_target, monthly_budget)
        elif view == "Swap studio":
            _render_swap_studio()
        elif view == "Eco rewards":
            _render_rewards(purchases, st.session_state.dark_mode, monthly_target)
        elif view == "Help & returns":
            _render_help_and_returns()
        elif view == "Profile":
            _render_profile()
