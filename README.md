# Bitcoin Price Prediction - Flask Web App

Production-ready Flask application for Bitcoin price prediction using KNN model with sentiment analysis.

## Project Structure

```
flask/
├── app.py                    # Flask application
├── requirements.txt          # Python dependencies
├── runtime.txt              # Python version for Render
├── Procfile                 # Render startup command
├── model/
│   ├── knn.py              # KNN prediction logic (no changes)
│   ├── sentiment.py        # Sentiment analysis (no changes)
│   ├── scaler.pkl          # Pre-trained scaler
│   └── train_data.pkl      # Pre-trained model data
├── templates/
│   ├── index.html          # Main prediction form
│   └── error.html          # Error page
└── static/                 # Static files (CSS, JS, images)
```

## Features

- **KNN Model**: Uses pre-trained K-Nearest Neighbors model
- **Live Data**: Fetches real-time Bitcoin OHLCV data from Binance
- **Sentiment Analysis**: Analyzes recent Bitcoin news sentiment
- **Clean UI**: Simple, responsive web interface
- **Error Handling**: Comprehensive error management
- **Production Ready**: Optimized for deployment

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The app will start at `http://localhost:10000`

### 3. Test the Prediction Endpoint

Navigate to `http://localhost:10000` in your browser and click "Get Prediction"

## Deployment on Render

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial Flask ML app"
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 2: Create New Web Service on Render

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: bitcoin-prediction
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click "Create Web Service"

### Step 3: Set Environment Variables (Optional)

In Render dashboard → Environment:

```
NEWS_API_KEY=<your-api-key>  # Optional, for enhanced sentiment analysis
```

### Step 4: Deploy

Push to main branch → Render auto-deploys

```bash
git push origin main
```

## API Endpoints

### GET `/`
Returns the prediction form (HTML)

### POST `/predict`
Executes prediction and returns JSON

**Response:**
```json
{
  "success": true,
  "data": {
    "signal": "BUY",
    "confidence": 65.43,
    "sentiment": "POSITIVE",
    "sent_score": 0.325,
    "final": "STRONG BUY",
    "similar_days": [
      {
        "date": "2024-01-15",
        "candle": 2.34,
        "rsi": 45.2,
        "result": "BUY"
      }
    ],
    "news": [
      {
        "title": "Bitcoin rally continues...",
        "text": "...",
        "url": "..."
      }
    ]
  }
}
```

### GET `/health`
Health check endpoint for monitoring

**Response:**
```json
{
  "status": "ok",
  "model_ready": true
}
```

## Model Files

Required pickle files (already in `model/` folder):
- `scaler.pkl`: StandardScaler used during training
- `train_data.pkl`: Contains training data and labels

These files are NOT retrained. They're loaded as-is for predictions.

## Error Handling

- **Missing Model Files**: Returns 503 Service Unavailable
- **Binance API Unavailable**: Returns meaningful error message
- **Invalid Requests**: Returns 400 Bad Request
- **Server Errors**: Returns 500 with error logging

## Monitoring

Monitor health on Render:
```bash
curl https://<your-app>.onrender.com/health
```

## Performance

- Model loading: ~1-2 seconds (on startup)
- Prediction computation: ~2-3 seconds
- Live data fetch: ~1-2 seconds
- Total response time: ~4-6 seconds

## Troubleshooting

### "Model not loaded" Error
Ensure `scaler.pkl` and `train_data.pkl` are in the `model/` folder

### Slow Predictions
Check Binance API status or network connectivity

### Port Already in Use
Change the default port in app.py or set `PORT` environment variable

## License

MIT

## Author

Bitcoin Price Prediction ML Team
