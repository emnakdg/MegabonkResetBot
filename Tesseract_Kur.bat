@echo off
color 0A
title Tesseract-OCR Otomatik Kurulum (Megabonk Bot i&#231;in)
echo.
echo ========================================================
echo Megabonk Bot yazilarin okunabilmesi (OCR) icin acik kaynakli
echo Tesseract yazilimina ihtiyac duyar.
echo.
echo Kurulum internetten otomatik indirilip sessizce yapilacaktir.
echo ========================================================
echo.
echo Indiriliyor ve kuruluyor... (Bu islem birkac dakika surebilir)
winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements --silent

echo.
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo Kurulum basariyla tamamlandi! Artik botu acabilirsiniz.
) else (
    echo Kurulumda bir sorun olusmus olabilir. 
    echo Lutfen Github'dan "Tesseract-OCR" yazilimini manuel indirip kurun.
)
echo.
pause
