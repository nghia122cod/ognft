@echo off
chcp 65001 >nul
cd /d "%~dp0"
title CHAN DOAN DANG NHAP
where git >nul 2>nul && git pull --ff-only
echo.
echo Phien ban dang chay:
git log --oneline -1
echo.
echo Dang mo app giong doc va thu bam DANG NHAP... (dung cham chuot)
python -m video_auto thu-dang-nhap -p "%~dp0videos\video-thu"
echo.
echo Chup man hinh cua so nay gui Claude.
start "" "%~dp0videos\video-thu\chan-doan-dang-nhap.png"
pause
