"""ShopImpact ledger."""
from __future__ import annotations

import html
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st
from .ui import render_table
from .catalog import ALTERNATIVE_BRANDS, CATEGORIES, ECO_TIPS, LOW_IMPACT_FACTOR
from .logic import _make_monthly_report, _new_purchase, _purchase_frame, calculate_impact, check_badges, get_alternatives
from .data import _parse_purchase_csv


LEAF_IMAGE = Path(__file__).with_name("assets") / "eco-leaf.svg"


def _render_purchase_view(purchases: list[dict]) -> None:
    st.subheader("Log a purchase", anchor=False)
    st.caption("A quick estimate today makes your next choice easier to compare.")

    with st.expander("Import an existing purchase log", icon=":material/upload_file:"):
        st.caption("CSV columns: product, category, price. Optional columns: date, brand. CO2e is recalculated using ShopImpact category factors.")
        template = pd.DataFrame(columns=["date", "product", "category", "brand", "price"])
        st.download_button("Get CSV template", data=template.to_csv(index=False), file_name="shopimpact-import-template.csv", mime="text/csv", icon=":material/download:", key="download_import_template", on_click="ignore")
        uploaded_file = st.file_uploader("Choose a purchase CSV", type=["csv"], key="purchase_csv_upload")
        if uploaded_file is not None and st.button("Validate and import", icon=":material/fact_check:", key="import_purchases"):
            imported, issues = _parse_purchase_csv(uploaded_file)
            if imported:
                st.session_state.purchases.extend(imported)
                st.toast(f"Imported {len(imported)} purchase(s).", icon=":material/check_circle:")
            if issues:
                st.warning("Some rows were skipped: " + " ".join(issues[:5]))
            if not imported and not issues:
                st.info("This CSV contains no purchase rows to import.")

    templates = [
        ("Organic pantry", "Seasonal produce box", "Groceries / organic food", "Local co-op", 24.0),
        ("Pre-loved find", "Second-hand jacket", "Sustainable apparel / second-hand", "Vinted", 42.0),
        ("Refill care", "Refill hand wash", "Beauty & personal care", "Ethique", 18.0),
    ]
    with st.container(horizontal=True):
        for index, template in enumerate(templates):
            if st.button(template[0], key=f"template_{index}", icon=":material/add_shopping_cart:"):
                st.session_state.log_product = template[1]
                st.session_state.log_category = template[2]
                st.session_state.log_brand = template[3]
                st.session_state.log_price = template[4]

    st.session_state.setdefault("log_product", "")
    st.session_state.setdefault("log_category", "Groceries / organic food")
    st.session_state.setdefault("log_brand", "")
    st.session_state.setdefault("log_price", 25.0)
    st.session_state.setdefault("log_date", date.today())
    st.session_state.setdefault("log_green_choice", False)

    details, preview = st.columns([2, 1], gap="medium")
    # Regular widgets rerun on change, so the estimate updates before a purchase is saved.
    with details, st.container(border=True):
        product = st.text_input("Product", key="log_product", placeholder="e.g. Oat milk or wireless headphones")
        category = st.selectbox("Category", list(CATEGORIES), key="log_category")
        col_brand, col_price, col_date = st.columns([1.2, 0.8, 0.9])
        with col_brand:
            brand = st.text_input("Brand or shop", key="log_brand", placeholder="Optional")
        with col_price:
            price = st.number_input("Price ($)", min_value=0.01, max_value=100000.0, step=1.0, key="log_price")
        with col_date:
            purchased_on = st.date_input("Purchase date", key="log_date", max_value=date.today())
        greener_choice = st.checkbox(
            "I chose a greener alternative",
            key="log_green_choice",
            help="Uses a lower-factor scenario (at most 0.4 kg CO2e per $10). This is an assumed comparison, not a verified product footprint.",
        )

    estimated_co2 = calculate_impact(category, price)
    preview_co2 = round(min(LOW_IMPACT_FACTOR, CATEGORIES[category]["factor"]) * price / 10, 2) if greener_choice else estimated_co2
    with details:
        submitted = st.button("Add to my impact log", type="primary", icon=":material/add_circle:")
    with preview, st.container(border=True):
        label = "Lower-factor scenario" if greener_choice else f'{CATEGORIES[category]["level"]} impact category'
        st.metric("Live footprint estimate", f"{preview_co2:.2f} kg CO₂e")
        st.caption(f"{label}. Category-based estimate.")
        st.markdown("**Options to explore**")
        st.write(", ".join(ALTERNATIVE_BRANDS[category]))

    saved_purchase = None
    if submitted:
        if not product.strip():
            st.error("Add a product name before saving this purchase.")
        elif purchased_on > date.today():
            st.error("Purchase date cannot be in the future.")
        else:
            scenario_co2 = preview_co2 if greener_choice else None
            saved_purchase = _new_purchase(product, category, brand, price, purchased_on, co2_override=scenario_co2)
            st.session_state.purchases.append(saved_purchase)
            st.session_state.last_added_id = saved_purchase["id"]
            st.toast(f"{product.strip()} added to your impact log.", icon=":material/check_circle:")

    # The saved ID keeps the most recent purchase visible across Streamlit reruns.
    last_id = st.session_state.get("last_added_id")
    last_purchase = next((item for item in reversed(purchases) if item.get("id") == last_id), None)
    if last_purchase:
        _render_swap(last_purchase)
    with preview:
        badges = check_badges(purchases, monthly_target=st.session_state.monthly_target)["badges"]
        earned = [badge["name"] for badge in badges if badge["earned"]]
        if earned:
            st.caption("Badges earned: " + ", ".join(earned))

        if saved_purchase:
            st.caption(ECO_TIPS[(len(purchases) - 1) % len(ECO_TIPS)])
            if CATEGORIES[category]["factor"] <= LOW_IMPACT_FACTOR or greener_choice:
                leaf = LEAF_IMAGE.read_text(encoding="utf-8")
                if st.session_state.get("reduce_motion"):
                    leaf = leaf.replace("prefers-reduced-motion: no-preference", "not all")
                # Renew the SVG URL so consecutive lower-impact purchases replay the strokes.
                leaf += f'<!-- {saved_purchase["id"]} -->'
                st.image(leaf, width=160, caption="A Turtle leaf for your lower-impact choice")

    report = _make_monthly_report(purchases, date.today())
    st.markdown("**This month in your impact log**")
    spend_col, co2_col = st.columns(2)
    spend_col.metric("Monthly spend", f'${report["total_spend"]:,.2f}')
    co2_col.metric("Monthly footprint", f'{report["estimated_co2_kg"]:.2f} kg CO₂e')

    st.subheader("Recent purchases", anchor=False)
    frame = _purchase_frame(purchases)
    if frame.empty:
        st.markdown("Your ledger is ready. Add an item above or load demo data from the sidebar.")
        return

    st.markdown("**Purchase history**")
    filter_cols = st.columns([1.2, 1, 0.9])
    with filter_cols[0]:
        search_term = st.text_input("Search purchases", placeholder="Product or brand", key="history_search")
    with filter_cols[1]:
        category_filter = st.selectbox("Category filter", ["All categories", *list(CATEGORIES)], key="history_category")
    with filter_cols[2]:
        sort_order = st.selectbox("Sort by", ["Newest first", "Oldest first", "Highest footprint", "Highest spend"], key="history_sort")

    filtered = frame.copy()
    if search_term.strip():
        match = filtered["product"].str.contains(search_term.strip(), case=False, na=False, regex=False) | filtered["brand"].str.contains(search_term.strip(), case=False, na=False, regex=False)
        filtered = filtered[match]
    if category_filter != "All categories":
        filtered = filtered[filtered["category"] == category_filter]
    sort_config = {
        "Newest first": ("date", False),
        "Oldest first": ("date", True),
        "Highest footprint": ("co2", False),
        "Highest spend": ("price", False),
    }
    sort_column, ascending = sort_config[sort_order]
    filtered = filtered.sort_values(sort_column, ascending=ascending)
    if filtered.empty:
        st.caption("No purchases match those filters.")
        return

    display = filtered.head(20).copy()
    display["date"] = display["date"].dt.strftime("%b %d, %Y")
    display = display.rename(
        columns={"date": "Date", "product": "Product", "category": "Category", "brand": "Brand", "price": "Spend", "co2": "CO2e (kg)", "impact_level": "Impact"}
    )
    render_table(
        display[["Date", "Product", "Category", "Brand", "Spend", "CO2e (kg)", "Impact"]],
        hide_index=True,
        column_config={
            "Spend": st.column_config.NumberColumn("Spend", format="$%.2f"),
            "CO2e (kg)": st.column_config.NumberColumn("CO2e (kg)", format="%.2f kg"),
        },
        alt="Most recent purchases with category, spend, and estimated emissions",
    )
    remove_col, remove_action_col = st.columns([1.5, 1])
    with remove_col:
        remove_id = st.selectbox(
            "Remove a purchase",
            filtered["id"].tolist(),
            format_func=lambda purchase_id: next(
                f"{row.product} · {row.date:%b %d} · ${row.price:.2f}"
                for row in filtered.itertuples()
                if row.id == purchase_id
            ),
            key="remove_purchase_id",
        )
    with remove_action_col:
        st.write("")
        if st.button("Remove selected", icon=":material/delete_outline:", key="remove_purchase"):
            st.session_state.purchases = [item for item in purchases if item.get("id") != remove_id]
            if st.session_state.get("last_added_id") == remove_id:
                st.session_state.last_added_id = None
            st.rerun()
    csv_data = frame.drop(columns=["carbon_saved_kg"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export purchase log",
        data=csv_data,
        file_name="shopimpact-purchases.csv",
        mime="text/csv",
        icon=":material/download:",
        key="download_purchases",
        on_click="ignore",
    )


def _render_swap(purchase: dict) -> None:
    suggestions = get_alternatives(
        str(purchase.get("category", "")),
        float(purchase.get("price", 0)),
        str(purchase.get("brand", "")),
    )
    if not suggestions:
        return
    names = ", ".join(html.escape(option["brand"]) for option in suggestions)
    saved = max(option["estimated_savings"] for option in suggestions)
    st.markdown(
        f"""
        <div class="si-swap">
          <strong>Quick-swap idea for {html.escape(str(purchase.get('product', 'your item')))}</strong><br>
          Next time, explore {names}. A similar-price lower-impact choice could save about
          <strong>{saved:.1f} kg CO2e</strong> by this category estimate.
        </div>
        """,
        unsafe_allow_html=True,
    )
