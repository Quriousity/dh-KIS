import requests
import pandas as pd

from time import sleep
from datetime import datetime, timedelta

# start ~ end 날짜세기
def CountDate(start, end):
    t1 = datetime.strptime(start, '%Y%m%d')
    t2 = datetime.strptime(end, '%Y%m%d')
    return (t2-t1).days
# 평일만 모으기 (YYYYmmdd)
def CollectOnlyWeekdays(start, end):
    result = []
    date = datetime.strptime(start, '%Y%m%d')
    if date.weekday() < 5:
        result.append(date.strftime('%Y%m%d'))
    for _ in range(CountDate(start, end)):
        date += timedelta(days=1)
        if date.weekday() < 5:
            result.append(date.strftime('%Y%m%d'))
    return result
# 거래일 조회
def GetTradingDays(appkey, appsecret, token, date):
    '''
    Method         GET
    실전 Domain     https://openapi.koreainvestment.com:9443
    모의 Domain     
    URL            /uapi/domestic-stock/v1/quotations/chk-holiday
    Format 
    Content-Type 
    '''
    endpoint = '/uapi/domestic-stock/v1/quotations/chk-holiday'
    url = 'https://openapi.koreainvestment.com:9443' + endpoint
    # Header
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer {}'.format(token),
        'appkey': appkey,
        'appsecret': appsecret,
        'tr_id': 'CTCA0903R',
        'custtype': 'P'
    }
    # Parameter
    params = {
        'BASS_DT': date,
        'CTX_AREA_NK': '',
        'CTX_AREA_FK': ''
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['rt_cd'] == '0':
            for i in result['output']:
                if i['bass_dt'] == date:
                    if i['opnd_yn'] == 'Y':
                        return True
                    if i['opnd_yn'] == 'N':
                        return False
        else:
            print('GetTradingDays, {}'.format(result['msg1']))
    else:
        print('error (GetTradingDays)')

# KOSPI200 선물 당일 분봉 조회, JSON
def GetKOSPI200_m(appkey, appsecret, token, interval, date):
    '''
    Method         GET
    실전 Domain     https://openapi.koreainvestment.com:9443
    모의 Domain     
    URL            /uapi/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice
    Format 
    Content-Type 
    '''
    endpoint = '/uapi/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice'
    url = 'https://openapi.koreainvestment.com:9443' + endpoint
    # Header
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer {}'.format(token),
        'appkey': appkey,
        'appsecret': appsecret,
        'tr_id': 'FHKIF03020200',
        'custtype': 'P'
    }
    # Parameter
    params = {
        'FID_COND_MRKT_DIV_CODE': 'F',
        'FID_INPUT_ISCD': '101000',
        'FID_HOUR_CLS_CODE': str(interval),
        'FID_PW_DATA_INCU_YN': 'N',
        'FID_FAKE_TICK_INCU_YN': 'N',
        # YYYYMMDD
        'FID_INPUT_DATE_1': date,
        # HHMMSS
        'FID_INPUT_HOUR_1': '170000'
    }
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    if result['rt_cd'] == '0':
        return result['output2']
    if result['rt_cd'] == '1':
        print('GetKOSPI200_m, {}'.format(result['msg1']))

# KOSPI200 선물 당일 분봉 조회, pd.DataFrame
def GetKOSPI200(appkey, appsecret, token, interval, date):
    a = GetKOSPI200_m(appkey, appsecret, token, str(interval), date)
    endtime = []
    raw = {
        'open' : [],
        'high': [],
        'low': [],
        'close': [],
        'volume': []       
    }
    while type(a) == type(None):
        sleep(0.1)
        a = GetKOSPI200_m(appkey, appsecret, token, str(interval), date)        
    for i in a:
        t = '{}-{}-{} {}:{}:{}'.format(i['stck_bsop_date'][:4], i['stck_bsop_date'][4:6], i['stck_bsop_date'][6:], i['stck_cntg_hour'][:2], i['stck_cntg_hour'][2:4], i['stck_cntg_hour'][4:])
        endtime.append(t)  
        raw['open'].append(float(i['futs_oprc']))
        raw['high'].append(float(i['futs_hgpr']))
        raw['low'].append(float(i['futs_lwpr']))
        raw['close'].append(float(i['futs_prpr']))
        raw['volume'].append(float(i['cntg_vol']))

    endtime = endtime[::-1]
    raw['open'] = raw['open'][::-1]
    raw['high'] = raw['high'][::-1]
    raw['low'] = raw['low'][::-1]
    raw['close'] = raw['close'][::-1]
    raw['volume'] = raw['volume'][::-1]

    df = pd.DataFrame(raw, index=endtime)
    return df
# 5일선, 10일선, 20일선
def CalculateMA(df):
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    return df
# MACD
def CalculateMACD(df):
    length_fast = 12
    length_slow = 26
    length_signal = 9

    ma_fast = df['close'].rolling(length_fast).mean()
    ma_slow = df['close'].rolling(length_slow).mean()
    macd = ma_fast - ma_slow
    signal = macd.rolling(length_signal).mean()
    df['macd'] = macd - signal 
    return df
# 5분봉
def Get5(appkey, appsecret, token, date):
    t = datetime.strptime(date, '%Y%m%d')
    # 당일
    df1 = GetKOSPI200(appkey, appsecret, token, 300, date)
    sleep(0.1)
    # 전일
    t = datetime.strptime(df1.index[0][:10], '%Y-%m-%d')
    t -= timedelta(days=1)
    date_y = t.strftime('%Y%m%d')
    while GetTradingDays(appkey, appsecret, token, date_y) == False:
        sleep(0.1)
        t -= timedelta(days=1)
        date_y = t.strftime('%Y%m%d')
        print(date_y)
    df2 = GetKOSPI200(appkey, appsecret, token, 300, date_y)
    sleep(0.1)
    df = pd.concat([df2, df1])
    df = CalculateMA(df)
    df = CalculateMACD(df)
    return df1, df
# 10분봉
def Get10(appkey, appsecret, token, date):
    t = datetime.strptime(date, '%Y%m%d')
    # 당일
    df1 = GetKOSPI200(appkey, appsecret, token, 600, date)
    sleep(0.1)
    # 전일
    t = datetime.strptime(df1.index[0][:10], '%Y-%m-%d')
    t -= timedelta(days=1)
    date_y = t.strftime('%Y%m%d')
    while GetTradingDays(appkey, appsecret, token, date_y) == False:
        sleep(0.1)
        t -= timedelta(days=1)
        date_y = t.strftime('%Y%m%d')
    df2 = GetKOSPI200(appkey, appsecret, token, 600, date_y)
    sleep(0.1)
    df = pd.concat([df2, df1])
    df = CalculateMA(df)
    df = CalculateMACD(df)
    return df1, df
# 30분봉
def Get30(appkey, appsecret, token, date):
    t = datetime.strptime(date, '%Y%m%d')
    # 당일
    df1 = GetKOSPI200(appkey, appsecret, token, 1800, date)
    sleep(0.1)
    # 전일
    t = datetime.strptime(df1.index[0][:10], '%Y-%m-%d')
    t -= timedelta(days=1)
    date_y = t.strftime('%Y%m%d')
    while GetTradingDays(appkey, appsecret, token, date_y) == False:
        sleep(0.1)
        t -= timedelta(days=1)
        date_y = t.strftime('%Y%m%d')
    df2 = GetKOSPI200(appkey, appsecret, token, 1800, date_y)
    sleep(0.1)
    # 전전일
    t = datetime.strptime(df2.index[0][:10], '%Y-%m-%d')
    t -= timedelta(days=1)
    date_y = t.strftime('%Y%m%d')
    while GetTradingDays(appkey, appsecret, token, date_y) == False:
        sleep(0.1)
        t -= timedelta(days=1)
        date_y = t.strftime('%Y%m%d')
    df3 = GetKOSPI200(appkey, appsecret, token, 1800, date_y)
    sleep(0.1)
    df = pd.concat([df3, df2, df1])
    df = CalculateMA(df)
    df = CalculateMACD(df)
    return df1, df

def Get5_10_15_1(appkey, appsecret, token, date): 
    t = datetime.strptime(date, '%Y%m%d')
    # 당일
    df1_5 = GetKOSPI200(appkey, appsecret, token, 300, date)
    sleep(0.1)
    df1_10 = GetKOSPI200(appkey, appsecret, token, 600, date)
    sleep(0.1)
    df1_30 = GetKOSPI200(appkey, appsecret, token, 1800, date)
    sleep(0.1)
    # 전일
    t = datetime.strptime(df1_30.index[0][:10], '%Y-%m-%d')
    t -= timedelta(days=1)
    date_y = t.strftime('%Y%m%d')
    while GetTradingDays(appkey, appsecret, token, date_y) == False:
        sleep(0.1)
        t -= timedelta(days=1)
        date_y = t.strftime('%Y%m%d')
    df2_5 = GetKOSPI200(appkey, appsecret, token, 300, date_y)
    sleep(0.1)
    df2_10 = GetKOSPI200(appkey, appsecret, token, 600, date_y)
    sleep(0.1)
    df2_30 = GetKOSPI200(appkey, appsecret, token, 1800, date_y)
    sleep(0.1)
    # 전전일
    t = datetime.strptime(df2_30.index[0][:10], '%Y-%m-%d')
    t -= timedelta(days=1)
    date_y = t.strftime('%Y%m%d')
    while GetTradingDays(appkey, appsecret, token, date_y) == False:
        sleep(0.1)
        t -= timedelta(days=1)
        date_y = t.strftime('%Y%m%d')
    df3_30 = GetKOSPI200(appkey, appsecret, token, 1800, date_y)
    sleep(0.1)
    df_5 = pd.concat([df2_5, df1_5])
    df_5 = CalculateMA(df_5)
    df_5 = CalculateMACD(df_5)
    df_10 = pd.concat([df2_10, df1_10])
    df_10 = CalculateMA(df_10)
    df_10 = CalculateMACD(df_10)
    df_30 = pd.concat([df3_30, df2_30, df1_30])
    df_30 = CalculateMA(df_30)
    df_30 = CalculateMACD(df_30)
    return df_5, df_10, df_30


def GetToday_m(appkey, appsecret, token, interval, date):
    # 당일
    df1 = GetKOSPI200(appkey, appsecret, token, interval, date)
    return df1

def GetToday(appkey, appsecret, token, date):
    '''
    Method         GET
    실전 Domain     https://openapi.koreainvestment.com:9443
    모의 Domain     https://openapivts.koreainvestment.com:29443
    URL            /uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice
    Format 
    Content-Type 
    '''
    endpoint = '/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice'
    url = 'https://openapi.koreainvestment.com:9443' + endpoint
    # Header
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer {}'.format(token),
        'appkey': appkey,
        'appsecret': appsecret,
        'tr_id': 'FHKIF03020100'
    }
    # Parameter
    params = {
        'FID_COND_MRKT_DIV_CODE': 'F',
        'FID_INPUT_ISCD': '101000',
        'FID_INPUT_DATE_1': date,
        'FID_INPUT_DATE_2': date,
        'FID_PERIOD_DIV_CODE': 'D'
    }
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    if result['rt_cd'] == '0':
        endtime = []
        raw = {
            'open' : [],
            'high': [],
            'low': [],
            'close': []
        }
        for i in result['output2']:
            t = '{}-{}-{}'.format(i['stck_bsop_date'][:4], i['stck_bsop_date'][4:6], i['stck_bsop_date'][6:])
            endtime.append(t)  
            raw['open'].append(float(i['futs_oprc']))
            raw['high'].append(float(i['futs_hgpr']))
            raw['low'].append(float(i['futs_lwpr']))
            raw['close'].append(float(i['futs_prpr']))

        endtime = endtime[::-1]
        raw['open'] = raw['open'][::-1]
        raw['high'] = raw['high'][::-1]
        raw['low'] = raw['low'][::-1]
        raw['close'] = raw['close'][::-1]

        df = pd.DataFrame(raw, index=endtime)
        return df

    else:
        print('GetToday, {}'.format(result['msg1']))

def GetToday_m_forClose(appkey, appsecret, token, interval, date):
    t = datetime.strptime(date, '%Y%m%d')
    # 당일
    df1 = GetKOSPI200(appkey, appsecret, token, interval, date)
    sleep(0.1)
    # 전일
    t = datetime.strptime(df1.index[0][:10], '%Y-%m-%d')
    t -= timedelta(days=1)
    date_y = t.strftime('%Y%m%d')
    while GetTradingDays(appkey, appsecret, token, date_y) == False:
        sleep(0.1)
        t -= timedelta(days=1)
        date_y = t.strftime('%Y%m%d')
    df2 = GetKOSPI200(appkey, appsecret, token, interval, date_y)
    sleep(0.1)
    df = pd.concat([df2, df1])
    df = CalculateMA(df)
    return df1, df
