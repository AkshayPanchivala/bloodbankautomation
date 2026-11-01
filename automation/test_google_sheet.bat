@echo off
cd /d "%~dp0"
echo ==============================================
echo Testing Google Sheets Live Write-Back Webhook
echo ==============================================
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe resources\test_live_google_sheet.py
) else (
    python resources\test_live_google_sheet.py
)
echo.

