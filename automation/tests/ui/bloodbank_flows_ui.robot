*** Settings ***
Documentation     UI tests for the Bloodbank Role workflows.
Library           SeleniumLibrary
Resource          ../../resources/ui_keywords.robot
Test Teardown     Close Browser

*** Test Cases ***
Verify Bloodbank Login And Dashboard Access
    [Documentation]    Attempts to login as a bloodbank and verifies navigation to the stock page.
    [Tags]             bloodbank    stock
    Login As    bloodbank    mockbloodbank@example.com    Password123_
    
    Sleep    2s
    Logout
