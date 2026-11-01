*** Settings ***
Documentation     RPA test suite for Excel-driven Donor Motivation Automation.
...               Reads eligible donors from an Excel sheet only if Status is 'Pending' or null/empty.
...               Upon completion, updates the Status to 'Completed' in the Excel sheet.
Library           Process
Library           OperatingSystem

Suite Setup       Initialize Python Path

*** Variables ***
${PYTHON_EXE}     python
${EXCEL_SCRIPT}   ${CURDIR}/../../resources/DonorMotivationRpa.py

*** Keywords ***
Initialize Python Path
    ${py}=    Evaluate    sys.executable    modules=sys
    Set Suite Variable    ${PYTHON_EXE}    ${py}

*** Test Cases ***
Reset Excel Queue With Sample Data
    [Documentation]    Initializes or resets the Excel sheet with fresh test records (Pending, Null, and Completed).
    ${result}=    Run Process    ${PYTHON_EXE}    ${EXCEL_SCRIPT}    --reset-excel
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    ${result.rc}    0    msg=Failed to reset Excel queue: ${result.stderr}
    Should Contain    ${result.stdout}    Excel queue initialized

Process Pending And Null Donors From Excel Sheet
    [Documentation]    Runs RPA to process ONLY rows with Status 'Pending' or null, and updates them to 'Completed'.
    ${result}=    Run Process    ${PYTHON_EXE}    ${EXCEL_SCRIPT}    --excel    --simulate
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    ${result.rc}    0    msg=Excel RPA execution failed: ${result.stderr}
    
    # Verify that pending and null rows were detected and matched
    Should Contain    ${result.stdout}    Match Found -> Status is 'Pending'
    Should Contain    ${result.stdout}    Match Found -> Status is 'None'
    Should Contain    ${result.stdout}    Match Found -> Status is 'null'
    Should Contain    ${result.stdout}    Match Found -> Status is 'pending'
    
    # Verify that previously completed rows were skipped
    Should Contain    ${result.stdout}    SKIPPED -> Donor: Already Notified Donor
    
    # Verify that status was updated to Completed
    Should Contain    ${result.stdout}    STATUS UPDATED TO 'Completed'
    Should Contain    ${result.stdout}    Rows Processed & Completed: 4
    Should Contain    ${result.stdout}    Rows Skipped (Already Completed): 1

Verify Completed Donors Are Skipped On Re-Execution
    [Documentation]    Running the automation again should skip all rows because all are now marked 'Completed'.
    ${result}=    Run Process    ${PYTHON_EXE}    ${EXCEL_SCRIPT}    --excel    --simulate
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    ${result.rc}    0    msg=Excel re-execution failed: ${result.stderr}
    
    # Now 0 rows should be processed, and all 5 rows should be skipped
    Should Contain    ${result.stdout}    Rows Processed & Completed: 0
    Should Contain    ${result.stdout}    Rows Skipped (Already Completed): 5
