@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

if not "%~1"=="" (
    set "TARGET=%~1"
    goto handle_arg
)

:menu
cls
echo ==============================================================
echo             EXCEL / GOOGLE SHEET AUTOMATION RUNNER
echo ==============================================================
echo.
echo Select which Excel automation you want to run:
echo.
echo   [1]  Run ALL Excel Automations (Registrations + Donor Motivation)
echo   [2]  Run Master System Registrations (Admin, User, Bloodbank)
echo   [3]  Run Donor Motivation Alerts Only
echo   [4]  Reset Excel Queues with Fresh Sample Data (Pending/Null)
echo   [0]  Exit
echo.
echo ==============================================================
set /p choice="Enter your choice (0-4): "

if "%choice%"=="1" goto run_all_excel
if "%choice%"=="2" goto run_registration
if "%choice%"=="3" goto run_donor
if "%choice%"=="4" goto run_reset
if "%choice%"=="0" goto end

echo Invalid option. Please choose 0-4.
pause
goto menu

:handle_arg
if /i "%TARGET%"=="all" goto run_all_excel
if /i "%TARGET%"=="reg" goto run_registration
if /i "%TARGET%"=="register" goto run_registration
if /i "%TARGET%"=="registration" goto run_registration
if /i "%TARGET%"=="donor" goto run_donor
if /i "%TARGET%"=="reset" goto run_reset

echo Unknown target: %TARGET%
echo Available targets: all, registration, donor, reset
exit /b 1

:run_all_excel
echo.
echo ==============================================================
echo [1/2] Running Master System Registrations from Excel...
echo ==============================================================
python -m robot -d results tests\rpa\excel_system_registration.robot

echo.
echo ==============================================================
echo [2/2] Running Donor Motivation RPA from Excel...
echo ==============================================================
python -m robot -d results tests\rpa\excel_donor_motivation.robot
goto finish

:run_registration
echo.
echo ==============================================================
echo Running Master System Registrations (Admin, User, Bloodbank)...
echo ==============================================================
python -m robot -d results tests\rpa\excel_system_registration.robot
goto finish

:run_donor
echo.
echo ==============================================================
echo Running Donor Motivation RPA...
echo ==============================================================
python -m robot -d results tests\rpa\excel_donor_motivation.robot
goto finish

:run_reset
echo.
echo ==============================================================
echo Resetting Excel Queues with Fresh Sample Data...
echo ==============================================================
python resources\SystemRegistrationRpa.py --reset
python resources\DonorMotivationRpa.py --reset-excel
echo.
echo Queues reset successfully!
goto finish

:finish
echo.
echo ==============================================================
echo Execution complete!
echo Report: automation\results\report.html
echo Log:    automation\results\log.html
echo ==============================================================
:end
