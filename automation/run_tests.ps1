<#
.SYNOPSIS
    Cross-platform PowerShell automation runner for Blood Bank Management
.DESCRIPTION
    Allows running specific test suites, UI cases, or Excel automations.
#>

param(
    [ValidateSet("all", "api", "ui", "ui-register", "ui-login", "ui-donate", "ui-user", "ui-admin", "ui-bb", "rpa", "excel", "excel-reg", "excel-donor", "stock-alert", "seed")]
    [string]$Target = "menu"
)

$AutomationDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $AutomationDir

if (Test-Path "venv\Scripts\activate.ps1") {
    & "venv\Scripts\activate.ps1"
}

function Show-Menu {
    Clear-Host
    Write-Host "==============================================================" -ForegroundColor Cyan
    Write-Host "          BLOOD BANK MANAGEMENT - AUTOMATION RUNNER           " -ForegroundColor Yellow
    Write-Host "==============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Select the test suite or RPA task you want to run:"
    Write-Host ""
    Write-Host "  [1]  Run All Tests (API + UI + RPA)"
    Write-Host "  [2]  Run API Tests Only"
    Write-Host "  [3]  Run UI Tests - All Flows"
    Write-Host "  [4]  Run UI Tests - User Register / Signup Only"
    Write-Host "  [5]  Run UI Tests - User Login Only"
    Write-Host "  [6]  Run UI Tests - User Donate Blood Only"
    Write-Host "  [7]  Run UI Tests - Admin Flows Only"
    Write-Host "  [8]  Run UI Tests - Bloodbank Flows Only"
    Write-Host "  [9]  Run RPA Tasks - All"
    Write-Host "  [10] Run System Registrations from Excel (Admin, User, Bloodbank)"
    Write-Host "  [11] Run Donor Motivation Alerts from Excel"
    Write-Host "  [12] Run Low Stock Email Alert RPA Only"
    Write-Host "  [13] Seed Mock Data & Reset Excel Queues"
    Write-Host "  [0]  Exit"
    Write-Host ""
    Write-Host "==============================================================" -ForegroundColor Cyan
    $choice = Read-Host "Enter your choice (0-13)"
    
    switch ($choice) {
        "1"  { Run-Suite "all" }
        "2"  { Run-Suite "api" }
        "3"  { Run-Suite "ui" }
        "4"  { Run-Suite "ui-register" }
        "5"  { Run-Suite "ui-login" }
        "6"  { Run-Suite "ui-donate" }
        "7"  { Run-Suite "ui-admin" }
        "8"  { Run-Suite "ui-bb" }
        "9"  { Run-Suite "rpa" }
        "10" { Run-Suite "excel-reg" }
        "11" { Run-Suite "excel-donor" }
        "12" { Run-Suite "stock-alert" }
        "13" { Run-Suite "seed" }
        "0"  { exit }
        default { Write-Host "Invalid option" -ForegroundColor Red; Pause; Show-Menu }
    }
}

function Run-Suite($suite) {
    switch ($suite) {
        "all" {
            Write-Host "`n[1/3] Running API Tests..." -ForegroundColor Green
            python -m robot -d results -v BASE_URL:http://localhost:5000 tests\api\
            Write-Host "`n[2/3] Seeding Mock Data & Running UI Tests..." -ForegroundColor Green
            python resources\MockDataSeeder.py
            python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\
            Write-Host "`n[3/3] Running RPA Tasks..." -ForegroundColor Green
            python -m robot -d results tests\rpa\
        }
        "api" {
            python -m robot -d results -v BASE_URL:http://localhost:5000 tests\api\
        }
        "ui" {
            python resources\MockDataSeeder.py
            python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\
        }
        "ui-register" {
            python resources\MockDataSeeder.py
            python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\register_ui.robot
        }
        "ui-login" {
            python resources\MockDataSeeder.py
            python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\login_ui.robot
        }
        "ui-donate" {
            python resources\MockDataSeeder.py
            python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\donate_ui.robot
        }
        "ui-user" {
            python resources\MockDataSeeder.py
            python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\user_flows_ui.robot
        }
        "ui-admin" {
            python resources\MockDataSeeder.py
            python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\admin_flows_ui.robot
        }
        "ui-bb" {
            python resources\MockDataSeeder.py
            python -m robot -d results -v FRONTEND_URL:http://localhost:3000 tests\ui\bloodbank_flows_ui.robot
        }
        "rpa" {
            python -m robot -d results tests\rpa\
        }
        "excel-reg" {
            Write-Host "`nRunning System Registration RPA from Excel/Google Sheet..." -ForegroundColor Green
            python -m robot -d results tests\rpa\excel_system_registration.robot
        }
        "excel-donor" {
            Write-Host "`nRunning Donor Motivation RPA from Excel/Google Sheet..." -ForegroundColor Green
            python -m robot -d results tests\rpa\excel_donor_motivation.robot
        }
        "excel" {
            Write-Host "`nRunning All Excel RPA..." -ForegroundColor Green
            python -m robot -d results tests\rpa\excel_system_registration.robot
            python -m robot -d results tests\rpa\excel_donor_motivation.robot
        }
        "stock-alert" {
            python -m robot -d results tests\rpa\low_stock_email_alert.robot
        }
        "seed" {
            python resources\MockDataSeeder.py
        }
    }
    
    Write-Host "`nExecution complete! Reports saved to automation\results\" -ForegroundColor Cyan
}

if ($Target -eq "menu") {
    Show-Menu
} else {
    Run-Suite $Target
}
