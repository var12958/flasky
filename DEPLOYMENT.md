# Deployment Guide: Flask Bitcoin Prediction on Render

Complete step-by-step guide to deploy your Flask ML app on Render.

## Prerequisites

- GitHub account
- Render account (free tier available at [render.com](https://render.com))
- Your Flask project pushed to GitHub

## Step 1: Prepare Your Repository

### 1.1 Initialize Git (if not already done)

```bash
cd flask
git init
git config user.email "you@example.com"
git config user.name "Your Name"
```

### 1.2 Add All Files

```bash
git add .
git commit -m "Initial Flask ML app - production ready"
```

### 1.3 Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Create a new repository (e.g., `bitcoin-prediction`)
3. Do NOT initialize with README (you already have files)
4. Click "Create repository"

### 1.4 Push to GitHub

```bash
git remote add origin https://github.com/YOUR-USERNAME/bitcoin-prediction.git
git branch -M main
git push -u origin main
```

## Step 2: Connect Render Account

1. Go to [render.com](https://render.com)
2. Click "Sign up" or "Sign in"
3. Click "Connect GitHub"
4. Authorize Render to access your GitHub

## Step 3: Create Web Service on Render

### 3.1 Create New Service

1. Dashboard → Click "New +" → Select "Web Service"
2. Connect your GitHub repository

### 3.2 Configure Service

Fill in the form:

| Field | Value |
|-------|-------|
| **Name** | bitcoin-prediction |
| **Environment** | Python 3 |
| **Region** | Choose closest to your users |
| **Branch** | main |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

### 3.3 Instance Settings

- **Plan**: Free (Starter)
- Leave other settings as default

### 3.4 Create Service

Click "Create Web Service" → Wait for deployment (2-5 minutes)

## Step 4: Monitor Deployment

### 4.1 Watch Logs

Dashboard shows real-time build logs:
- "Running build steps..."
- "Building py-3.11.7-1"
- "Installing pip packages..."
- "Build successful"

### 4.2 Check Deployment Status

When you see "Your service is live!", copy your URL:
```
https://bitcoin-prediction.onrender.com
```

## Step 5: Test Your App

### 5.1 Test Website

Open: `https://bitcoin-prediction.onrender.com`

You should see the prediction form.

### 5.2 Test Health Endpoint

```bash
curl https://bitcoin-prediction.onrender.com/health
```

Expected response:
```json
{
  "status": "ok",
  "model_ready": true
}
```

### 5.3 Test Prediction

Click "Get Prediction" on the website or:

```bash
curl -X POST https://bitcoin-prediction.onrender.com/predict
```

## Step 6: Auto-Deploy on Updates

Every push to main branch automatically redeploys:

```bash
git add .
git commit -m "Update prediction logic"
git push origin main
```

Render will automatically rebuild and deploy.

## Troubleshooting

### Issue: "Build failed"

**Check logs** for:
- Missing dependencies in requirements.txt
- Syntax errors in Python files
- File path issues

**Solution**: Fix the issue locally, test with `python app.py`, then push:
```bash
git add .
git commit -m "Fix build issue"
git push origin main
```

### Issue: "Model not loaded" Error

**Check**:
1. `scaler.pkl` exists in `model/` folder
2. `train_data.pkl` exists in `model/` folder
3. Files are not in `.gitignore`

**Solution**: Push the files to GitHub:
```bash
git add model/scaler.pkl model/train_data.pkl
git commit -m "Add model files"
git push origin main
```

### Issue: Slow First Request

**Normal behavior**: First request is slow because:
- Render starts the container
- Python loads model artifacts
- Fetches live Binance data

Subsequent requests are faster.

### Issue: "Service Unavailable" Error

**Possible causes**:
1. Binance API unreachable - try again later
2. Model files missing - check Step 6
3. Container restarting - check logs

**Solution**: 
- Refresh the page
- Check `/health` endpoint
- Review Recent & Build logs

## Environment Variables (Optional)

### Add to Render Dashboard

1. Settings tab → "Environment"
2. Add variables:

```
NEWS_API_KEY=your_api_key_here
FLASK_ENV=production
```

3. Click "Save"
4. Service auto-redeploys

## Performance Optimization

### First Request Optimization

Edit `app.py` and add preloading:

```python
# After MODEL_READY = True
if MODEL_READY:
    # Warm up with dummy prediction
    try:
        _ = get_live_btc_data()  # Cache Binance connection
    except:
        pass
```

### Memory Optimization

Current setup uses ~300-400MB (Free tier allows up to 512MB)

For larger models:
- Upgrade to Paid plan ($7/month)
- Or optimize model size

### Response Caching

Consider adding Redis for sentiment cache:
- Reduces API calls to News providers
- Faster predictions

## Monitoring & Maintenance

### Monitor Uptime

1. Render Dashboard → "Logs"
2. Recent Logs tab for real-time events
3. Metrics tab for resource usage

### Error Notification

Set up GitHub Actions to notify on deployment failure:
1. Create `.github/workflows/deploy-alert.yml`
2. Configure notifications

### Scheduled Restarts

Render automatically restarts idle services (Starter plan):
- First restart after 15 minutes inactivity
- Subsequent restarts every 1 hour

This is fine for our use case.

## Updating Your App

### Code Changes

```bash
# Make changes locally
nano app.py  # or your IDE

# Test locally
python app.py

# Deploy
git add .
git commit -m "Description of changes"
git push origin main
```

### Model File Updates

```bash
git add model/scaler.pkl model/train_data.pkl
git commit -m "Update trained model"
git push origin main
```

## Free Plan Limits

- **Compute**: 750 hours/month (always-on)
- **Memory**: 512 MB per service
- **Storage**: Ephemeral (resets on redeploy)
- **Bandwidth**: Unlimited
- **Services**: Unlimited

**Note**: For persistent storage (database), upgrade to Paid.

## Support & Resources

- Render Docs: https://render.com/docs
- Flask Docs: https://flask.palletsprojects.com
- Deployment Issues: Check Render's Recent Logs tab
- Community: Render Discord or GitHub Issues

## Next Steps

After successful deployment:

1. **Custom Domain**: Add your own domain in Settings
2. **SSL Certificate**: Automatically managed by Render
3. **Analytics**: Monitor prediction requests
4. **Scaling**: Move to paid plan if needed

---

**Deployment Complete!** Your Flask ML app is now live and automatically deploys on every push to main.
