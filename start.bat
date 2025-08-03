@echo off
echo 🕷️  Starting Haystack Web Collector Suite...

REM Check if .env file exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your settings before continuing!
    echo    Edit the .env file, then run this script again.
    pause
    exit /b 1
)

REM Create required directories
echo 📁 Creating data directories...
if not exist data mkdir data
if not exist data\downloads mkdir data\downloads
if not exist data\haystack mkdir data\haystack
if not exist logs mkdir logs

REM Start services
echo 🚀 Starting Docker services...
docker-compose up -d

REM Wait a moment for services to start
echo ⏳ Waiting for services to initialize...
timeout /t 10 /nobreak >nul

REM Check service status
echo 📊 Checking service status...
docker-compose ps

REM Display access information
echo.
echo ✅ Haystack is starting up!
echo.
echo 📱 Web Interface: http://localhost
echo 🔧 API Documentation: http://localhost:8000/docs
echo 📊 API Health Check: http://localhost:8000/health
echo.
echo 📝 To view logs: docker-compose logs -f
echo 🛑 To stop: docker-compose down
echo.
echo 🎉 Happy scraping!
pause