import json
import requests

def GetToken(appkey, appsecret):
    '''
    Method          POST
    실전 Domain      https://openapi.koreainvestment.com:9443
    모의 Domain      https://openapivts.koreainvestment.com:29443
    URL             /oauth2/tokenP
    Format          JSON
    Content-Type    application/json; charset=UTF-8

    - 접근토큰(access_token)의 유효기간은 24시간 이며(1일 1회발급 원칙) 갱신발급주기는 6시간 입니다.(6시간 이내는 기존 발급키로 응답)
    - 접근토큰발급(/oauth2/tokenP) 시 접근토큰값(access_token)과 함께 수신되는 접근토큰 유효기간(acess_token_token_expired)을 이용해 접근토큰을 관리하실 수 있습니다.
    - '23.4.28 이후 지나치게 잦은 토큰 발급 요청건을 제어 하기 위해 신규 접근토큰발급 이후 일정시간 이내에 재호출 시에는 직전 토큰값을 리턴하게 되었습니다. 
    일정시간 이후 접근토큰발급 API 호출 시에는 신규 토큰값을 리턴합니다. 접근토큰발급 API 호출 및 코드 작성하실 때 해당 사항을 참고하시길 바랍니다.

    [Output] position, price, quantity
    '''
    endpoint = '/oauth2/tokenP'
    url = 'https://openapi.koreainvestment.com:9443' + endpoint
    body = {
            'grant_type': 'client_credentials',
            'appkey': appkey,
            'appsecret': appsecret
    }
    response = requests.post(url, data=json.dumps(body))
    if response.status_code == 200:
        result = response.json()
        return result['access_token']
    else:
        print('error (GetToken)')