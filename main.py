# main.py - Railway entry point for Kolam Generator
from backend import app
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Kolam Generator on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)