# Quick Start Guide

Get your Flask app running in 5 minutes.

## Local Development (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run App
```bash
python app.py
```

### 3. Open Browser
```
http://localhost:10000
```

### 4. Click "Get Prediction"
Done! You should see:
- BUY/SELL signal
- Confidence percentage
- Sentiment analysis
- Similar historical days
- Recent news

---

## Deploy on Render (10 minutes)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Flask ML app"
git remote add origin https://github.com/YOUR-USERNAME/bitcoin-prediction.git
git branch -M main
git push -u origin main
```

### 2. Create on Render
- Go to [render.com](https://render.com)
- Click "New Web Service"
- Connect GitHub repo
- Set **Build Command**: `pip install -r requirements.txt`
- Set **Start Command**: `gunicorn app:app`
- Click "Create"

### 3. Wait for Deployment
- Takes 2-5 minutes
- Watch logs for "Your service is live"
- Copy your live URL

### 4. Test
- Open your Render URL
- Click "Get Prediction"
- Done!

---

## Folder Structure

```
flask/
├── app.py                  ← Main Flask app
├── requirements.txt        ← Dependencies
├── runtime.txt            ← Python version
├── Procfile               ← Render startup
├── model/
│   ├── knn.py            ← Prediction logic (DO NOT MODIFY)
│   ├── sentiment.py      ← Sentiment analysis (DO NOT MODIFY)
│   ├── scaler.pkl        ← Pre-trained scaler
│   └── train_data.pkl    ← Pre-trained data
├── templates/
│   ├── index.html        ← Form UI
│   └── error.html        ← Error page
└── static/               ← CSS/JS/Images
```

---

## API Endpoints

### GET `/`
Returns form

### POST `/predict`
Returns prediction JSON

### GET `/health`
Health check

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Import error | Run `pip install -r requirements.txt` |
| Port in use | Change port in app.py or set PORT env var |
| Model not found | Verify model/*.pkl files exist |
| Deployment fails | Check Render logs for errors |
| Slow predictions | Normal (4-6s for live data fetch) |

---

## File Reference

- **app.py**: Flask app - handles routes & loading models
- **index.html**: Web form - clean responsive UI
- **requirements.txt**: All Python packages needed
- **runtime.txt**: Python 3.11.7 (for Render)
- **Procfile**: Tells Render to use gunicorn

---

## Key Features

✓ Production-ready code  
✓ Error handling  
✓ Live data from Binance  
✓ Sentiment analysis  
✓ KNN model (no retraining)  
✓ Clean responsive UI  
✓ Easy Render deployment  

---

## Next Steps

1. **Test locally**: `python app.py`
2. **Deploy**: Push to GitHub, then render.com
3. **Monitor**: Check `/health` endpoint regularly
4. **Update**: Code changes auto-deploy on push

---

For detailed docs, see:
- `README.md` - Full documentation
- `DEPLOYMENT.md` - Detailed deployment guide
- `app.py` - Code with comments

Happy deploying!
