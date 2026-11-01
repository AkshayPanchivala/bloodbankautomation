@echo off
cd /d "%~dp0"
echo ==============================================================
echo Running System Registrations from Excel / Google Sheet...
echo Handles: Admin, User, and Bloodbank Registrations
echo Reads Pending/Null rows from Excel sheet and marks Completed.
echo ==============================================================
python resources\SystemRegistrationRpa.py --simulate
echo.
