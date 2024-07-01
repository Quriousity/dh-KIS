import requests

# 잔고 조회
def GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD):
    '''
    Method          GET
    실전 Domain      https://openapi.koreainvestment.com:9443
    모의 Domain      https://openapivts.koreainvestment.com:29443
    URL             /uapi/domestic-futureoption/v1/trading/inquire-balance
    Format 
    Content-Type 

    개요
    - 선물옵션 잔고현황 API입니다. 한 번의 호출에 최대 100건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다.

    [Output] position, price, quantity
    '''
    endpoint = '/uapi/domestic-futureoption/v1/trading/inquire-balance'
    url = 'https://openapi.koreainvestment.com:9443' + endpoint
    # Header
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer {}'.format(token),
        'appkey': appkey,
        'appsecret': appsecret,
        'tr_id': 'CTFO6118R'
    }
    # Parameter
    params = {
        'CANO': CANO,
        'ACNT_PRDT_CD': ACNT_PRDT_CD,
        # 유지 증거금
        'MGNA_DVSN': '02',
        # 정산상태코트 (매입가격으로 잔고 조회)
        'EXCC_STAT_CD': '2',
        'CTX_AREA_FK200': '',
        'CTX_AREA_NK200': ''
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()['output1']
        if len(result) > 0:
            # 포지션
            position = result[0]['sll_buy_dvsn_name']
            if position == "SLL":
                position = "매도"
            elif position == "BUY":
                position = "매수"
            # 가격
            price = round(float(result[0]['ccld_avg_unpr1']), 2)
            # 수량
            qty = round(int(result[0]['cblc_qty']))
            return position, price, qty
        return 0, 0, 0
    else:
        print('error (GetBalance)')

# 당일 미체결주문체결내역 조회
def GetOrders(appkey, appsecret, token, CANO, ACNT_PRDT_CD, date):
    endpoint = '/uapi/domestic-futureoption/v1/trading/inquire-balance'
    url = 'https://openapivts.koreainvestment.com:29443' + endpoint
    # Header
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer {}'.format(token),
        'appkey': appkey,
        'appsecret': appsecret,
        'tr_id': 'VTTO5201R'
    }
    # Parameter
    params = {
        'CANO': CANO,
        'ACNT_PRDT_CD': ACNT_PRDT_CD,
        'STRT_ORD_DT': date,
        'END_ORD_DT': date,
        'SLL_BUY_DVSN_CD': '00',  # 매수/매도 전체
        'CCLD_NCCS_DVSN': '02',  # 미체결 전체
        'SORT_SQN': 'DS',  # 역순
        'STRT_ODNO': '',
        'PDNO': '',
        'MKET_ID_CD': '',
        'CTX_AREA_FK200': '',
        'CTX_AREA_NK200': ''
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()['output1']
        result2 = []
        for i in result:
            odno = i['orgn_odno']
            buysell = i['sll_buy_dvsn_cd']  # 01: 매도, 02:매수
            if buysell == '01':
                buysell = '매도'
            elif buysell == '02':
                buysell = '매수'
            qty = i['qty']
            price = i['ord_idx']
            result2.append((odno, buysell, qty, price))
        return result2
    else:
        print('error (GetOrders)')