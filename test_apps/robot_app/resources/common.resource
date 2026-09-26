*** Settings ***
Library     RequestsLibrary

*** Keywords ***
Create API Session
    [Arguments]    ${base_url}
    Create Session    api    ${base_url}
    Log    API session created for ${base_url}
