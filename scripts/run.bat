@echo off
echo Starting Sign Language Translation System...

start cmd /k "cd backend && python run.py"
timeout /t 3 /nobreak > nul
start cmd /k "cd frontend && npm run dev"

echo.
echo System running!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo WebSocket: ws://localhost:8000/ws
echo.
echo Close the windows to stop the services