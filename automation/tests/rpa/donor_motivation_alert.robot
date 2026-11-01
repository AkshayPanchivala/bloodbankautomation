*** Settings ***
Documentation     RPA script to check eligible donations from Excel queue or DB and send motivation emails.
Library           Process

*** Variables ***
${PYTHON_CMD}     python
${RPA_SCRIPT}     ${CURDIR}/../../resources/DonorMotivationRpa.py

*** Test Cases ***
Process Donor Motivation From Excel Queue
    [Documentation]    Runs the Python RPA script to process eligible donors from the Excel sheet (Pending/Null -> Completed).
    
    # Run the Python script using the configured python executable
    ${result}=    Run Process    ${PYTHON_CMD}    ${RPA_SCRIPT}    --excel    --simulate    shell=True
    
    # Log the output for debugging
    Log    ${result.stdout}
    Log    ${result.stderr}
    
    # Verify the script executed successfully
    Should Be Equal As Integers    ${result.rc}    0    msg=RPA Script failed with exit code ${result.rc}
    
    # Verify that it processed pending/null records and updated status
    Should Contain    ${result.stdout}    EXCEL AUTOMATION SUMMARY:
