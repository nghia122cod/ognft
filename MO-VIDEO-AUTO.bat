@echo off
chcp 65001 >nul
cd /d "%~dp0"
title VIDEO AUTO
echo Dang cap nhat ban moi nhat...
where git >nul 2>nul && git pull --ff-only
echo Dang mo app...
python -m video_auto gui --project "%~dp0videos\video-thu"
if errorlevel 1 pause
