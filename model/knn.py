"""
knn.py
------
Prediction logic only — no training, no CSV reading at runtime.
All heavy work is done offline by train_model.py.

At runtime this module only:
  1. Loads two small .pkl files (< 5 MB total, instant)
  2. Fetches one live candle from Binance
  3. Runs cosine similarity against the pre-scaled training matrix
"""

import os
import joblib
import pandas as pd
import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(__file__)
K        = 9

FEATURES = [
    'candle_body', 'upper_wick', 'lower_wick', 'hl_range',
    'volume_change',
    'momentum_3', 'momentum_5', 'momentum_10',
    'ma5_dist', 'ma10_dist', 'ma20_dist',
    'rsi', 'macd_pct', 'volatility_pct'
]


# ── Feature engineering (same logic as train_model.py) ────────────────────

def _compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def _engineer_features(df):
    df = df.copy()
    df['candle_body']    = (df['Close'] - df['Open']) / df['Open'] * 100
    df['upper_wick']     = (df['High']  - df['Close']) / df['Open'] * 100
    df['lower_wick']     = (df['Open']  - df['Low'])   / df['Open'] * 100
    df['hl_range']       = (df['High']  - df['Low'])   / df['Open'] * 100
    df['volume_change']  = df['Volume'].pct_change() * 100
    df['momentum_3']     = df['Close'].pct_change(3)  * 100
    df['momentum_5']     = df['Close'].pct_change(5)  * 100
    df['momentum_10']    = df['Close'].pct_change(10) * 100
    df['ma5_dist']       = (df['Close'] - df['Close'].rolling(5).mean())  / df['Close'] * 100
    df['ma10_dist']      = (df['Close'] - df['Close'].rolling(10).mean()) / df['Close'] * 100
    df['ma20_dist']      = (df['Close'] - df['Close'].rolling(20).mean()) / df['Close'] * 100
    df['rsi']            = _compute_rsi(df['Close'])
    ema12                = df['Close'].ewm(span=12).mean()
    ema26                = df['Close'].ewm(span=26).mean()
    df['macd_pct']       = (ema12 - ema26) / df['Close'] * 100
    df['volatility_pct'] = df['Close'].rolling(10).std() / df['Close'] * 100
    return df


# ── Model artifact loader (replaces load_and_train) ───────────────────────

def load_model_artifacts():
    """
    Loads pre-trained artifacts saved by train_model.py.
    Returns (df, y_train, X_train_scaled, scaler).

    Raises FileNotFoundError with a clear message if either .pkl is missing
    so streamlit_app.py can show a helpful error instead of a traceback.
    """
    scaler_path = os.path.join(BASE_DIR, "scaler.pkl")
    data_path   = os.path.join(BASE_DIR, "train_data.pkl")

    for path in (scaler_path, data_path):
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing model file: {os.path.basename(path)}. "
                "Run `python train_model.py` locally and upload the generated "
                ".pkl files to your Hugging Face Space."
            )

    scaler     = joblib.load(scaler_path)
    train_data = joblib.load(data_path)

    return (
        train_data["df"],
        train_data["y_train"],
        train_data["X_train_scaled"],
        scaler,
    )


# ── Live data fetcher ──────────────────────────────────────────────────────

def get_live_btc_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=1"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        last = data[-1]  # [timestamp, open, high, low, close]
        return {
            "Date":   pd.to_datetime(last[0], unit='ms'),
            "Open":   float(last[1]),
            "High":   float(last[2]),
            "Low":    float(last[3]),
            "Close":  float(last[4]),
            "Volume": 0.0,  # CoinGecko OHLC doesn't include volume
        }
    except Exception as exc:
        raise RuntimeError(f"CoinGecko API unavailable: {exc}")


def _prepare_live_features(df, live):
    base    = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()
    df_live = pd.concat([base, pd.DataFrame([live])], ignore_index=True)
    df_live = _engineer_features(df_live)
    df_live = df_live.dropna().reset_index(drop=True)
    return df_live.iloc[-1]


# ── Core prediction (signature unchanged — streamlit_app.py needs no edits) ─

def build_prediction(df, y_train, X_train_scaled, scaler,
                     sent_score, sent_label, pos, neg, news):
    """
    Fetches live BTC candle, computes cosine similarity against pre-scaled
    training data, returns full result dict.
    """
    live      = get_live_btc_data()
    live_feat = _prepare_live_features(df, live)

    live_vec    = pd.DataFrame([live_feat[FEATURES]])
    live_scaled = scaler.transform(live_vec)

    # Single similarity pass — reused for signal AND similar-days
    sims      = cosine_similarity(live_scaled, X_train_scaled)[0]
    top_k_idx = sims.argsort()[-K:][::-1]

    weights = sims[top_k_idx]
    targets = y_train.iloc[top_k_idx].values
    buy_w   = np.sum(weights[targets == 1])
    sell_w  = np.sum(weights[targets == 0])

    confidence = max(buy_w, sell_w) / (buy_w + sell_w)
    signal     = "BUY" if buy_w > sell_w else "SELL"

    if confidence < 0.55:
        final = "HOLD"
    elif confidence >= 0.55 and sent_score > 0.3:
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
            "date":   str(row['Date'].date()),
            "candle": round(row['candle_body'], 2),
            "rsi":    round(row['rsi'], 1),
            "result": "BUY" if row['target'] == 1 else "SELL",
        })

    return {
        "signal":       signal,
        "confidence":   round(confidence * 100, 2),
        "sentiment":    sent_label,
        "sent_score":   round(sent_score, 3),
        "news_count":   pos + neg,
        "final":        final,
        "similar_days": similar_days,
        "news":         news,
    }
