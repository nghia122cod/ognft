@echo off
cd /d "%~dp0"
python -m video_auto gui --project "%~dp0projects\demo"
pause
