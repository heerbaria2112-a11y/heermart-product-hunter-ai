# HeerMart Product Hunter AI — multi-source starter

A free starter for India-focused product discovery. It combines public RSS discovery signals with a CSV importer for real supplier/marketplace listings and a profit comparison tool.

## What it uses automatically
- Google Trends India public RSS (if available)
- Public Reddit product-discussion RSS (may be rate-limited)
- Bing News RSS searches for product/shopping signals

Automatic sources can be unavailable or return irrelevant results; product-specific filtering reduces, but cannot eliminate, noise. A research score is a priority heuristic, not sales volume or a bestseller rank.

## What it does NOT automatically access
This project does not log into or scrape Dropdash, Meesho, IndiaMART, Amazon, Flipkart, Meta Ad Library, or Pinterest. Marketplace terms, bot controls, account permissions, and API access vary; do not bypass them. Supplier prices, inventory, order volumes, shipping fees, and RTO rates are not invented. Use the dashboard CSV importer to compare real listing details you verify yourself, or add an authorized API integration if you have one.

## Run research locally
Install Python 3.11+; in this folder run:

```bash
python -m venv .venv
```

Windows:
```bat
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python research.py
.venv\Scripts\python -m streamlit run app.py
```

macOS/Linux:
```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python research.py
.venv/bin/python -m streamlit run app.py
```

## GitHub Actions
Workflow `.github/workflows/daily-research.yml` can be manually run or scheduled. It writes `reports/latest_products.csv` and `reports/latest_status.json`.

## Supplier CSV
Download the template from the dashboard. Required columns:
`product_name, source, product_url, supplier_cost_inr, selling_price_inr, shipping_cost_inr, packaging_fees_inr, ad_cost_per_order_inr, expected_rto_cost_inr`.

Use real current values. The dashboard calculates estimated profit as selling price minus the costs entered. Add taxes, payment/COD fees, discounts, platform overhead, and expected returns if applicable.

## Safety and accuracy
- Never put passwords, OTPs, cookies, or private API keys in CSV files or GitHub commits.
- Check a listing's current price, stock, delivery coverage, return/RTO terms, and supplier reliability before selling.
- Search trends, discussion, news, and reviews are not proof of sales.
