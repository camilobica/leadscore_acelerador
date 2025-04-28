@echo off
echo 🔁 Iniciando Webhook + Cloudflare Tunnel...

:: Caminho até a pasta do seu projeto
cd C:\Users\Camilo_Bica\data_science\consultoria\portal_vhe

:: Ativar o ambiente Conda
call C:\Users\Camilo_Bica\anaconda3\Scripts\activate.bat

:: Iniciar o FastAPI no background
start uvicorn notebooks.src.webhook_server:app --reload --port 8000

:: Abrir a docs da API no navegador
start http://localhost:8000/docs

:: Esperar o servidor subir
timeout /t 3 > NUL

:: Iniciar o túnel Cloudflare
cd C:\cloudflared
cloudflared.exe tunnel --url http://localhost:8000
