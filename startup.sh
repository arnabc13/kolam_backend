#!/bin/bash
# startup.sh - Production startup script

echo "🚀 Starting Kolam Generator in Production Mode"
echo "============================================="

# Set environment variables
export FLASK_ENV=production
export PYTHONPATH=$PWD

# Check Python version
python --version

# Install production requirements if needed
if [ -f requirements.txt ]; then
    pip install -r requirements.txt --quiet
fi

# Start with Gunicorn (preferred) or fallback to Flask
if command -v gunicorn &> /dev/null; then
    echo "✅ Starting with Gunicorn (production server)"
    gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 main:app
else
    echo "⚠️  Gunicorn not found, using Flask (development server)"
    python main.py
fi
