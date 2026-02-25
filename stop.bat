@echo off
chcp 65001 >nul
color 0C

echo ===================================================
echo CS2 Esya Fiyati Analiz - Durdurma Komut Dosyasi
echo CS2 Item Price Analysis - Stop Script
echo ===================================================

echo.
echo [INFO] Uygulama durduruluyor... / Stopping the application...
taskkill /F /FI "WINDOWTITLE eq CS2PriceAnalysis_Server*" /T >nul 2>&1

echo.
echo [BASARILI/SUCCESS] Uygulama ve arka plan islemleri basariyla durduruldu. / Application and background processes stopped successfully.
timeout /t 3 >nul
exit
