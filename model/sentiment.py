import os
import requests
from datetime import datetime, timedelta, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
analyzer     = SentimentIntensityAnalyzer()


def get_recent_btc_news():
    """
    Fetches BTC-related news from Mediastack (last 12 h).
    Returns a list of dicts: {text, title, url}.
    Never raises — returns [] on any failure.
    Cached with TTL by @st.cache_data in streamlit_app.py.
    """
    url     = "https://api.mediastack.com/v1/news"
    queries = ["Bitcoin", "BTC", "crypto", "cryptocurrency", "blockchain"]
    all_news = []
    now      = datetime.now(timezone.utc)
    past_12h = now - timedelta(hours=12)

    for q in queries:
        params = {
            "access_key": NEWS_API_KEY,
            "keywords":   q,
            "languages":  "en",
            "limit":      25,
        }
        try:
            resp = requests.get(url, params=params, timeout=5)
        except Exception:
            continue

        if resp.status_code != 200:
            continue

        try:
            data = resp.json()
        except Exception:
            continue

        for article in data.get("data", []):
            published = article.get("published_at")
            if not published:
                continue
            try:
                article_time = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except Exception:
                continue
            if article_time < past_12h:
                continue

            title = article.get("title") or ""
            desc  = article.get("description") or ""
            text  = (title + " " + desc).strip()

            if len(text) > 20:
                all_news.append({
                    "text":  text,
                    "title": title,
                    "url":   article.get("url") or "",
                })

    # Deduplicate by first 100 chars
    unique_news, seen = [], set()
    for item in all_news:
        key = item["text"][:100]
        if key not in seen:
            unique_news.append(item)
            seen.add(key)

    # Relax 12 h filter if too few results
    if len(unique_news) < 5:
        unique_news = all_news[:20]

    return unique_news  # [] when everything fails — handled upstream


def analyze_sentiment(news_list):
    """Returns (avg_score, label, pos_count, neg_count, neu_count)."""
    if not news_list:
        return 0.0, "NEUTRAL", 0, 0, 0

    scores = []
    pos = neg = neu = 0

    for item in news_list:
        text  = item["text"] if isinstance(item, dict) else str(item)
        score = analyzer.polarity_scores(text)["compound"]
        scores.append(score)
        if score > 0.05:
            pos += 1
        elif score < -0.05:
            neg += 1
        else:
            neu += 1

    avg = sum(scores) / len(scores)
    label = "POSITIVE" if avg > 0.05 else ("NEGATIVE" if avg < -0.05 else "NEUTRAL")
    return avg, label, pos, neg, neu


def get_sentiment_signal():
    """Convenience wrapper. Cached by @st.cache_data in streamlit_app.py."""
    news                        = get_recent_btc_news()
    score, label, pos, neg, neu = analyze_sentiment(news)
    return score, label, pos, neg, news


if __name__ == "__main__":
    get_sentiment_signal()
