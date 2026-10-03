@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title GHEP ANH THEO TIMELINE
color 0B
cls
echo ==========================================================
echo    GHEP ANH THEO TIMELINE
echo    Doc SO o dau ten file: anh 10.xxx = dong 10
echo ==========================================================
echo.
where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo  [LOI] May chua co FFmpeg.
  echo        Mo Thiet bi dau cuoi ^(Quan tri vien^) va dan:
  echo            winget install Gyan.FFmpeg
  goto :ket
)

echo  [1/2] Keo FILE TIMELINE tha vao day roi nhan Enter.
set "TL="
set /p "TL=       File timeline: "
set "TL=!TL:"=!"
if not exist "!TL!" ( echo. & echo  [LOI] Khong thay file timeline. & goto :ket )
echo.
echo  [2/2] Keo THU MUC ANH tha vao day roi nhan Enter.
set "TM="
set /p "TM=       Thu muc anh: "
set "TM=!TM:"=!"
if not exist "!TM!\" ( echo. & echo  [LOI] Khong thay thu muc. & goto :ket )
for %%F in ("!TL!") do set "TL=%%~fF"
cd /d "!TM!"
cls
echo ==========================================================
echo    KIEM TRA DU LIEU
echo ==========================================================
echo.

set "EXT="
for %%E in (jpg jpeg jfif png webp bmp) do if not defined EXT if exist "*.%%E" set "EXT=%%E"
if not defined EXT ( echo  [LOI] Thu muc khong co anh nao. & goto :ket )
set /a SO=0
for %%F in (*.!EXT!) do set /a SO+=1
set "LAN="
for %%E in (jpg jpeg jfif png webp bmp) do if /i not "%%E"=="!EXT!" if exist "*.%%E" set "LAN=!LAN! .%%E"
if defined LAN (
  echo  [LOI] Thu muc lan duoi file khac:!LAN!
  echo        Doi het ve .!EXT! roi chay lai.
  goto :ket
)
echo  Anh       : !SO! file duoi .!EXT!

set "FRM="
set /a SOCANH=0 & set /a TONGF=0 & set /a NGAN=0
for /f "usebackq tokens=1 delims=,; 	" %%A in ("!TL!") do (
  set "v=%%A"
  if not "!v!"=="" (
    echo !v!| findstr /r /c:"^[0-9][0-9]*$" >nul && (
      set /a SOCANH+=1 & set /a TONGF+=!v!
      if !v! LSS 15 set /a NGAN+=1
      set "FRM=!FRM! !v!"
      set "T!SOCANH!=!v!"
    )
  )
)
if !SOCANH!==0 ( echo  [LOI] Timeline khong co dong so hop le. & goto :ket )
set /a TS=TONGF/30 & set /a TM2=TS/60 & set /a TG=TS%%60
echo  Timeline  : !SOCANH! dong  ^|  !TONGF! frame  ^|  !TM2! phut !TG! giay
if !NGAN! GTR 0 echo  Chu y      : !NGAN! canh ngan duoi 0.5 giay
if not "!SO!"=="!SOCANH!" (
  echo.
  echo  [LOI] So anh ^(!SO!^) khac so dong timeline ^(!SOCANH!^).
  goto :ket
)
echo  Doi chieu : !SO! anh = !SOCANH! dong   ^(KHOP^)
echo.

rem ===== DAT ANH VAO DUNG SO CUA NO =====
echo  Dang doc so o dau ten tung file...
if exist _ghep rd /s /q _ghep
mkdir _ghep
set /a DAT=0
for %%F in (*.!EXT!) do (
  set "fn=%%~nF"
  set "num="
  for /f "tokens=1 delims=.-_ " %%A in ("!fn!") do set "num=%%A"
  echo !num!| findstr /r /c:"^[0-9][0-9]*$" >nul || (
    echo.
    echo  [LOI] File nay khong bat dau bang so:
    echo        %%F
    echo        Moi ten file phai bat dau bang so thu tu canh.
    goto :ket
  )
  set /a n=1!num! - 1
  set /a n=!num!
  if !n! LSS 1 ( echo  [LOI] So khong hop le o file %%F & goto :ket )
  if !n! GTR !SOCANH! ( echo  [LOI] File %%F co so !n! vuot qua !SOCANH! & goto :ket )
  set "pp=0000!n!"
  set "pp=!pp:~-5!"
  if exist "_ghep\!pp!.!EXT!" (
    echo.
    echo  [LOI] Hai anh cung mang so !n!. File thu hai la:
    echo        %%F
    goto :ket
  )
  copy /y "%%F" "_ghep\!pp!.!EXT!" >nul
  set /a DAT+=1
  if !n!==1 set "N1=%%F"
  if !n!==2 set "N2=%%F"
  if !n!==3 set "N3=%%F"
  set /a c1=SOCANH-2
  if !n!==!c1! set "M1=%%F"
  set /a c2=SOCANH-1
  if !n!==!c2! set "M2=%%F"
  if !n!==!SOCANH! set "M3=%%F"
)
set /a DEM=0
for %%F in (_ghep\*.!EXT!) do set /a DEM+=1
if not "!DEM!"=="!SOCANH!" (
  echo.
  echo  [LOI] Chi dat duoc !DEM!/!SOCANH! anh, co so bi thieu.
  goto :ket
)
echo  Da dat du !DEM! anh vao dung so cua chung.
echo.
echo  ----------------------------------------------------------
echo    Anh 1 ^(!T1! frame^)  =  !N1!
echo    Anh 2 ^(!T2! frame^)  =  !N2!
echo    Anh 3 ^(!T3! frame^)  =  !N3!
echo    ...
set /a c1=SOCANH-2 & set /a c2=SOCANH-1
for %%X in (!c1!) do echo    Anh %%X  =  !M1!
for %%X in (!c2!) do echo    Anh %%X  =  !M2!
echo    Anh !SOCANH!  =  !M3!
echo  ----------------------------------------------------------
echo.
echo   Anh 1 phai la canh mo dau, anh !SOCANH! phai la canh ket.
echo   Dung thi bam phim bat ky. Sai thi dong cua so lai.
echo.
pause
echo.

cd _ghep
set /a i=0
if exist danhsach.txt del danhsach.txt
for %%D in (!FRM!) do (
  set /a i+=1
  set "pp=0000!i!" & set "pp=!pp:~-5!"
  set /a gy=%%D/30
  set /a le=^(%%D%%%%30^)*1000000/30
  set "le=000000!le!"
  echo file '!pp!.!EXT!'>>danhsach.txt
  echo duration !gy!.!le:~-6!>>danhsach.txt
  set "cuoi=!pp!"
)
echo file '!cuoi!.!EXT!'>>danhsach.txt
echo  Dang ghep video, dung dong cua so...
echo  ----------------------------------------------------------
set "VF=scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p"
ffmpeg -y -hide_banner -loglevel error -stats -f concat -safe 0 -i danhsach.txt -r 30 -vf "!VF!" -c:v libx264 -crf 18 -preset veryfast "..\video-anh.mp4"
cd ..
echo  ----------------------------------------------------------
if not exist "video-anh.mp4" ( echo  [LOI] Khong tao duoc video. & goto :ket )
echo.
echo  Dang do lai do dai video that...
call :demframe
if not defined NF ( echo  [!] Khong doc duoc so frame. & goto :xong )
set /a LECH=NF-TONGF
if !LECH! LSS 0 set /a LECH=-LECH
echo    Can co  : !TONGF! frame
echo    Thuc te : !NF! frame
if !LECH! LEQ 1 ( echo    Lech    : !LECH! frame   ^(DAT^) & goto :xong )
echo    Lech    : !LECH! frame   ^(KHONG DAT^)
echo.
echo  Chuyen sang che do khop tuyet doi, render tung anh dung so frame.
echo.
cd _ghep
if exist clip rd /s /q clip
mkdir clip
if exist noiclip.txt del noiclip.txt
set /a i=0
for %%D in (!FRM!) do (
  set /a i+=1
  set "pp=0000!i!" & set "pp=!pp:~-5!"
  <nul set /p "=   [!i!/!SOCANH!] "
  ffmpeg -y -hide_banner -loglevel error -loop 1 -i "!pp!.!EXT!" -frames:v %%D -vf "!VF!" -r 30 -c:v libx264 -crf 18 -preset veryfast "clip\!pp!.mp4"
  echo file 'clip/!pp!.mp4'>>noiclip.txt
)
echo.
echo  Dang noi cac doan lai...
ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i noiclip.txt -c copy "..\video-anh.mp4"
cd ..
call :demframe
echo.
echo    Can co  : !TONGF! frame
echo    Thuc te : !NF! frame
goto :xong

:demframe
set "NF="
for /f "delims=" %%K in ('ffprobe -v error -select_streams v:0 -show_entries stream^=nb_frames -of csv^=p^=0 "video-anh.mp4" 2^>nul') do set "NF=%%K"
if "!NF!"=="N/A" set "NF="
if not defined NF for /f "delims=" %%K in ('ffprobe -v error -count_frames -select_streams v:0 -show_entries stream^=nb_read_frames -of csv^=p^=0 "video-anh.mp4" 2^>nul') do set "NF=%%K"
exit /b

:xong
echo.
echo  ==========================================================
echo     XONG. video-anh.mp4 nam trong thu muc anh cua ban.
echo  ==========================================================
echo.
echo  Nhan phim bat ky de mo thu muc.
pause >nul
explorer "%CD%"
goto :eof

:ket
echo.
pause