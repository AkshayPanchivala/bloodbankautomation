@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Activate virtualenv if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: Ensure python scripts folder is in PATH if present
if exist "%APPDATA%\Python\Python314\Scripts" (
    set "PATH=%APPDATA%\Python\Python314\Scripts;%PATH%"
)

:: If a command line parameter was passed, jump directly to that routine
if not "%~1"=="" (
    set "TARGET=%~1"
    goto handle_arg
)

:menu
cls
echo ==============================================================
echo           BLOOD BANK MANAGEMENT - AUTOMATION RUNNER
echo ==============================================================
echo.
echo Select the test suite or RPA task you want to run:
echo.
echo   [1]  Run All Tests (API + UI + RPA)
echo   [2]  Run API Tests Only
echo   [3]  Run UI Tests - All Flows
echo   [4]  Run UI Tests - User Register / Signup Only
echo   [5]  Run UI Tests - User Login Only
echo   [6]  Run UI Tests - User Donate Blood Only
echo   [7]  Run UI Tests - Admin Flows (Add Bloodbank) Only
echo   [8]  Run UI Tests - Bloodbank Flows (Dashboard ^& Stock) Only
echo   [9]  Run RPA Tasks - All
echo   [10] Run System Registrations from Excel (Admin, User, Bloodbank)
echo   [11] Run Donor Motivation Alerts from Excel
echo   [12] Run Low Stock Email Alert RPA Only
echo   [13] Seed Mock Data ^& Reset Excel Queues
echo   [0]  Exit
echo.
echo ==============================================================
set /p choice="Enter your choice (0-13): "

if "%choice%"=="1" goto run_all
if "%choice%"=="2" goto run_api
if "%choice%"=="3" goto run_ui
if "%choice%"=="4" goto run_ui_register
if "%choice%"=="5" goto run_ui_login
if "%choice%"=="6" goto run_ui_donate
if "%choice%"=="7" goto run_ui_admin
if "%choice%"=="8" goto run_ui_bb
if "%choice%"=="9" goto run_rpa
if "%choice%"=="10" goto run_excel_reg
if "%choice%"=="11" goto run_excel_donor
if "%choice%"=="12" goto run_stock_alert
if "%choice%"=="13" goto run_seed
if "%choice%"=="0" goto end

echo Invalid option. Please try again.
pause
goto menu

:handle_arg
if /i "%TARGET%"=="all" goto run_all
if /i "%TARGET%"=="api" goto run_api
if /i "%TARGET%"=="ui" goto run_ui
if /i "%TARGET%"=="ui-register" goto run_ui_register
if /i "%TARGET%"=="ui-signup" goto run_ui_register
if /i "%TARGET%"=="ui-login" goto run_ui_login
if /i "%TARGET%"=="ui-donate" goto run_ui_donate
if /i "%TARGET%"=="ui-user" goto run_ui_user
if /i "%TARGET%"=="ui-admin" goto run_ui_admin
if /i "%TARGET%"=="ui-bb" goto run_ui_bb
if /i "%TARGET%"=="ui-bloodbank" goto run_ui_bb
if /i "%TARGET%"=="rpa" goto run_rpa
if /i "%TARGET%"=="excel" goto run_excel_reg
if /i "%TARGET%"=="excel-reg" goto run_excel_reg
if /i "%TARGET%"=="excel-donor" goto run_excel_donor
if /i "%TARGET%"=="stock-alert" goto run_stock_alert
if /i "%TARGET%"=="seed" goto run_seed

echo Unknown test target: %TARGET%
echo Available targets: all, api, ui, ui-register, ui-login, ui-donate, ui-user, ui-admin, ui-bb, rpa, excel-reg, excel-donor, stock-alert, seed
exit /b 1

:run_all
echo.
echo ==============================================
echo [1/3] Running API Tests...
echo ==============================================
python -m robot -d results -v BASE_URL:http://localhost:5000 tests\api\

echo.
echo ==============================================
echo [2/3] Seeding Mock Data and Running UI Tests...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\

echo.
echo ==============================================
echo [3/3] Running RPA Tasks (Excel + Email Alerts)...
echo ==============================================
python -m robot -d results tests\rpa\
goto finish

:run_api
echo.
echo ==============================================
echo Running API Tests Only...
echo ==============================================
python -m robot -d results -v BASE_URL:http://localhost:5000 tests\api\
goto finish

:run_ui
echo.
echo ==============================================
echo Running All UI Tests...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\
goto finish

:run_ui_register
echo.
echo ==============================================
echo Running UI Tests - User Register / Signup Only...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\register_ui.robot
goto finish

:run_ui_login
echo.
echo ==============================================
echo Running UI Tests - User Login Only...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\login_ui.robot
goto finish

:run_ui_donate
echo.
echo ==============================================
echo Running UI Tests - User Donate Blood Only...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\donate_ui.robot
goto finish

:run_ui_user
echo.
echo ==============================================
echo Running UI Tests - All User Flows...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\user_flows_ui.robot
goto finish

:run_ui_admin
echo.
echo ==============================================
echo Running UI Tests - Admin Flows Only...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\admin_flows_ui.robot
goto finish

:run_ui_bb
echo.
echo ==============================================
echo Running UI Tests - Bloodbank Flows Only...
echo ==============================================
python resources\MockDataSeeder.py
python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\bloodbank_flows_ui.robot
goto finish

:run_rpa
echo.
echo ==============================================
echo Running All RPA Tasks...
echo ==============================================
python -m robot -d results tests\rpa\
goto finish

:run_excel_reg
echo.
echo ==============================================================
echo Running Master System Registrations from Excel...
echo Reads Pending/Null rows for Admin, User, Bloodbank and marks Completed.
echo ==============================================================
python -m robot -d results tests\rpa\excel_system_registration.robot
goto finish

:run_excel_donor
echo.
echo ==============================================================
echo Running Donor Motivation RPA from Excel...
echo Reads Pending/Null rows from Excel/Google Sheet and marks Completed.
echo ==============================================================
python -m robot -d results tests\rpa\excel_donor_motivation.robot
goto finish

:run_stock_alert
echo.
echo ==============================================
echo Running Low Stock Email Alert RPA...
echo ==============================================
python -m robot -d results tests\rpa\low_stock_email_alert.robot
goto finish

:run_seed
echo.
echo ==============================================
echo Seeding Mock Data and Resetting Excel Queues...
echo ==============================================
python resources\MockDataSeeder.py
goto finish

:finish
echo.
echo ==============================================
echo Execution complete!
echo Report: automation\results\report.html
echo Log:    automation\results\log.html
echo ==============================================
:end
