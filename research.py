"""HeerMart product discovery: public signals + product-keyword filtering.
Does not scrape marketplaces or claim sales/supplier prices are verified.
"""
from __future__ import annotations
import csv, json, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import feedparser
import requests

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
USER_AGENT = "HeerMartProductHunterAI/2.0 (public-feed research; respectful access)"

# Public feeds are discovery signals only. Availability and formats can change.
FEEDS = [
    {"name": "Google Trends India", "url": "https://trends.google.com/trending/rss?geo=IN", "kind": "trend"},
    {"name": "Reddit product discussions", "url": "https://www.reddit.com/search.rss/?q=(best%20gadgets%20OR%20product%20recommendations%20OR%20must%20have%20gadgets)%20India&sort=hot&t=month", "kind": "discussion"},
    {"name": "Bing News product discovery", "url": "https://www.bing.com/news/search?q=" + quote('(product OR gadget OR kitchen tool OR home organizer) India price review') + "&format=rss", "kind": "news"},
    {"name": "Bing News viral shopping products", "url": "https://www.bing.com/news/search?q=" + quote('trending products India shopping gadget 2026') + "&format=rss", "kind": "news"},
]

CATEGORIES = {
    "Home": ["organizer", "organiser", "storage", "cleaning brush", "mop", "lamp", "decor", "led light", "vacuum", "bathroom", "garden", "cleaning cloth", "shoe rack", "shelf", "dustbin", "mosquito net"],
    "Fashion": ["dress", "shirt", "saree", "kurti", "handbag", "jewellery", "jewelry", "necklace", "bracelet", "watch", "shoes", "sneaker", "sunglasses", "wallet", "sling bag"],
    "Kitchen": ["blender", "juicer", "cutter", "chopper", "lunch box", "bottle", "cookware", "air fryer", "mixer", "water bottle", "oil dispenser", "spice rack", "peeler", "kitchen tool", "food storage"],
    "Toys": ["toy", "toys", "puzzle", "educational toy", "doll", "building blocks", "craft kit", "remote control car", "kids activity"],
    "Fitness": ["fitness", "gym", "workout", "yoga mat", "posture corrector", "resistance band", "dumbbell", "massage gun", "exercise band", "jump rope", "foam roller"],
    "Accessories": ["mobile stand", "phone holder", "charger", "earbuds", "cable", "travel adapter", "portable juicer", "mini blender", "power bank", "gadget", "tripod", "led selfie", "car accessory"],
}
PRODUCT_TERMS = sorted({kw for kws in CATEGORIES.values() for kw in kws}, key=len, reverse=True)
SHOPPING_TERMS = ["buy", "price", "review", "best", "product", "gadget", "shopping", "deal", "portable", "mini", "organizer", "blender", "cutter", "holder", "cleaner", "toy", "bag", "lamp", "bottle", "charger", "kit", "tool", "accessory"]
JUNK_TERMS = ["cricket", "match result", "election", "stock market", "weather", "earthquake", "celebrity", "movie review", "box office", "politics", "war update", "scorecard", "exam result", "lottery", "horoscope"]

FIELDS = ["rank", "date_utc", "product_name_or_signal", "category", "research_priority_score", "source", "source_url", "published", "signal_type", "is_product_listing_verified", "supplier_price_inr", "marketplace_price_inr", "estimated_sales_volume", "evidence_notes", "next_validation_step"]

def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()

def category_for(text: str) -> str:
    low = text.lower()
    scores = {cat: sum(1 for kw in kws if kw in low) for cat, kws in CATEGORIES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "Needs manual category review"

def product_relevance(title: str, summary: str) -> tuple[bool, str]:
    text = (title + " " + summary).lower()
    if any(term in text for term in JUNK_TERMS):
        return False, "Excluded: unrelated trend/news topic"
    hits = [kw for kw in PRODUCT_TERMS if kw in text]
    shopping = any(term in text for term in SHOPPING_TERMS)
    # Only keep signals that mention a recognizable product type or have clear shopping intent.
    if not hits and not (shopping and any(w in text for w in ["kitchen", "home", "fashion", "fitness", "gadgets", "gift"])):
        return False, "Excluded: insufficient product-specific signal"
    return True, ", ".join(hits[:5]) if hits else "Shopping-intent phrase; manual review required"

def priority_score(title: str, summary: str, source: str) -> int:
    text = (title + " " + summary).lower()
    product_hits = sum(1 for kw in PRODUCT_TERMS if kw in text)
    shopping_hits = sum(1 for kw in SHOPPING_TERMS if kw in text)
    source_points = {"Google Trends India": 20, "Reddit product discussions": 18, "Bing News product discovery": 12, "Bing News viral shopping products": 12}.get(source, 8)
    return max(0, min(100, 25 + min(product_hits * 9, 36) + min(shopping_hits * 4, 20) + source_points - (15 if len(title.split()) > 14 else 0)))

def fetch_feed(feed: dict) -> tuple[list[dict], dict]:
    status = {"source": feed["name"], "feed_url": feed["url"], "status": "unavailable", "items_seen": 0, "product_signals_kept": 0, "error": ""}
    try:
        response = requests.get(feed["url"], timeout=25, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if parsed.bozo and not parsed.entries:
            raise RuntimeError(f"RSS parse error: {parsed.bozo_exception}")
        status["status"] = "ok"
        rows = []
        for entry in parsed.entries[:100]:
            title = clean(entry.get("title"))
            if not title:
                continue
            summary = clean(entry.get("summary", entry.get("description", "")))[:700]
            status["items_seen"] += 1
            ok, match_reason = product_relevance(title, summary)
            if not ok:
                continue
            published = clean(entry.get("published", entry.get("updated", "Not provided")))
            url = entry.get("link", feed["url"])
            rows.append({
                "date_utc": TODAY,
                "product_name_or_signal": title,
                "category": category_for(title + " " + summary),
                "research_priority_score": priority_score(title, summary, feed["name"]),
                "source": feed["name"], "source_url": url, "published": published,
                "signal_type": "Trend/discussion/news signal — not proof of sales",
                "is_product_listing_verified": "No",
                "supplier_price_inr": "Not available from this feed",
                "marketplace_price_inr": "Not verified",
                "estimated_sales_volume": "Not available",
                "evidence_notes": (summary or "No summary supplied")[:700] + f" | Product keyword match: {match_reason}",
                "next_validation_step": "Open evidence link; locate a real listing on supplier/marketplace and record current price, shipping, stock and return terms."
            })
        status["product_signals_kept"] = len(rows)
        return rows, status
    except Exception as exc:
        status["error"] = f"{type(exc).__name__}: {exc}"
        return [], status

def main() -> None:
    rows, statuses = [], []
    for feed in FEEDS:
        items, status = fetch_feed(feed)
        rows.extend(items)
        statuses.append(status)
    dedup = {}
    for row in rows:
        key = hashlib.sha256((row["product_name_or_signal"].lower() + row["source_url"]).encode()).hexdigest()
        dedup[key] = row
    rows = sorted(dedup.values(), key=lambda r: r["research_priority_score"], reverse=True)
    for i, row in enumerate(rows, 1): row["rank"] = i
    for filename in [f"daily_products_{TODAY}.csv", "latest_products.csv"]:
        with (REPORTS / filename).open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    status = {
        "run_date_utc": TODAY, "product_signals_kept": len(rows), "source_status": statuses,
        "important_limitations": [
            "These are product-specific discovery signals, not verified product listings or bestseller rankings.",
            "This free workflow does not log into Dropdash, Meesho, IndiaMART, Amazon, Flipkart, Facebook Ad Library or Pinterest.",
            "Supplier/marketplace prices, stock, sales volumes, shipping charges and return/RTO rates are not invented; add them from real listings or import a supplier CSV in the dashboard.",
            "For actual supplier prices, use official partner/API access where available or manually record publicly visible listing details. Do not share passwords, OTPs or private API keys in reports."
        ]
    }
    (REPORTS / "latest_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))
    if not rows: print("No product-specific signals found in this run. Check source status or import a supplier catalog in the dashboard.")

if __name__ == "__main__": main()
