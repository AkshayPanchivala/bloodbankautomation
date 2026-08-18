@echo off
echo ==============================================
echo Running Blood Bank Automation Suite
echo ==============================================

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo.
echo Running API Tests...
robot -d results -v BASE_URL:http://localhost:5000 tests\api\

echo.
echo Running UI Tests...
call venv\Scripts\python.exe resources\MockDataSeeder.py
robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\

echo.
echo Running RPA Tasks...
robot -d results tests\rpa\

echo.
echo ==============================================
echo Test execution complete! 
echo Check the 'automation\results' folder for the HTML reports.
echo ==============================================
