*** Settings ***
Documentation     Reusable UI keywords for Robot Framework test suites.
Library           SeleniumLibrary

*** Variables ***
${FRONTEND_URL}   http://localhost:3000
${BROWSER}        Chrome

*** Keywords ***
Open Application To
    [Arguments]    ${route}
    ${status}=    Run Keyword And Return Status    Get Location
    IF    not ${status}
        Open Browser    ${FRONTEND_URL}${route}    ${BROWSER}
    ELSE
        Go To    ${FRONTEND_URL}${route}
    END
    Maximize Browser Window

Login As
    [Arguments]    ${role}    ${email}    ${password}
    Open Application To    /login/${role}
    Wait Until Element Is Visible    id=email    timeout=10s
    Input Text         id=email       ${email}
    Input Text         id=password    ${password}
    Click Button       xpath=//button[@type='submit']
    Wait Until Location Does Not Contain    /login/    timeout=5s
    Sleep              1s

Select MUI Dropdown
    [Arguments]    ${label}    ${value}
    ${dropdown_xpath}=    Set Variable    //label[text()='${label}']/..//div[@role='button']
    Wait Until Element Is Visible    xpath=${dropdown_xpath}    timeout=5s
    
    # Scroll to center to bypass sticky toolbars, then use Selenium click so React catches the event
    ${dropdown_elem}=    Get WebElement    xpath=${dropdown_xpath}
    Execute Javascript    arguments[0].scrollIntoView({block: 'center'});    ARGUMENTS    ${dropdown_elem}
    Sleep    0.5s
    Click Element    xpath=${dropdown_xpath}
    
    # Wait for the popover menu item to appear
    ${option_xpath}=    Set Variable    //li[@role='option' and text()='${value}']
    Wait Until Element Is Visible    xpath=${option_xpath}    timeout=5s
    Sleep    0.5s
    
    ${option_elem}=    Get WebElement    xpath=${option_xpath}
    Execute Javascript    arguments[0].scrollIntoView({block: 'center'});    ARGUMENTS    ${option_elem}
    Click Element    xpath=${option_xpath}
    Sleep    1s

Logout
    # Assuming there's a logout button somewhere in the nav. If not, this can just close the browser.
    # Click Element    xpath=//button[contains(text(), 'Logout')]
    Log    Logged out
