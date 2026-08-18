*** Settings ***
Documentation     API test to verify the backend endpoints are functioning.
Library           RequestsLibrary

*** Variables ***
${BASE_URL}       http://localhost:5000

*** Test Cases ***
Verify Backend Bloodbank Route Is Running
    [Documentation]    Checks if the backend API bloodbank route is up and running.
    Create Session     backend    ${BASE_URL}
    ${response}=       GET On Session    backend    /api/bloodbank/getbloodbanks
    Status Should Be   200    ${response}
