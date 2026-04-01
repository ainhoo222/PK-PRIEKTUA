@echo off
REM Script para ejecutar Streamix (backend y frontend)

REM Ejecutar backend en nueva ventana
start "Backend" cmd /k "cd backend && ..\.venv\Scripts\activate && python app.py"

REM Ejecutar frontend en nueva ventana
start "Frontend" cmd /k "cd frontend && npm run dev"

echo Servidores iniciados. Backend en http://127.0.0.1:5000, Frontend en http://localhost:5173