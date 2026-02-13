@echo off
echo Starting ChartAnalyzer...
echo.

:: Start backend in a new window
echo Starting backend server on http://localhost:8000
start "ChartAnalyzer Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait a moment for backend to start
timeout /t 2 /nobreak >nul

:: Start frontend in a new window
echo Starting frontend server on http://localhost:5173
start "ChartAnalyzer Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both servers are starting...
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to exit this window (servers will keep running)
pause >nul
