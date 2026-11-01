*** Settings ***
Documentation     RPA test suite for Excel & Google Sheet System Registration Automation.
...               Reads registration records for Admin, User, and Bloodbank roles from Excel.
...               Only processes rows where Status is 'Pending' or null/empty.
...               Upon completion, updates the Status to 'Completed' in the Excel sheet.
Library           Process
Library           OperatingSystem

Suite Setup       Initialize Python Path

*** Variables ***
${PYTHON_EXE}     python
${REG_SCRIPT}     ${CURDIR}/../../resources/SystemRegistrationRpa.py

*** Keywords ***
Initialize Python Path
    ${py}=    Evaluate    sys.executable    modules=sys
    Set Suite Variable    ${PYTHON_EXE}    ${py}

*** Test Cases ***
Reset Registration Excel Queue With Sample Data
    [Documentation]    Initializes or resets the Excel sheet with fresh test records (Pending, Null, Completed) for all roles.
    ${result}=    Run Process    ${PYTHON_EXE}    ${REG_SCRIPT}    --reset
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    ${result.rc}    0    msg=Failed to reset registration Excel queue: ${result.stderr}
    Should Contain    ${result.stdout}    System registration Excel queue initialized

Process Pending And Null Registrations For All Roles
    [Documentation]    Runs RPA to process ONLY rows with Status 'Pending' or null, and updates them to 'Completed'.
    ${result}=    Run Process    ${PYTHON_EXE}    ${REG_SCRIPT}    --simulate
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    ${result.rc}    0    msg=System registration RPA failed: ${result.stderr}
    
    # Verify that each role was processed
    Should Contain    ${result.stdout}    Role: Admin
    Should Contain    ${result.stdout}    Role: User
    Should Contain    ${result.stdout}    Role: Bloodbank
    
    # Verify that already completed rows were skipped
    Should Contain    ${result.stdout}    SKIPPED -> Admin: existing_admin@example.com
    
    # Verify summary of processed items
    Should Contain    ${result.stdout}    STATUS UPDATED TO 'Completed'
    Should Contain    ${result.stdout}    Registrations Processed & Completed: 5
    Should Contain    ${result.stdout}    Rows Skipped (Already Completed):   1

Verify Completed Registrations Are Skipped On Re-Execution
    [Documentation]    Running the automation again should skip all rows because all are now marked 'Completed'.
    ${result}=    Run Process    ${PYTHON_EXE}    ${REG_SCRIPT}    --simulate
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    ${result.rc}    0    msg=Re-execution failed: ${result.stderr}
    
    # Now 0 registrations should be processed, all 6 skipped
    Should Contain    ${result.stdout}    Registrations Processed & Completed: 0
    Should Contain    ${result.stdout}    Rows Skipped (Already Completed):   6

