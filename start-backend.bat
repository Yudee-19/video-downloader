@echo off
REM Start Backend Server

echo Starting FastAPI Backend Server...
cd backend
D:\Projects\ytdlp-demo\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
