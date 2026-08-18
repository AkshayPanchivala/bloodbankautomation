*** Settings ***
Documentation     RPA script to check blood stock and send an email alert if low.
Library           RequestsLibrary
Library           ../../resources/EmailEnvLoader.py

*** Variables ***
${BASE_URL}       http://localhost:5000
${THRESHOLD}      5
${ENV_FILE_PATH}  .env

*** Test Cases ***
Check Stock And Send Email Alert
    [Documentation]    Checks O- stock and triggers an email if below threshold.
    
    # Load Email Credentials from the backend .env file
    ${email_creds}=    Load Email Credentials From Env    ${ENV_FILE_PATH}
    Log    Loaded Email Username: ${email_creds['username']}
    
    ${current_stock}=  Set Variable      3  # Simulated low stock
    
    IF    ${current_stock} < ${THRESHOLD}
        Log    Stock is low! Sending Email Alert from ${email_creds['username']} to Admin...
        Send Smtp Email    ${ENV_FILE_PATH}    akshaypanchivala@gmail.com    URGENT: Low Blood Stock Alert (O-)    Warning! The stock for O- blood has dropped to ${current_stock} units. Please take action immediately.
        Log    Email successfully sent!
    ELSE
        Log    Stock is healthy.
    END
