@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m video_auto gui --project "%~dp0videos\video-moi"
if errorlevel 1 pause
