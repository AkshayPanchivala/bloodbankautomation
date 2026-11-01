@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: If a parameter is passed directly (e.g. run_ui.bat register), jump directly
if not "%~1"=="" (
    set "TARGET=%~1"
    goto handle_arg
)

:menu
cls
echo ==============================================================
echo             FRONTEND UI AUTOMATION TEST RUNNER
echo ==============================================================
echo.
echo Select which UI test case to run separately:
echo.
echo   [1]  Run ALL UI Tests (Full Suite)
echo   [2]  Run User Registration / Signup Flow Only
echo   [3]  Run User Login Flow Only
echo   [4]  Run User Donate Blood Flow Only
echo   [5]  Run Admin Flow (Add Bloodbank) Only
echo   [6]  Run Bloodbank Flow (Dashboard ^& Stock) Only
echo   [0]  Exit
echo.
echo ==============================================================
set /p choice="Enter your choice (0-6): "

if "%choice%"=="1" goto run_all
if "%choice%"=="2" goto run_register
if "%choice%"=="3" goto run_login
if "%choice%"=="4" goto run_donate
if "%choice%"=="5" goto run_admin
if "%choice%"=="6" goto run_bloodbank
if "%choice%"=="0" goto end

echo Invalid option. Please choose 0-6.
pause
goto menu

:handle_arg
if /i "%TARGET%"=="all" goto run_all
if /i "%TARGET%"=="register" goto run_register
if /i "%TARGET%"=="signup" goto run_register
if /i "%TARGET%"=="login" goto run_login
if /i "%TARGET%"=="donate" goto run_donate
if /i "%TARGET%"=="admin" goto run_admin
if /i "%TARGET%"=="bloodbank" goto run_bloodbank
if /i "%TARGET%"=="bb" goto run_bloodbank

echo Unknown target: %TARGET%
echo Available targets: all, register, login, donate, admin, bloodbank
exit /b 1

:run_all
echo.
echo ==============================================
echo Running ALL UI Tests (Full Suite)...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\
goto finish

:run_register
echo.
echo ==============================================
echo Running User Registration / Signup UI Test...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\register_ui.robot
goto finish

:run_login
echo.
echo ==============================================
echo Running User Login UI Test...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\login_ui.robot
goto finish

:run_donate
echo.
echo ==============================================
echo Running User Want To Donate Blood UI Test...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\donate_ui.robot
goto finish

:run_admin
echo.
echo ==============================================
echo Running Admin Flow (Add Bloodbank) UI Test...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\admin_flows_ui.robot
goto finish

:run_bloodbank
echo.
echo ==============================================
echo Running Bloodbank Dashboard ^& Stock UI Test...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\bloodbank_flows_ui.robot
goto finish

:finish
echo.
echo ==============================================
echo UI Test Execution Complete!
echo Report: automation\results\report.html
echo Log:    automation\results\log.html
echo ==============================================
:end
