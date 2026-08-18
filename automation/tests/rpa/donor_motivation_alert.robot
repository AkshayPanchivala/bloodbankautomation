*** Settings ***
Documentation     RPA script to check for old donations and send motivation emails.
Library           Process

*** Variables ***
${PYTHON_CMD}     python

*** Test Cases ***
Check Old Donations And Send Motivation Email
    [Documentation]    Runs the Python RPA script to find donations > 90 days old and send emails.
    
    # Run the python script directly using the virtual environment python
    ${result}=    Run Process    venv\\Scripts\\python.exe    resources\\DonorMotivationRpa.py    shell=True
    
    # Log the output for debugging
    Log    ${result.stdout}
    Log    ${result.stderr}
    
    # Verify the script executed successfully
    Should Be Equal As Integers    ${result.rc}    0    msg=RPA Script failed with exit code ${result.rc}
    
    # Verify that it found at least one eligible donor (we seeded Aditya!)
    Should Contain    ${result.stdout}    Total motivation emails sent: 
    
    # Specifically verify Aditya was found
    Should Contain    ${result.stdout}    Found eligible donor: adityamodi.imca22@gmail.com
