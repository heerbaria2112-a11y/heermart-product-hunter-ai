# HeerMart Product Hunter AI — Daily Research Edition

A free, open-source, rules-based research assistant for an India-focused Shopify store. It runs daily via GitHub Actions, reads configured public RSS feeds, categorises trend/discussion titles, ranks research leads, and publishes CSV/JSON reports.

## What is automatic
- Scheduled daily run at 07:50 India Standard Time (02:20 UTC).
- Google Trends India public RSS feed (subject to availability/format changes).
- Optional public Reddit search RSS (may be unavailable or rate-limited).
- Categorisation into Home, Fashion, Kitchen, Toys, Fitness, Accessories or General.
- Transparent heuristic research-priority score, evidence URL and run date.
- CSV/JSON report committed to `reports/` and visible in the Streamlit dashboard.
- Manual run via GitHub Actions → Daily product research → Run workflow.

## What is not claimed
- This is **not** a verified best-seller detector. The score is a heuristic for prioritising further research, not actual sales rank or demand forecast.
- Views, likes, search interest, discussion and ad presence do not prove sales or profit.
- The starter does not automatically scrape Facebook/Meta Ad Library, Pinterest, Instagram, TikTok or e-commerce sites. Use official permitted interfaces or manual research; do not bypass logins, paywalls, robots/access controls, or rate limits.
- Supplier prices, product cost, delivery costs, conversion rates, ad cost, COD/RTO loss and net profit must be entered from real evidence. The dashboard never fabricates them.
- Free services can change limits and availability. A GitHub-hosted workflow is not guaranteed to run if GitHub changes its policies or usage limits.

## GitHub setup (no paid API keys)
1. Create a public repository at https://github.com/new named `heermart-product-hunter-ai`.
2. Upload all files and folders from this project, including `.github/workflows/daily-research.yml`.
3. In repository **Settings → Actions → General**, ensure workflow permissions allow read/write access to repository contents. If policy prevents write access, the workflow can still be changed to upload reports as workflow artifacts instead.
4. Open **Actions → Daily product research → Run workflow** to test it immediately.
5. Check `reports/latest_status.json` and `reports/latest_products.csv`. GitHub Actions will also run on its schedule.
6. To run the dashboard locally:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
7. Optional dashboard hosting: deploy `app.py` on Streamlit Community Cloud if its current free tier is available. Connect the GitHub repository and select `app.py`.

## Files
- `research.py`: scheduled public-feed collector, category heuristics, score and CSV/JSON reports.
- `app.py`: Streamlit dashboard and editable per-candidate profit calculator.
- `.github/workflows/daily-research.yml`: scheduled daily automation.
- `reports/`: latest report output.
- `sample_products.csv`: blank/illustrative research worksheet template.

## Score method
`research_score` is a rough 0–100 research-priority heuristic using title keyword signals, source type, and basic title shape. It does not measure product sales, conversion, search volume, or profit. Improve it only with traceable data, timestamped sources, and documented scoring rules.

## Suggested safe workflow before selling
1. Validate a trend using multiple independent sources and compare interest over time.
2. Check competitor prices, reviews, recent ad creatives and repeated complaints using permitted public interfaces.
3. Obtain supplier quotation and shipping/COD/RTO terms.
4. Calculate net profit with actual inputs, including advertising and return losses.
5. Test a small budget or sample order before scaling.
6. Keep the source URL, date, evidence notes and uncertainty for every decision.

## Responsible access
Respect each platform's terms, API requirements, rate limits, robots/access controls and privacy rules. Do not put secrets in code or commit customer data. The starter uses no paid AI model or paid API key.
