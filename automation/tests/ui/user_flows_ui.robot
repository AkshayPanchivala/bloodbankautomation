*** Settings ***
Documentation     UI tests for User Role workflows driven from Excel / Google Sheet.
Library           SeleniumLibrary
Library           ../../resources/ExcelDataDriver.py
Resource          ../../resources/ui_keywords.robot

*** Test Cases ***
Verify User Signup Form Driven From Excel Sheet
    [Documentation]    Reads pending user data from Excel/Google Sheet, fills UI signup form, and marks status Completed.
    [Tags]             register    signup    user    excel
    
    ${record}=    Get Pending Registration Record    role=User
    
    IF    ${record} is None
        Pass Execution    No pending User records found in Excel/Google Sheet. All rows already marked Completed!
    END
    
    Log    Processing Registration from Excel for: ${record['name']} ${record['lastname_or_contact']} (${record['email']})    console=True
    
    Open Application To    /user/signup
    
    Input Text    id=firstName    ${record['name']}
    Input Text    id=lastName     ${record['lastname_or_contact']}
    
    ${gender}=    Set Variable If    '${record['gender']}' != '' and '${record['gender']}' != 'None'    ${record['gender']}    Male
    Click Element    xpath=//input[@value='${gender}']
    
    ${raw_dob}=      Set Variable If    '${record['dob_or_openingdate']}' != '' and '${record['dob_or_openingdate']}' != 'None'    ${record['dob_or_openingdate']}    1990-01-01
    ${clean_dob}=    Evaluate    str('${raw_dob}').replace('-', '')[:8]
    Input Text    id=dob          ${clean_dob}
    
    ${age}=          Set Variable If    '${record['age']}' != '' and '${record['age']}' != 'None'    ${record['age']}    30
    Input Text    id=age          ${age}
    
    Input Text    id=phoneNo1     ${record['phone1']}
    ${phone2}=       Set Variable If    '${record['phone2']}' != '' and '${record['phone2']}' != 'None'    ${record['phone2']}    ${record['phone1']}
    Input Text    id=phoneNo2     ${phone2}
    
    Input Text    id=email        ${record['email']}
    
    ${address}=      Set Variable If    '${record['address1']}' != '' and '${record['address1']}' != 'None'    ${record['address1']}    123 Main St
    Input Text    id=address      ${address}
    
    ${pincode}=      Set Variable If    '${record['pincode']}' != '' and '${record['pincode']}' != 'None'    ${record['pincode']}    123456
    Input Text    id=pinCode      ${pincode}
    
    Input Text    id=password         ${record['password']}
    Input Text    id=passwordConfirm  ${record['password']}
    
    ${state}=        Set Variable If    '${record['state']}' != '' and '${record['state']}' != 'None'    ${record['state']}    MockState
    ${city}=         Set Variable If    '${record['city']}' != '' and '${record['city']}' != 'None'    ${record['city']}    MockCity
    Select MUI Dropdown    State    ${state}
    Select MUI Dropdown    City     ${city}
    
    Click Button    xpath=//button[@type='submit']
    Sleep    2s
    
    Mark Registration Record Completed    row_index=${record['_row_idx']}    file_path=${record['_file_path']}    remarks=Registered successfully via Frontend UI form
    Log    Updated row ${record['_row_idx']} (${record['email']}) to 'Completed' in Excel sheet!    console=True

Verify User Login Flow
    [Documentation]    Attempts to login as a user with credentials.
    [Tags]             login    user
    Login As    user    mockuser@example.com    Password123_
    Sleep    1s
    Logout

Verify User Want To Donate Flow
    [Documentation]    Tests that a logged in user can access the donate form and select dropdowns.
    [Tags]             donate    user
    Login As    user    mockuser@example.com    Password123_
    Open Application To    /user/wanttodonate
    Wait Until Page Contains    Search Blood Stock    timeout=5s
    Select MUI Dropdown    State    MockState
    Select MUI Dropdown    City     MockCity
    Sleep    2s
    Logout
