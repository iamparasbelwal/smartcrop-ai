@echo off
cd /d "%~dp0"
.\.venv\Scripts\python.exe SmartCrop-AI-Web\server.py --port 8000
pause
