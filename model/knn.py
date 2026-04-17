import os
import joblib
import pandas as pd
import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(BASE_DIR)

K = 9

FEATURES = [
    'candle_body', 'upper_wick', 'lower_wick', 'hl_range',
    'volume_change',
    'momentum_3', 'momentum_5', 'momentum_10',
    'ma5_dist', 'ma10_dist', 'ma20_dist',
    'rsi', 'macd_pct', 'volatility_pct'
]

# ── Feature engineering ─────────────────────────────────────────────

def _compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _engineer_features(df):
    df = df.copy()
    df['candle_body'] = (df['Close'] - df['Open']) / df['Open'] * 100
    df['upper_wick'] = (df['High'] - df['Close']) / df['Open'] * 100
    df['lower_wick'] = (df['Open'] - df['Low']) / df['Open'] * 100
    df['hl_range'] = (df['High'] - df['Low']) / df['Open'] * 100
    df['volume_change'] = df['Volume'].pct_change() * 100
    df['momentum_3'] = df['Close'].pct_change(3) * 100
    df['momentum_5'] = df['Close'].pct_change(5) * 100
    df['momentum_10'] = df['Close'].pct_change(10) * 100
    df['ma5_dist'] = (df['Close'] - df['Close'].rolling(5).mean()) / df['Close'] * 100
    df['ma10_dist'] = (df['Close'] - df['Close'].rolling(10).mean()) / df['Close'] * 100
    df['ma20_dist'] = (df['Close'] - df['Close'].rolling(20).mean()) / df['Close'] * 100
    df['rsi'] = _compute_rsi(df['Close'])
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['macd_pct'] = (ema12 - ema26) / df['Close'] * 100
    df['volatility_pct'] = df['Close'].rolling(10).std() / df['Close'] * 100
    return df


# ── Model loader ────────────────────────────────────────────────────

def load_model_artifacts():
    scaler_path = os.path.join(BASE_DIR, "scaler.pkl")
    data_path = os.path.join(BASE_DIR, "train_data.pkl")

    for path in (scaler_path, data_path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing file: {os.path.basename(path)}")

    scaler = joblib.load(scaler_path)
    train_data = joblib.load(data_path)

    return (
        train_data["df"],
        train_data["y_train"],
        train_data["X_train_scaled"],
        scaler,
    )


# ── Live + fallback data ────────────────────────────────────────────

def get_live_btc_data():
    try:
        # 🔹 OHLC
        ohlc_url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"
        ohlc_params = {"vs_currency": "usd", "days": 1}

        ohlc_resp = requests.get(ohlc_url, params=ohlc_params, timeout=5)
        ohlc_resp.raise_for_status()
        ohlc_data = ohlc_resp.json()
        d = ohlc_data[-1]

        # 🔹 Volume
        vol_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        vol_params = {"vs_currency": "usd", "days": 1}

        vol_resp = requests.get(vol_url, params=vol_params, timeout=5)
        vol_resp.raise_for_status()
        vol_data = vol_resp.json()

        volume = vol_data["total_volumes"][-1][1]

        return {
            "Date": pd.to_datetime(d[0], unit='ms'),
            "Open": float(d[1]),
            "High": float(d[2]),
            "Low": float(d[3]),
            "Close": float(d[4]),
            "Volume": float(volume)
        }

    except Exception:
        print("⚠️ API failed — using CSV fallback")

        csv_path = os.path.join(ROOT_DIR, "btc_sample_30days.csv")
        df = pd.read_csv(csv_path)
        df["Date"] = pd.to_datetime(df["Date"])

        last = df.iloc[-1]

        return {
            "Date": pd.to_datetime("2026-04-24"),
            "Open": float(last["Open"]),
            "High": float(last["High"]),
            "Low": float(last["Low"]),
            "Close": float(last["Close"]),
            "Volume": float(last["Volume"])
        }


# ── Feature prep ────────────────────────────────────────────────────

def _prepare_live_features(df, live):
    base = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()
    df_live = pd.concat([base, pd.DataFrame([live])], ignore_index=True)
    df_live = _engineer_features(df_live)
    df_live = df_live.dropna().reset_index(drop=True)
    return df_live.iloc[-1]


# ── Prediction ──────────────────────────────────────────────────────

def build_prediction(df, y_train, X_train_scaled, scaler,
                     sent_score, sent_label, pos, neg, news):

    live = get_live_btc_data()
    live_feat = _prepare_live_features(df, live)

    live_vec = pd.DataFrame([live_feat[FEATURES]])
    live_scaled = scaler.transform(live_vec)

    sims = cosine_similarity(live_scaled, X_train_scaled)[0]
    top_k_idx = sims.argsort()[-K:][::-1]

    weights = sims[top_k_idx]
    targets = y_train.iloc[top_k_idx].values

    buy_w = np.sum(weights[targets == 1])
    sell_w = np.sum(weights[targets == 0])

    confidence = max(buy_w, sell_w) / (buy_w + sell_w)
    signal = "BUY" if buy_w > sell_w else "SELL"

    # 🔥 FIXED LOGIC
    if confidence < 0.55:
        final = "HOLD"

    elif signal == "BUY" and sent_score > 0.3:
        final = "BUY (SENTIMENT BOOST)"

    elif signal == "BUY" and sent_score > 0:
        final = "STRONG BUY"

    elif signal == "SELL" and sent_score < 0:
        final = "STRONG SELL"

    else:
        final = "WEAK SIGNAL"

    similar_days = []
    for idx in top_k_idx[:5]:
        row = df.iloc[idx]
        similar_days.append({
            "date": str(row['Date'].date()),
            "candle": round(row['candle_body'], 2),
            "rsi": round(row['rsi'], 1),
            "result": "BUY" if row['target'] == 1 else "SELL",
        })

    return {
        "signal": signal,
        "confidence": round(confidence * 100, 2),
        "sentiment": sent_label,
        "sent_score": round(sent_score, 3),
        "news_count": pos + neg,
        "final": final,
        "similar_days": similar_days,
        "news": news,
    }
