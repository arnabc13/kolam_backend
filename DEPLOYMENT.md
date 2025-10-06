# Railway Deployment Instructions

## Files to Upload:
1. main.py (the Railway-optimized version)
2. requirements.txt (with Gunicorn)
3. Procfile (Gunicorn configuration)

## Steps:
1. Replace your current main.py with the Railway-optimized version
2. Update requirements.txt to include gunicorn==21.2.0
3. Add Procfile with: web: gunicorn main:app --bind 0.0.0.0:$PORT
4. Push to GitHub
5. Railway will auto-redeploy

## Expected Result:
- No more development server warnings
- Gunicorn will be used as WSGI server
- Better performance and stability
- Proper production logging

## Verification:
Visit: https://web-production-06d8.up.railway.app/api/health
Should return: {"status": "healthy", "server": "Railway"}
