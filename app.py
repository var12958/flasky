"""
Flask web application for Bitcoin price prediction using KNN model.
Production-ready for deployment on Render.
"""

import os
import traceback
from flask import Flask, render_template, request, jsonify
from model.knn import load_model_artifacts, build_prediction
from model.sentiment import get_recent_btc_news, analyze_sentiment


# ─── Application Setup ────────────────────────────────────────────────────

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Model artifacts loaded at startup
try:
    df, y_train, X_train_scaled, scaler = load_model_artifacts()
    MODEL_READY = True
except FileNotFoundError as e:
    MODEL_READY = False
    MODEL_ERROR = str(e)


# ─── Error Handlers ───────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Page not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ─── Routes ───────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    """Render the main prediction form."""
    if not MODEL_READY:
        return render_template("error.html", error=MODEL_ERROR), 503
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    """
    Handle prediction request.
    Returns JSON with prediction result or error.
    """
    if not MODEL_READY:
        return jsonify({
            "success": False,
            "error": "Model not loaded. Please upload model files."
        }), 503

    try:
        # Fetch news and analyze sentiment
        news_list = get_recent_btc_news()
        sent_score, sent_label, pos, neg, _ = analyze_sentiment(news_list)

        # Build prediction
        result = build_prediction(
            df, y_train, X_train_scaled, scaler,
            sent_score, sent_label, pos, neg, news_list
        )

        return jsonify({
            "success": True,
            "data": result
        })

    except RuntimeError as e:
        # Binance API or other runtime errors
        return jsonify({
            "success": False,
            "error": f"Prediction failed: {str(e)}"
        }), 503

    except Exception as e:
        # Unexpected errors
        app.logger.error(f"Prediction error: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred. Please try again."
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for uptime monitoring."""
    return jsonify({
        "status": "ok",
        "model_ready": MODEL_READY
    })


# ─── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Use PORT environment variable for Render, default to 10000 locally
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
