*** Settings ***
Documentation     UI tests for the Admin Role workflows.
Library           SeleniumLibrary
Resource          ../../resources/ui_keywords.robot

*** Test Cases ***
Verify Admin Login And Add Bloodbank Deep Fill
    [Documentation]    Attempts to login as an admin and deeply fills the Add Bloodbank form.
    Login As    admin    admin@example.com    Password123_
    
    # In a real scenario, this would redirect to /admin/bloodbanks
    # We can simulate navigating directly to the add bloodbank page to verify it loads if authorized
    Open Application To    /admin/addbloodbank
    
    # Wait for the form to render
    Wait Until Element Is Visible    id=bloodbankName    timeout=5s
    
    # Fill standard text fields
    Input Text    id=bloodbankName    City Central Bloodbank
    Input Text    id=contactPerson    Dr. Smith
    Input Text    id=address1         456 Medical Ave
    Input Text    id=address2         Suite 100
    Input Text    id=pinCode          654321
    Input Text    id=phoneNo1         9876543210
    Input Text    id=phoneNo2         0123456789
    
    # Generate a random email
    ${random_num}=    Evaluate    random.randint(1000, 9999)    modules=random
    Input Text    id=email        bloodbank${random_num}@example.com
    
    Input Text    id=openingDate      01012023
    
    Input Text    id=password         Password123_
    Input Text    id=passwordConfirm  Password123_
    
    # Test MUI Dropdowns
    Select MUI Dropdown    State       MockState
    Select MUI Dropdown    City        MockCity
    Select MUI Dropdown    Category    Government
    
    # Try to submit the form
    Click Button       xpath=//button[@type='submit']
    
    Sleep    2s
    
    Logout
