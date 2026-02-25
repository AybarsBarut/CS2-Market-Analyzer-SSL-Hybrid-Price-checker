@echo off
chcp 65001 >nul
color 0A

echo ===================================================
echo CS2 Price Checker Web - Startup Script
echo ===================================================

echo.
echo [INFO] Python kurulumu kontrol ediliyor... / Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [UYARI/WARNING] Python sisteminizde bulunamadi! / Python not found on your system!
    echo [INFO] Python indirilip kuruluyor... Lutfen bekleyin. / Downloading and installing Python... Please wait.
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    
    if %errorlevel% neq 0 (
        echo.
        echo [HATA/ERROR] Otomatik kurulum basarisiz oldu. / Automatic installation failed.
        echo Lutfen https://www.python.org/downloads/ adresinden Python'u manuel olarak indirip kurun. / Please download and install Python manually from https://www.python.org/downloads/
        echo Kurulum sirasinda "Add Python to PATH" secenegini isaretlemeyi unutmayin! / Don't forget to check "Add Python to PATH" during installation!
        pause
        exit /b
    )
    
    echo.
    echo [BASARILI/SUCCESS] Python kuruldu. Degisikliklerin aktif olmasi icin lutfen bu pencereyi kapatin ve start.bat dosyasini YENIDEN CALISTIRIN. / Python installed. Please close this window and RUN start.bat AGAIN for changes to take effect.
    pause
    exit /b
)

echo.
echo [INFO] Gerekli kutuphaneler yukleniyor ve kontrol ediliyor... / Loading and checking required libraries...
python -m pip install --upgrade pip >nul 2>&1
pip install streamlit pandas numpy requests pandas_ta plotly

echo.
echo.
echo [INFO] Uygulama baslatiliyor (Port: 8501)... / Starting the application (Port: 8501)...
:: Uygulamayı kendi penceresine sahip ayrı bir cmd olarak başlatıyoruz, böylece stop.bat ile durdurabiliriz
:: Streamlit'in kendi portunu belirtip, browser'i bizim acmamiz daha saglikli
start "CS2PriceAnalysis_Server" cmd /c "python -m streamlit run cs2_price_analysis.py --server.port 8501 --server.headless true"

echo.
echo [INFO] Tarayici sayfasinin acilmasi icin bekleniyor... / Waiting for the browser page to open...
timeout /t 3 >nul

echo [BASARILI/SUCCESS] Uygulama basariyla baslatildi! Tarayicida localhost:8501 adresine gidiliyor... / Application started successfully! Navigating to localhost:8501 in browser...
start http://localhost:8501
echo [BILGI/INFO] Uygulamayi kapatmak istediginizde stop.bat dosyasini calistirin. / Run stop.bat when you want to close the application.
timeout /t 5 >nul
exit
