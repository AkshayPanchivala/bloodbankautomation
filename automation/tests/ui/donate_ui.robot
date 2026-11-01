*** Settings ***
Documentation     UI test for User Want To Donate flow.
Library           SeleniumLibrary
Resource          ../../resources/ui_keywords.robot
Test Teardown     Close Browser

*** Test Cases ***
Verify User Want To Donate Flow
    [Documentation]    Tests that a logged in user can access the donate form and select dropdowns.
    [Tags]             donate    user
    # Login as the mock user that was injected by MockDataSeeder
    Login As    user    mockuser@example.com    Password123_
    
    # Navigate to Want To Donate (which is accessible now that we are logged in)
    Open Application To    /user/wanttodonate
    
    # Wait for the table to render
    Wait Until Page Contains    Search Blood Stock    timeout=5s
    
    # Test State and City MUI Dropdowns
    Select MUI Dropdown    State    MockState
    Select MUI Dropdown    City     MockCity
    
    Sleep    2s
    Logout

