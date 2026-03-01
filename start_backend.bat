@echo off
cd backend
call venv\Scripts\activate
uvicorn app.main:app --port 8000 --reload
pause
