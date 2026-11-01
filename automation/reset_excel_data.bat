@echo off
cd /d "%~dp0"
echo Resetting Excel Queues with fresh sample data (Pending, Null, Completed)...
python resources\DonorMotivationRpa.py --reset-excel
python resources\SystemRegistrationRpa.py --reset
echo.
echo Excel files reset successfully at:
echo   - automation\data\donor_motivation_queue.xlsx
echo   - automation\data\system_registration_queue.xlsx
