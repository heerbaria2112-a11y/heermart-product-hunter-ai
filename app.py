from pathlib import Path
import json
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)
st.set_page_config(page_title="HeerMart Product Hunter AI", page_icon="🛍️", layout="wide")
st.title("🛍️ HeerMart Product Hunter AI")
st.caption("India-focused product discovery • public signals + real listing validation • free starter")
st.warning("Important: a trend signal is not a real product listing, confirmed demand, or a verified bestseller. Prices and sales volumes are never fabricated. Validate a supplier and listing before spending on ads.")

status_path = REPORTS / "latest_status.json"
latest_path = REPORTS / "latest_products.csv"

with st.expander("What this tool can and cannot access", expanded=False):
    st.markdown("""
- **Automatic public signals:** Google Trends India RSS when available, public Reddit discussion RSS, and Bing News RSS product searches.
- **Supplier/marketplace validation:** import a CSV you prepare from listings you can actually access on Dropdash, Meesho, IndiaMART, Amazon, Flipkart, or other sources.
- **Not automatic:** this starter does not sign into private accounts or scrape restricted marketplaces, Meta Ad Library, or Pinterest. Some providers require partner/API credentials.
- **Never assume:** supplier price, stock, sales volume, shipping, COD/RTO rates, or profit unless you have evidence.
""")

if status_path.exists():
    try: status = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception: status = {}
    c1, c2 = st.columns(2)
    c1.metric("Latest research date (UTC)", status.get("run_date_utc", "Unknown"))
    c2.metric("Product-specific signals", status.get("product_signals_kept", 0))
    with st.expander("Automatic source status", expanded=True):
        for src in status.get("source_status", []):
            st.write(f"**{src.get('source','Source')}** — {src.get('status','unknown')} — kept {src.get('product_signals_kept',0)} / seen {src.get('items_seen',0)}")
            if src.get("error"): st.caption(src["error"])
        for note in status.get("important_limitations", []): st.caption("• " + note)

st.header("1. Public product-discovery signals")
if latest_path.exists():
    try: signals = pd.read_csv(latest_path).fillna("")
    except Exception: signals = pd.DataFrame()
else: signals = pd.DataFrame()
if not signals.empty:
    cats = ["All"] + sorted(signals["category"].astype(str).unique().tolist())
    cat = st.selectbox("Category", cats)
    query = st.text_input("Search signals", placeholder="e.g. portable juicer, kitchen cutter")
    view = signals.copy()
    if cat != "All": view = view[view["category"] == cat]
    if query: view = view[view["product_name_or_signal"].astype(str).str.contains(query, case=False, na=False)]
    shown = [c for c in ["rank", "product_name_or_signal", "category", "research_priority_score", "source", "published", "source_url", "is_product_listing_verified", "supplier_price_inr", "marketplace_price_inr", "next_validation_step"] if c in view.columns]
    st.dataframe(view[shown], use_container_width=True, hide_index=True, column_config={"source_url": st.column_config.LinkColumn("Evidence link")})
    st.download_button("Download discovery signals CSV", view.to_csv(index=False).encode("utf-8-sig"), "heermart_discovery_signals.csv", "text/csv")
else:
    st.info("No qualifying signals are available yet. The RSS feeds may be temporarily unavailable. You can still use the supplier catalog importer below.")

st.header("2. Import real product listings from any source")
st.write("Prepare a CSV from listings you can verify on Dropdash, Meesho, IndiaMART, Amazon, Flipkart, or another source. Use the template below so the dashboard can compare costs and estimate profit.")
template = pd.DataFrame([{
    "product_name": "Portable mini juicer blender", "source": "Dropdash", "product_url": "https://example.com/replace-with-real-listing",
    "supplier_cost_inr": 250, "selling_price_inr": 499, "shipping_cost_inr": 60,
    "packaging_fees_inr": 20, "ad_cost_per_order_inr": 80, "expected_rto_cost_inr": 25,
    "stock_checked": "No - check supplier", "price_checked_date": "YYYY-MM-DD", "evidence_notes": "Replace sample values with real checked values"
}])
st.download_button("Download supplier CSV template", template.to_csv(index=False).encode("utf-8-sig"), "heermart_supplier_catalog_template.csv", "text/csv")
upload = st.file_uploader("Upload your verified supplier/listing CSV", type=["csv"])
if upload is not None:
    try:
        catalog = pd.read_csv(upload).fillna("")
        required = ["product_name", "source", "product_url", "supplier_cost_inr", "selling_price_inr", "shipping_cost_inr", "packaging_fees_inr", "ad_cost_per_order_inr", "expected_rto_cost_inr"]
        missing = [x for x in required if x not in catalog.columns]
        if missing:
            st.error("Missing columns: " + ", ".join(missing) + ". Download the template above and use its column names.")
        else:
            numeric = ["supplier_cost_inr", "selling_price_inr", "shipping_cost_inr", "packaging_fees_inr", "ad_cost_per_order_inr", "expected_rto_cost_inr"]
            for col in numeric: catalog[col] = pd.to_numeric(catalog[col], errors="coerce").fillna(0)
            catalog["estimated_profit_inr"] = catalog["selling_price_inr"] - catalog["supplier_cost_inr"] - catalog["shipping_cost_inr"] - catalog["packaging_fees_inr"] - catalog["ad_cost_per_order_inr"] - catalog["expected_rto_cost_inr"]
            catalog["estimated_margin_percent"] = catalog.apply(lambda r: round((r["estimated_profit_inr"] / r["selling_price_inr"] * 100), 1) if r["selling_price_inr"] else 0, axis=1)
            catalog["validation_status"] = catalog.apply(lambda r: "Check supplier listing/price/stock" if "stock_checked" not in catalog.columns or str(r.get("stock_checked", "No")).lower() not in ["yes", "true", "checked"] else "Supplier marked checked by user", axis=1)
            st.success(f"Loaded {len(catalog)} listing(s). Profit is calculated only from the values you supplied.")
            st.dataframe(catalog, use_container_width=True, hide_index=True, column_config={"product_url": st.column_config.LinkColumn("Product listing")})
            st.download_button("Download comparison with profit estimates", catalog.to_csv(index=False).encode("utf-8-sig"), "heermart_product_profit_comparison.csv", "text/csv")
            st.caption("Estimates exclude any costs you did not enter, such as taxes, payment/COD fees, subscription overhead, discounts, or unexpected returns. Confirm supplier prices and stock before publishing.")
    except Exception as e: st.error(f"Could not read the CSV: {e}")

st.header("3. Validate before choosing a product")
st.markdown("""
1. Open the real supplier or marketplace listing and confirm it is purchasable in India.
2. Record the current product cost, shipping/fulfilment charge, stock, delivery estimates, and return/RTO terms.
3. Check comparable retail prices and product reviews; distinguish review counts from sales.
4. Estimate advertising cost and all fees before calculating net profit.
5. Order a sample where practical. Do not run ads based only on a trend score.
""")
