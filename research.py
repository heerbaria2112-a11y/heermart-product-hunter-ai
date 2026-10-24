"""Free daily trend research. Uses public RSS feeds only; no scraping/login/API keys."""
from __future__ import annotations
import csv, json, os, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import feedparser
import requests

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
USER_AGENT = "HeerMartProductHunterAI/1.0 (public RSS trend research; contact: repository owner)"

# Google Trends public RSS endpoint. RSS availability/format can change.
FEEDS = [
    {"name": "Google Trends India", "url": "https://trends.google.com/trending/rss?geo=IN", "kind": "trend"},
    # Public Reddit RSS search feeds are optional and may be rate-limited/unavailable.
    {"name": "Reddit product discovery", "url": "https://www.reddit.com/search.rss/?q=product%20recommendations%20OR%20must%20have%20gadgets&sort=hot&t=week", "kind": "discussion"},
]

CATEGORIES = {
    "Home": ["home", "organizer", "organiser", "storage", "cleaning", "mop", "kitchen rack", "lamp", "decor", "led", "vacuum", "furniture", "bathroom", "garden"],
    "Fashion": ["fashion", "dress", "shirt", "saree", "kurti", "bag", "handbag", "jewellery", "jewelry", "necklace", "bracelet", "watch", "shoes", "sneaker", "sunglasses"],
    "Kitchen": ["kitchen", "blender", "juicer", "cutter", "chopper", "lunch box", "bottle", "cookware", "air fryer", "mixer", "water bottle"],
    "Toys": ["toy", "toys", "kids", "kid", "baby", "puzzle", "educational", "doll", "building blocks", "school", "craft"],
    "Fitness": ["fitness", "gym", "workout", "yoga", "posture", "resistance band", "dumbbell", "sports", "massage", "exercise"],
    "Accessories": ["accessory", "accessories", "mobile", "phone", "charger", "earbuds", "cable", "travel", "portable", "mini", "gadget", "tech"],
}
COMMERCIAL_HINTS = ["buy", "best", "review", "price", "deal", "shop", "product", "amazon", "flipkart", "gift", "viral", "trending", "portable", "mini", "organizer", "organiser", "blender", "bag", "lamp", "cleaner", "toy", "accessory"]

def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(s or ""))).strip()

def category_for(text):
    low = text.lower()
    scores = {cat: sum(1 for kw in kws if kw in low) for cat, kws in CATEGORIES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "General"

def score_item(title, source, published):
    low = title.lower()
    # Heuristic relevance score, not a measured sales/demand score.
    commercial = min(30, sum(5 for hint in COMMERCIAL_HINTS if hint in low))
    length_score = 15 if 2 <= len(title.split()) <= 8 else 8
    source_score = 25 if "Google Trends" in source else 15
    recency_score = 20
    demand_score = min(10, sum(2 for word in ["trending", "viral", "popular", "best", "buy", "review"] if word in low))
    return min(100, commercial + length_score + source_score + recency_score + demand_score)

def fetch_feed(feed):
    try:
        response = requests.get(feed["url"], timeout=20, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if parsed.bozo and not parsed.entries:
            return [], f"Feed parse error: {parsed.bozo_exception}"
        rows = []
        for entry in parsed.entries[:100]:
            title = clean(entry.get("title"))
            link = entry.get("link", "")
            if not title:
                continue
            published = entry.get("published", entry.get("updated", "Not provided"))
            summary = clean(entry.get("summary", ""))[:500]
            rows.append({
                "date_utc": TODAY, "product_or_trend": title, "category": category_for(title + " " + summary),
                "research_score": score_item(title, feed["name"], published), "source": feed["name"],
                "source_url": link or feed["url"], "feed_url": feed["url"], "published": published,
                "evidence_type": "Public trend/discussion signal", "verified_sales": "No",
                "evidence_notes": summary or "No summary provided by feed",
            })
        return rows, None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"

def main():
    rows, statuses = [], []
    for feed in FEEDS:
        items, error = fetch_feed(feed)
        rows.extend(items)
        statuses.append({"source": feed["name"], "feed_url": feed["url"],
                         "status": "ok" if not error else "unavailable",
                         "items_found": len(items), "error": error or ""})
    # De-duplicate by title+source URL; keep strongest score.
    dedup = {}
    for row in rows:
        key = hashlib.sha256((row["product_or_trend"].lower() + row["source_url"]).encode()).hexdigest()
        dedup[key] = row
    rows = sorted(dedup.values(), key=lambda r: r["research_score"], reverse=True)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
        row["selling_price_inr"] = ""
        row["supplier_cost_inr"] = ""
        row["shipping_cost_inr"] = ""
        row["ad_cost_per_order_inr"] = ""
        row["fees_inr"] = ""
        row["expected_return_rto_cost_inr"] = ""
        row["estimated_net_profit_inr"] = ""
        row["profit_status"] = "Not calculated: verified cost inputs required"
    fields = ["rank","date_utc","product_or_trend","category","research_score","source","source_url","feed_url",
              "published","evidence_type","verified_sales","evidence_notes","selling_price_inr","supplier_cost_inr",
              "shipping_cost_inr","ad_cost_per_order_inr","fees_inr","expected_return_rto_cost_inr",
              "estimated_net_profit_inr","profit_status"]
    csv_path = REPORTS / f"daily_products_{TODAY}.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    # Also write a stable latest report path for dashboard and users.
    latest = REPORTS / "latest_products.csv"
    with latest.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary = {"run_date_utc": TODAY, "items_found": len(rows), "source_status": statuses,
               "limitations": [
                   "Rank is a heuristic research-priority score, not a sales rank.",
                   "No sales volumes or profit values are inferred from social signals.",
                   "Public RSS sources can change, be unavailable, or rate-limit requests.",
                   "Meta Ad Library and Pinterest are not automatically scraped; use their permitted official interfaces/manual research."
               ]}
    (REPORTS / "latest_status.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    # A failed feed does not fail the run if at least one source is available.
    if not rows and all(s["status"] != "ok" for s in statuses):
        print("Warning: no feeds available today. Check reports/latest_status.json.")
if __name__ == "__main__":
    main()
