from pathlib import Path
import json
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
st.set_page_config(page_title="HeerMart Product Hunter AI", page_icon="🛍️", layout="wide")
st.title("🛍️ HeerMart Product Hunter AI")
st.caption("Free daily product-trend discovery for India • Public RSS signals • No paid AI/API keys")
st.warning("Ranks are heuristic research-priority scores, not verified bestseller rankings. Trend signals do not prove sales or profitability.")

status_path = REPORTS / "latest_status.json"
csv_path = REPORTS / "latest_products.csv"
if status_path.exists():
    status = json.loads(status_path.read_text(encoding="utf-8"))
    a,b = st.columns(2)
    a.metric("Last scheduled research run (UTC)", status.get("run_date_utc","Unknown"))
    b.metric("Trend/discussion records", status.get("items_found",0))
    with st.expander("Source status and limitations", expanded=True):
        for src in status.get("source_status", []):
            st.write(f"**{src['source']}** — {src['status']} — {src['items_found']} records")
            if src.get("error"):
                st.caption(src["error"])
        for note in status.get("limitations", []):
            st.caption("• " + note)
else:
    st.info("No report exists yet. Run `python research.py` locally or use GitHub Actions → Run workflow.")

if csv_path.exists():
    df = pd.read_csv(csv_path).fillna("")
    if not df.empty:
        categories = ["All"] + sorted([x for x in df["category"].unique().tolist() if x])
        selected_category = st.selectbox("Filter by category", categories)
        search = st.text_input("Search products or keywords")
        view = df.copy()
        if selected_category != "All":
            view = view[view["category"] == selected_category]
        if search:
            view = view[view["product_or_trend"].astype(str).str.contains(search, case=False, na=False)]
        cols = ["rank","product_or_trend","category","research_score","source","published","verified_sales","source_url","evidence_notes"]
        st.dataframe(view[[c for c in cols if c in view.columns]], use_container_width=True, hide_index=True,
                     column_config={"source_url": st.column_config.LinkColumn("Evidence link")})
        st.download_button("Download current report CSV", view.to_csv(index=False).encode("utf-8-sig"),
                           "heermart_product_research.csv", "text/csv")
        st.subheader("Product validation & profit")
        st.write("Select a candidate and enter real supplier and operating costs. These values are not auto-filled from social signals.")
        if len(view):
            chosen = st.selectbox("Candidate", view["product_or_trend"].astype(str).tolist())
            r = view[view["product_or_trend"].astype(str) == chosen].iloc[0]
            st.write(f"**Category:** {r.get('category','Unknown')}  |  **Source:** {r.get('source','Unknown')}  |  **Evidence:** {r.get('source_url','')}")
            c1,c2,c3 = st.columns(3)
            price = c1.number_input("Planned selling price (₹)", min_value=0.0, value=499.0, step=10.0)
            cost = c2.number_input("Supplier cost (₹)", min_value=0.0, value=150.0, step=10.0)
            shipping = c3.number_input("Shipping/fulfilment (₹)", min_value=0.0, value=60.0, step=5.0)
            c4,c5,c6 = st.columns(3)
            ads = c4.number_input("Ad cost per order (₹)", min_value=0.0, value=80.0, step=10.0)
            fees = c5.number_input("Fees/packaging (₹)", min_value=0.0, value=30.0, step=5.0)
            rto = c6.number_input("Expected return/RTO cost (₹)", min_value=0.0, value=25.0, step=5.0)
            profit = price - cost - shipping - ads - fees - rto
            margin = (profit / price * 100) if price else 0
            x,y,z = st.columns(3)
            x.metric("Estimated net profit/order", f"₹{profit:,.0f}")
            y.metric("Estimated margin", f"{margin:.1f}%")
            z.metric("Trend research score", f"{r.get('research_score',0)}/100")
            st.caption("Profit is a user-input estimate, not verified earnings. Include taxes and other costs if applicable.")
    else:
        st.info("The latest feed run returned no records. Check source status above and try again later.")
else:
    st.markdown("### What it researches")
    st.markdown("- Google Trends public RSS for India (when available)\n- Optional public Reddit search RSS (may be rate-limited)\n- Keyword-based categories: home, fashion, kitchen, toys, fitness, accessories and general")
    st.markdown("### What it does not do")
    st.markdown("- Does not scrape Facebook/Pinterest pages or bypass access controls\n- Does not claim to know actual sales from views, likes or search interest\n- Does not generate supplier prices or guaranteed profit")
