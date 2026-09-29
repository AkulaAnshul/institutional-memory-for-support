@echo off
cd /d "%~dp0"
echo ==^> Setting up the Institutional Memory console

where conda >nul 2>nul
if %errorlevel%==0 (
  if not exist ".conda\python.exe" (
    echo Creating a local conda environment .\.conda ...
    conda create --prefix .\.conda python=3.11 -y
  ) else (
    echo Local conda environment already exists.
  )
  set "PY=.conda\python.exe"
  set "PIP=.conda\Scripts\pip.exe"
) else (
  where python >nul 2>nul
  if not %errorlevel%==0 (
    echo Python 3.11+ is required. Install Anaconda or Python and try again.
    pause
    exit /b 1
  )
  if not exist ".venv\Scripts\python.exe" (
    echo Creating a local virtual environment .\.venv ...
    python -m venv .venv
  )
  set "PY=.venv\Scripts\python.exe"
  set "PIP=.venv\Scripts\pip.exe"
)

echo Installing Python packages ^(this can take a minute^) ...
"%PIP%" install -q --upgrade pip
"%PIP%" install -q -r requirements.txt

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo.
  echo A .env file was created. Open it and paste your GROQ_API_KEY and HINDSIGHT_API_KEY.
)

echo.
echo Setup complete.
echo Start the console by double-clicking run.bat
pause
