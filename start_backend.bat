@echo off
echo ========================================
echo Starting Nyaya AI Backend Server
echo ========================================
echo.

cd /d "%~dp0"

echo Loading environment variables...
set HMAC_SECRET_KEY=nyaya-ai-secret-key-2025-production-change-this-in-production
set PORT=8000
set HOST=0.0.0.0

echo Starting FastAPI server on http://localhost:8000
echo.
echo API Documentation will be available at:
echo - Swagger UI: http://localhost:8000/docs
echo - ReDoc: http://localhost:8000/redoc
echo - Root Info: http://localhost:8000/
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

pause
