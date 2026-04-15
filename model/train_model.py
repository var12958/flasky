"""
train_model.py
--------------
Run this ONCE locally before deploying:

    python train_model.py

Produces two files in the same directory:
    scaler.pkl      — fitted StandardScaler
    train_data.pkl  — dict with X_train_scaled, y_train, and full df

These are loaded at runtime by knn.py — no training happens in the app.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

BASE_DIR  = os.path.dirname(__file__)
FILE_PATH = os.path.join(BASE_DIR, "bitcoin_dataset.csv")

FEATURES = [
    'candle_body', 'upper_wick', 'lower_wick', 'hl_range',
    'volume_change',
    'momentum_3', 'momentum_5', 'momentum_10',
    'ma5_dist', 'ma10_dist', 'ma20_dist',
    'rsi', 'macd_pct', 'volatility_pct'
]


def compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def engineer_features(df):
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
    df['rsi']            = compute_rsi(df['Close'])
    ema12                = df['Close'].ewm(span=12).mean()
    ema26                = df['Close'].ewm(span=26).mean()
    df['macd_pct']       = (ema12 - ema26) / df['Close'] * 100
    df['volatility_pct'] = df['Close'].rolling(10).std() / df['Close'] * 100
    return df


def train():
    print("[1/4] Loading dataset...")
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError(f"Dataset not found: {FILE_PATH}")

    df = pd.read_csv(FILE_PATH)
    df = df.rename(columns={'Start': 'Date'})
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').drop_duplicates(subset='Date')
    df = df.drop(columns=['End'])
    df = df[df['Volume'] > 0].reset_index(drop=True)

    print("[2/4] Engineering features...")
    df = engineer_features(df)
    df = df.dropna().reset_index(drop=True)

    df['next_close'] = df['Close'].shift(-1)
    df['target']     = (df['next_close'] > df['Close']).astype(int)
    df = df.dropna().reset_index(drop=True)

    split   = int(len(df) * 0.8)
    X_train = df[FEATURES].iloc[:split]
    y_train = df['target'].iloc[:split]

    print("[3/4] Fitting scaler...")
    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # ── Save scaler ────────────────────────────────────────────────────────
    scaler_path = os.path.join(BASE_DIR, "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    print(f"Saved: {scaler_path}")

    # ── Save training data (scaled matrix + labels + full df for lookups) ─
    train_data = {
        "X_train_scaled": X_train_scaled,          # np.ndarray  (n_train, 14)
        "y_train":        y_train.reset_index(drop=True),  # pd.Series
        "df":             df.reset_index(drop=True),       # full df for similar-days
    }
    data_path = os.path.join(BASE_DIR, "train_data.pkl")
    joblib.dump(train_data, data_path)
    print(f"Saved: {data_path}")

    print("\n[4/4] Training complete.")
    print(f"   Rows in dataset : {len(df)}")
    print(f"   Training rows   : {split}")
    print(f"   Features        : {len(FEATURES)}")
    print("\nUpload these two files to Hugging Face along with your app:")
    print(f"   • scaler.pkl")
    print(f"   • train_data.pkl")


if __name__ == "__main__":
    train()
