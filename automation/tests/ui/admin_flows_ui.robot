*** Settings ***
Documentation     Data-driven UI tests for Admin Add Bloodbank reading directly from Excel / Google Sheet.
Library           SeleniumLibrary
Library           ../../resources/ExcelDataDriver.py
Resource          ../../resources/ui_keywords.robot
Test Teardown     Close Browser

*** Test Cases ***
Verify Admin Add Bloodbank Form Driven From Excel Sheet
    [Documentation]    Reads pending/null bloodbank data from Excel, logs in as admin, fills UI form, and marks status Completed.
    [Tags]             admin    bloodbank    excel
    
    # 1. Fetch the next pending or null Bloodbank record from Excel / Google Sheet
    ${record}=    Get Pending Registration Record    role=Bloodbank
    
    IF    ${record} is None
        Pass Execution    No pending Bloodbank records found in Excel/Google Sheet. All rows already marked Completed!
    END
    
    Log    Processing Bloodbank Registration from Excel for: ${record['name']} (${record['email']})    console=True
    
    # 2. Login as Admin
    Login As    admin    admin@example.com    Password123_
    
    Open Application To    /admin/addbloodbank
    Wait Until Element Is Visible    id=bloodbankName    timeout=10s
    
    # 3. Fill form fields dynamically from the Excel row data
    Input Text    id=bloodbankName    ${record['name']}
    
    ${contact}=   Set Variable If    '${record['lastname_or_contact']}' != '' and '${record['lastname_or_contact']}' != 'None'    ${record['lastname_or_contact']}    Dr. Incharge
    Input Text    id=contactPerson    ${contact}
    
    ${addr1}=     Set Variable If    '${record['address1']}' != '' and '${record['address1']}' != 'None'    ${record['address1']}    456 Medical Ave
    Input Text    id=address1         ${addr1}
    
    ${addr2}=     Set Variable If    '${record['address2']}' != '' and '${record['address2']}' != 'None'    ${record['address2']}    Suite 100
    Input Text    id=address2         ${addr2}
    
    ${pincode}=   Set Variable If    '${record['pincode']}' != '' and '${record['pincode']}' != 'None'    ${record['pincode']}    654321
    Input Text    id=pinCode          ${pincode}
    
    Input Text    id=phoneNo1         ${record['phone1']}
    ${phone2}=    Set Variable If    '${record['phone2']}' != '' and '${record['phone2']}' != 'None'    ${record['phone2']}    ${record['phone1']}
    Input Text    id=phoneNo2         ${phone2}
    
    Input Text    id=email            ${record['email']}
    
    # Opening Date (remove dashes, e.g. 01012023)
    ${raw_date}=  Set Variable If    '${record['dob_or_openingdate']}' != '' and '${record['dob_or_openingdate']}' != 'None'    ${record['dob_or_openingdate']}    2023-01-01
    ${clean_date}= Evaluate    str('${raw_date}').replace('-', '')[:8]
    Input Text    id=openingDate      ${clean_date}
    
    Input Text    id=password         ${record['password']}
    Input Text    id=passwordConfirm  ${record['password']}
    
    # Select Dropdowns from Excel
    ${state}=     Set Variable If    '${record['state']}' != '' and '${record['state']}' != 'None'    ${record['state']}    MockState
    ${city}=      Set Variable If    '${record['city']}' != '' and '${record['city']}' != 'None'    ${record['city']}    MockCity
    ${category}=  Set Variable If    '${record['category']}' != '' and '${record['category']}' != 'None'    ${record['category']}    Government
    
    Select MUI Dropdown    State       ${state}
    Select MUI Dropdown    City        ${city}
    Select MUI Dropdown    Category    ${category}
    
    # 4. Submit form
    Click Button    xpath=//button[@type='submit']
    Sleep    2s
    
    # 5. Mark status as Completed in Excel
    Mark Registration Record Completed    row_index=${record['_row_idx']}    file_path=${record['_file_path']}    remarks=Bloodbank added successfully via Admin UI from Excel
    Log    Updated row ${record['_row_idx']} (${record['email']}) to 'Completed' in Excel sheet!    console=True
    
    Logout
