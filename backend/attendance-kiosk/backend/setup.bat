@echo off
REM FRAMES Attendance Kiosk - Backend Setup Script (Windows)

echo ==================================================
echo 🎥 FRAMES Attendance Kiosk - Backend Setup
echo ==================================================
echo.

REM Check Python version
echo 🐍 Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)
python --version
echo ✅ Python found
echo.

REM Create virtual environment
echo 📦 Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated
echo.

REM Install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo ✅ Dependencies installed
echo.

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo ⚙️ Creating .env file...
    copy .env.example .env
    echo ✅ .env file created
    echo.
    echo ⚠️  IMPORTANT: Edit .env file with your database credentials!
    echo    notepad .env
    echo.
) else (
    echo ✅ .env file already exists
)

echo.
echo ==================================================
echo ✅ Setup Complete!
echo ==================================================
echo.
echo Next steps:
echo 1. Edit .env file with your database credentials:
echo    notepad .env
echo.
echo 2. Test database connection:
echo    python kiosk_api.py
echo.
echo 3. Backend will run on: http://localhost:5001
echo.
echo ==================================================
pause
