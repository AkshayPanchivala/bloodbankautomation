*** Settings ***
Documentation     UI test for User / Admin Login flow driven from Excel or test credentials.
Library           SeleniumLibrary
Library           ../../resources/ExcelDataDriver.py
Resource          ../../resources/ui_keywords.robot
Test Teardown     Close Browser

*** Variables ***
${DEFAULT_EMAIL}     mockuser@example.com
${DEFAULT_PASSWORD}  Password123_

*** Test Cases ***
User Can Attempt Login Driven From Excel
    [Documentation]    Opens browser, reads credentials from Excel or defaults, inputs credentials, and submits.
    [Tags]             login    auth    user    excel
    
    # Try fetching a user record from Excel
    ${record}=    Get Pending Registration Record    role=User
    
    ${email}=       Set Variable If    ${record} is not None and '${record['email']}' != ''    ${record['email']}    ${DEFAULT_EMAIL}
    ${password}=    Set Variable If    ${record} is not None and '${record['password']}' != ''    ${record['password']}    ${DEFAULT_PASSWORD}
    
    Log    Attempting UI login with: ${email}    console=True
    
    Open Application To    /login/user
    Wait Until Element Is Visible    id=email    timeout=10s
    
    Input Text         id=email       ${email}
    Input Text         id=password    ${password}
    Click Button       xpath=//button[@type='submit']
    
    Sleep              2s
