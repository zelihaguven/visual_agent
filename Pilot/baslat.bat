@echo off
rem Pilot arayüzünü başlatır (çift tıkla). Tarayıcı: http://localhost:8501  Kapatmak: bu pencereyi kapat.
rem Ortam: ..\.venv. Yoksa geçici olarak eski kopyanın ortamı (Desktop\visual_agent_repo\.venv) kullanılır.
cd /d "%~dp0"
set PYTHONUTF8=1
set "VENV=%~dp0..\.venv"
if not exist "%VENV%\Scripts\streamlit.exe" set "VENV=%~dp0..\..\visual_agent_repo\.venv"
if not exist "%VENV%\Scripts\streamlit.exe" (
    echo Python ortami bulunamadi. Kurulum: README.md
    pause
    exit /b 1
)
"%VENV%\Scripts\streamlit.exe" run app.py --server.port 8501
pause
