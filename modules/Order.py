import json
import requests

def BuySellOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, price, buy_sell, market_limit, functionName):
    '''
    Method          POST
    실전 Domain      https://openapi.koreainvestment.com:9443
    모의 Domain      https://openapivts.koreainvestment.com:29443
    URL             /uapi/domestic-futureoption/v1/trading/order
    Format          JSON
    Content-Type    application/json; charset=UTF-8    
    '''
    endpoint = '/uapi/domestic-futureoption/v1/trading/order'
    url = 'https://openapi.koreainvestment.com:9443' + endpoint
    # Header
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer {}'.format(token),
        'appkey': appkey,
        'appsecret': appsecret,
        'tr_id': 'TTTO1101U'
    }
    # Parameter
    body = {
        'ORD_PRCS_DVSN_CD': '02',  # 주문전송
        'CANO': CANO,  # 계좌번호(앞)
        'ACNT_PRDT_CD': ACNT_PRDT_CD,  # 계좌번호(뒤)
        'SLL_BUY_DVSN_CD': buy_sell,  # 매도: '01', 매수: '02'
        'SHTN_PDNO': ticker,  # 종목 Ticker
        'ORD_QTY': str(qty),  # 수량
        'UNIT_PRICE': str(price),  # 시장가 -> '0'
        'ORD_DVSN_CD': market_limit  # 지정가: '01', 시장가: '02', 조건부: '03'
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    result = response.json()
    if result['rt_cd'] == '0':
        return result['output']
    else:
        print('{}, {}'.format(functionName, result['msg1']))
# 시장가 매수
def BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty):
    return BuySellOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, '0', '02', '02', 'BuyMarket')
# 시장가 매도
def SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty):
    return BuySellOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, '0', '01', '02', 'SellMarket')
# 매수 STOP LOSS
def BuyStopLoss(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, price):
    return BuySellOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, price, '01', '03', 'BuyStopLoss')
# 매도 STOP LOSS
def SellStopLoss(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, price):
    return BuySellOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, price, '02', '03', 'SellStopLoss')
# 지정가 매수
def BuyLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, price):
    result =  BuySellOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, price, '02', '01', 'BuyLimit')
    buy_sell = result['TRAD_DVSN_NAME']
    name = result['ITEM_NAME']
    odno = result['ODNO']
    return buy_sell, name, odno
# 지정가 매도
def SellLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, price):
    result = BuySellOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty, price, '01', '01', 'SellLimit')
    buy_sell = result['TRAD_DVSN_NAME']
    name = result['ITEM_NAME']
    odno = result['ODNO']
    return buy_sell, name, odno

# 주문 정정취소
def ModifyOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, qty, price, modify_cancel, whole_part, market_limit, functionName):
    '''
    Method          POST
    실전 Domain      https://openapi.koreainvestment.com:9443
    모의 Domain      https://openapivts.koreainvestment.com:29443
    URL             /uapi/domestic-futureoption/v1/trading/order-rvsecncl
    Format          JSON
    Content-Type    application/json; charset=UTF-8
    '''
    endpoint = '/uapi/domestic-futureoption/v1/trading/order-rvsecncl'
    url = 'https://openapi.koreainvestment.com:9443' + endpoint
    # 가격 처리
    if price == 0:
        p = '0'
    else:
        p = str(round(price,2))
    # Header
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer {}'.format(token),
        'appkey': appkey,
        'appsecret': appsecret,
        'tr_id': 'TTTO1103U'
    }
    # Parameter
    body = {
        'ORD_PRCS_DVSN_CD': '02',  # 주문전송
        'CANO': CANO,  # 계좌번호(앞)
        'ACNT_PRDT_CD': ACNT_PRDT_CD,  # 계좌번호(뒤)
        'RVSE_CNCL_DVSN_CD': modify_cancel,  # 정정: '01', 취소: '02'
        'ORGN_ODNO': ODNO,  # 정정 혹은 취소할 주문 번호
        'ORD_QTY': str(qty),  # 전량(whole): '0'
        'UNIT_PRICE': p,  # 시장가, 취소 -> '0'
        'NMPR_TYPE_CD': market_limit,  # 지정가: '01', 시장가: '02'
        'KRX_NMPR_CNDT_CD': '0',  
        'RMN_QTY_YN': whole_part,  # 전량(whole): 'Y', 일부(part): 'N'
        'ORD_DVSN_CD': market_limit  # 지정가, 취소: '01', 시장가: '02'
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    result = response.json()
    if result['rt_cd'] == '0':
        return result['output']
    else:
        print('{}, {}'.format(functionName, result['msg1']))
# 주문 정정(시장가 전량)
def ModifyOrderMarketWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO):
    return ModifyOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, 0, 0, '01', 'Y', '02', 'ModifyOrderMarketWhole')
# 주문 정정(시장가 일부)
def ModifyOrderMarketPart(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, qty):
    return ModifyOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, qty, 0, '01', 'N', '02', 'ModifyOrderMarketPart')
# 주문 정정(지정가 전량)
def ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, price):
    result = ModifyOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, 0, price, '01', 'Y', '01', 'ModifyOrderLimitWhole')
    buy_sell = result['TRAD_DVSN_NAME']
    name = result['ITEM_NAME']
    odno = result['ODNO']
    return buy_sell, name, odno
# 주문 정정(지정가 일부)
def ModifyOrderLimitPart(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, qty, price):
    result = ModifyOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, qty, price, '01', 'Y', '01', 'ModifyOrderLimitPart')
    buy_sell = result['TRAD_DVSN_NAME']
    name = result['ITEM_NAME']
    odno = result['ODNO']
    return buy_sell, name, odno
# 주문 취소(전량)
def CancelOrderWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO):
    return ModifyOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, 0, 0, '02', 'Y', '01', 'CancelOrderWhole')
# 주문 취소(일부)
def CancelOrderPart(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, qty):
    return ModifyOrder(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ODNO, qty, 0, '02', 'N', '01', 'CancelOrderPart')

# 주문가능 조회
def GetOrderables(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, buy_sell):
    if buy_sell == '매수':
        bs = '02'
    if buy_sell == '매도':
        bs = '01'
    endpoint = '/uapi/domestic-futureoption/v1/trading/inquire-psbl-order'
    url = 'https://openapi.koreainvestment.com:9443' + endpoint
    # Header
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer {}'.format(token),
        'appkey': appkey,
        'appsecret': appsecret,
        'tr_id': 'TTTO5105R'
    }
    # Parameter
    params = {
        'CANO': CANO,  # 계좌번호(앞)
        'ACNT_PRDT_CD': ACNT_PRDT_CD,  # 계좌번호(뒤)
        'PDNO': ticker,
        'SLL_BUY_DVSN_CD': bs,
        'UNIT_PRICE': '0',
        'ORD_DVSN_CD': '02'
    }
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    if result['rt_cd'] == '0':
        return int(result['output']['lqd_psbl_qty1'])
    else:
        # print('{}, {}'.format(functionName, result['msg1']))
        print('{}'.format(result['msg1']))
        return 0



# 주문체결내역조회
def GetOrderList(appkey, appsecret, token, CANO, ACNT_PRDT_CD, date, buy_sell, conclusion, sort, ticker, functionName):
    endpoint = '/uapi/domestic-futureoption/v1/trading/inquire-ccnl'
    url = 'https://openapi.koreainvestment.com:9443' + endpoint
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
        'CANO': CANO,  # 계좌번호(앞)
        'ACNT_PRDT_CD': ACNT_PRDT_CD,  # 계좌번호(뒤)
        'STRT_ORD_DT': date,  # 시작 일자, YYYYMMDD
        'END_ORD_DT': date,  # 끝 일자, YYYYMMDD
        'SLL_BUY_DVSN_CD': buy_sell,  # 전체: '00', '매도': '01', '매수': '02',
        'CCLD_NCCS_DVSN': conclusion,  # 전체: '00', '체결': '01'. '미체결': '02'
        'SORT_SQN': sort,  # 빠른순서(처음주문이 맨 위): 'AS', 늦은순서(최근주문이 맨 위): 'DS'
        'STRT_ODNO': '',  # 조회 시작 주문번호
        'PDNO': ticker,
        'MKET_ID_CD': '',
        'CTX_AREA_FK200': '',
        'CTX_AREA_NK200': ''
    }
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    if result['rt_cd'] == '0':
        result2 = []
        for i in result['output1']:
            name = i['prdt_name']  # 이름
            pdno = i['pdno']  # 종목코드
            time = i['ord_tmd']  # 시간
            odno = i['odno']  # 주문번호
            orgn_odno = i['orgn_odno']  # 원주문번호
            buy_sell = i['trad_dvsn_name']
            market_limit = i['nmpr_type_name']  # 시장가/지정가
            price = round(float(i['ord_idx']), 2)  # 가격
            qty = int(i['ord_qty'])  # 수량
            result2.append((name, pdno, time, odno, orgn_odno, buy_sell, market_limit, price, qty))
        return result2
    else:
        print('{}, {}'.format(functionName, result['msg1']))
# 전체 조회(최근주문이 맨 위)
def GetOrderListAll(appkey, appsecret, token, CANO, ACNT_PRDT_CD, date, ticker):
    return GetOrderList(appkey, appsecret, token, CANO, ACNT_PRDT_CD, date, '00', '00', 'DS', ticker, 'GetOrderListAll')
# 체결된 주문 전체 조회(최근주문이 맨 위)
def GetCCOrderListAll(appkey, appsecret, token, CANO, ACNT_PRDT_CD, date, ticker):
    return GetOrderList(appkey, appsecret, token, CANO, ACNT_PRDT_CD, date, '00', '01', 'DS', ticker, 'GetCCOrderListAll')
# 미체결된 주문 전체 조회(최근주문이 맨 위)
def GetNCCOrderListAll(appkey, appsecret, token, CANO, ACNT_PRDT_CD, date, ticker):
    return GetOrderList(appkey, appsecret, token, CANO, ACNT_PRDT_CD, date, '00', '02', 'DS', ticker, 'GetNCCOrderListAll')
# 체결된 주문 중 지정가 주문(최근주문이 맨 위)


# 주문체결내역조회
def GetContractList(appkey, appsecret, token, CANO, ACNT_PRDT_CD):
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
        'CANO': CANO,  # 계좌번호(앞)
        'ACNT_PRDT_CD': ACNT_PRDT_CD,  # 계좌번호(뒤)
        'MGNA_DVSN': '02',  # 유지증거금
        'EXCC_STAT_CD': '2',  # 매입가격으로 잔고 조회
        'CTX_AREA_FK200': '',
        'CTX_AREA_NK200': ''
    }
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    if result['rt_cd'] == '0':
        result2 = []
        for i in result['output1']:
            # 이름
            name = i['prdt_name']
            # 포지션
            position = i['sll_buy_dvsn_name']
            # 가격
            price = round(float(i['ccld_avg_unpr1']), 2)
            # 수량
            qty = int(i['cblc_qty'])
            result2.append((name, position, price, qty))
        return result2
    else:
        print('{}, {}'.format('GetContractList', result['msg1']))
