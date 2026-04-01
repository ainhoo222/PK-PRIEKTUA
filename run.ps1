# Script para ejecutar Streamix (backend y frontend)
# Ejecuta el backend en background
Start-Process -NoNewWindow -FilePath "c:/Users/Usuario/OneDrive - UPV EHU/Escritorio/PK Proiektua/.venv/Scripts/python.exe" -ArgumentList "app.py" -WorkingDirectory "c:\Users\Usuario\OneDrive - UPV EHU\Escritorio\PK Proiektua\backend"

# Ejecuta el frontend en background
Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory "c:\Users\Usuario\OneDrive - UPV EHU\Escritorio\PK Proiektua\frontend"

Write-Host "Servidores iniciados. Backend en http://127.0.0.1:5000, Frontend en http://localhost:5173"