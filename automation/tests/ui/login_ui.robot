*** Settings ***
Documentation     UI test for the User Login flow.
Library           SeleniumLibrary
Resource          ../../resources/ui_keywords.robot

*** Variables ***
${TEST_EMAIL}     test@example.com
${TEST_PASSWORD}  password123

*** Test Cases ***
User Can Attempt Login
    [Documentation]    Opens the browser, navigates to user login, inputs credentials, and submits.
    Open Application To    /login/user
    
    # Wait for the email input to be visible
    Wait Until Element Is Visible    id=email    timeout=10s
    
    # Input credentials
    Input Text         id=email       ${TEST_EMAIL}
    Input Text         id=password    ${TEST_PASSWORD}
    
    # Click the login button
    Click Button       xpath=//button[@type='submit']
    
    # Wait a moment to observe the action before closing (optional, good for debugging)
    Sleep              2s
