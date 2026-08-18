*** Settings ***
Documentation     Suite setup for all UI tests to reuse a single browser window.
Library           SeleniumLibrary

Suite Setup       Open Browser    http://localhost:3000    Chrome
Suite Teardown    Close All Browsers
