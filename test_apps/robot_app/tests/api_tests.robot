*** Settings ***
Library     RequestsLibrary
Library     Collections

Suite Setup     Create Session    api    http://httpbin.org

*** Variables ***
${BASE_URL}     http://httpbin.org

*** Test Cases ***
Verify HTTP GET Request Returns 200
    [Documentation]    Test that a GET request returns status 200
    ${response}=    GET On Session    api    /get
    Should Be Equal As Integers    ${response.status_code}    200

Verify Response Contains Headers
    [Documentation]    Test that the response contains expected headers
    ${response}=    GET On Session    api    /headers
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${body}    headers

Verify HTTP POST Request
    [Documentation]    Test that a POST request returns status 200
    ${data}=    Create Dictionary    name=DockerFactory    version=1.0
    ${response}=    POST On Session    api    /post    json=${data}
    Should Be Equal As Integers    ${response.status_code}    200
