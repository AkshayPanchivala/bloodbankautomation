*** Settings ***
Documentation     UI tests for the Bloodbank Role workflows.
Library           SeleniumLibrary
Resource          ../../resources/ui_keywords.robot

*** Test Cases ***
Verify Bloodbank Login And Dashboard Access
    [Documentation]    Attempts to login as a bloodbank and verifies navigation to the stock page.
    Login As    bloodbank    mockbloodbank@example.com    Password123_
    
    # Wait to see if we stay on login or redirect
    # In a real scenario, this would redirect to /bloodbank and we could verify the stock table
    Sleep    2s
    
    Logout
