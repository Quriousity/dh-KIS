import json
import pickle
import requests
import schedule
import pandas as pd

from os import path
from time import sleep
from datetime import datetime, timedelta

from modules.Account import GetBalance
from modules.GetAuth import GetToken
from modules.Market import GetTradingDays, Get5, Get10, Get30, GetKOSPI200
from modules.Message import SendMessage
from modules.Order import BuyMarket, SellMarket, BuyLimit, SellLimit, ModifyOrderLimitWhole, CancelOrderWhole

# Configuration 불러오기
with open('conf.json') as f:
    config = json.load(f)
appkey = config["appkey"]
appsecret = config["appsecret"]
CANO = config["CANO"]
ACNT_PRDT_CD = config["ACNT_PRDT_CD"]
qty = config["qty"]
ticker = config["ticker"]
discord = [config['discord1'], config['discord2']]
reset = config["reset"]

# Token 발급받기
token = GetToken(appkey, appsecret); sleep(0.1)
if token != "":
    print('토큰 발급 성공')

# 오늘 날짜
date = datetime.now()
date = datetime.strftime(date, '%Y%m%d')

print('프로그램 시작!', datetime.now())
print('==========================================================')

# Log
log = 'Trade Log'
if path.exists('./Log.txt') == False:
    with open('Log.txt', 'w') as fw:
        fw.write(log)

# 진입 스위치
switch1 = True
# 청산 스위치
switch2 = False
# 스탑 스위치
switch3 = False
# 지정가청산 주문번호
odno = ''
# 롱 포지션
switchLong = 0
# 숏 포지션
switchShort = 0
# 포지션 정보 가져오기
position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)

# 경로 확인 후 있으면 가져오고 없으면 현재값으로 만드는 함수:
def CheckParameter(parameter, parameterName):
    if path.exists('./{}.pickle'.format(parameterName)):
        with open('{}.pickle'.format(parameterName), 'rb') as fr:
            parameter = pickle.load(fr)
    else:
        with open('{}.pickle'.format(parameterName), 'wb') as fw:
            pickle.dump(parameter, fw)
CheckParameter(switch1, 'switch1')
CheckParameter(switch2, 'switch2')
CheckParameter(switch3, 'switch3')
CheckParameter(odno, 'odno')
CheckParameter(switchLong, 'switchLong')
CheckParameter(switchShort, 'switchShort')

# 파라미터 변경되면 기록하는 함수
def UpdateParameter(parameter, parameterName):
    with open('{}.pickle'.format(parameterName), 'wb') as fw:
        pickle.dump(parameter, fw)

def ResetToday():
    # 개장일이면
    if GetTradingDays(appkey, appsecret, token, date):
        # Token 발급받기
        token = GetToken(appkey, appsecret); sleep(0.1)
        if token != "":
            print('토큰 발급 성공')

        # 오늘 날짜
        date = datetime.now()
        date = datetime.strftime(date, '%Y%m%d')

        log = '{} {}'.format(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), '프로그램 시작!'); print(log)
        print('==========================================================')
        with open('Log.txt', 'a') as fa:
            fa.write('\n'); fa.write(log)

        # 진입 스위치
        switch1 = True
        # 청산 스위치
        switch2 = False
        # 스탑 스위치
        switch3 = False
        # 지정가청산 주문번호
        odno = ''
        # 롱 포지션
        switchLong = 0
        # 숏 포지션
        switchShort = 0
        # 포지션 정보 가져오기
        position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
        CheckParameter(switch1, 'switch1')
        CheckParameter(switch2, 'switch2')
        CheckParameter(switch3, 'switch3')
        CheckParameter(odno, 'odno')
        CheckParameter(switchLong, 'switchLong')
        CheckParameter(switchShort, 'switchShort')
    # 휴장일이면
    else:
        # 진입, 청산, 스탑 스위치
        switch1, switch2, switch3 = False

# 직전 상승봉 고가 돌파
def GetBeforeHigh(candle):
    candle['body'] = candle['close'] - candle['open']
    body = candle['close'].iloc[-1] - candle['open'].iloc[-1]
    if body > 0:
        n = 0
        for b, h in zip(candle['body'].iloc[:-1][::-1], candle['high'].iloc[:-1][::-1]):
            if b > 0 and candle['high'].iloc[-1] > h:
                if n == 0:
                    return True
                n += 1
    return False
# 직전 하락봉 저가 돌파
def GetBeforeLow(candle):
    candle['body'] = candle['close'] - candle['open']
    body = candle['close'].iloc[-1] - candle['open'].iloc[-1]
    if body < 0:
        n = 0
        for b, l in zip(candle['body'].iloc[:-1][::-1], candle['low'].iloc[:-1][::-1]):
            if b < 0 and candle['low'].iloc[-1] < l:
                if n == 0:
                    return True
                n += 1
    return False
# 9시 14분 이후
def After914():
    t = datetime.now()
    if t.hour > 9:
        return True
    elif t.hour == 9 and t.minute > 13:
        return True
    return False
# 9시 44분 이후
def After944():
    t = datetime.now()
    if t.hour > 9:
        return True
    elif t.hour == 9 and t.minute > 43:
        return True
    return False


def OpenPosition():
    global switch1, switch2, switch3, switchLong, switchShort, appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, discord
    '''
    보조지표 캔들
        indicator5, indicator10, indicator30
    당일 캔들
        candle5, candle10, candle30
    현재봉 (종가 - 시가)
        body5, body10, body30
    직전봉 (종가 - 시가)
        body5_, body10_, body30_
    최초봉 (종가 - 시가)
        first5, first10, first30
    '''
    candle5, indicator5 = Get5(appkey, appsecret, token, date)  # 5분봉
    candle10, indicator10 = Get10(appkey, appsecret, token, date)  # 10분봉
    candle30, indicator30 = Get30(appkey, appsecret, token, date)  # 30분봉
    # 현재봉
    body5 = indicator5['close'].iloc[-1] - indicator5['open'].iloc[-1]
    body10 = indicator10['close'].iloc[-1] - indicator10['open'].iloc[-1]
    body30 = indicator30['close'].iloc[-1] - indicator30['open'].iloc[-1]
    # 직전봉
    body5_ = indicator5['close'].iloc[-2] - indicator5['open'].iloc[-2]
    body10_ = indicator10['close'].iloc[-2] - indicator10['open'].iloc[-2]
    body30_ = indicator30['close'].iloc[-2] - indicator30['open'].iloc[-2]
    # 최초봉
    first5 = indicator5['close'].iloc[1] - indicator5['open'].iloc[1]
    first10 = indicator10['close'].iloc[1] - indicator10['open'].iloc[1]
    first30 = indicator30['close'].iloc[1] - indicator30['open'].iloc[1]

    if switch1:
        # [전략1]30분봉, 롱
        if After944():
            if abs(body30_) < abs(body30):
                if first30 > 0 and body30_ < 0 and body30 > 0:
                    if candle30['low'].iloc[-1] < candle30['open'].iloc[1] and candle30['open'].iloc[1] < candle30['close'].iloc[-1] and candle30['close'].iloc[-1] < candle30['open'].iloc[1] + 0.5:
                        if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                            if GetBeforeHigh(candle30):
                                switch1 = False; switch2 = True; switch3 = True; switchLong = 30
                                UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchLong, 'switchLong');
                                # 시장가 매수
                                BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                # 포지션 정보 가져오기
                                position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                # 지정가 매도
                                buy_sell, name, odno = SellLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price+2); sleep(0.1)
                                # 알림
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "매수(전략1 30분봉)"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)

        # [전략1]10분봉, 롱
        if After914():
            if abs(body10_) < abs(body10):
                if first10 > 0 and body10_ < 0 and body10 > 0:
                    if candle10['low'].iloc[-1] < candle10['open'].iloc[1] and candle10['open'].iloc[1] < candle10['close'].iloc[-1] and candle10['close'].iloc[-1] < candle10['open'].iloc[1] + 0.5:
                        if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                            if GetBeforeHigh(candle10):
                                switch1 = False; switch2 = True; switch3 = True; switchLong = 10
                                UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchLong, 'switchLong');
                                # 시장가 매수
                                BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                # 포지션 정보 가져오기
                                position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                # 지정가 매도
                                buy_sell, name, odno = SellLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price+2); sleep(0.1)
                                # 알림
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "매수(전략1 10분봉)"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)

        # [전략1]5분봉, 롱
        if After914():
            if abs(body5_) < abs(body5):
                if first5 > 0 and body5_ < 0 and body5 > 0:
                    if candle5['low'].iloc[-1] < candle5['open'].iloc[1] and candle5['open'].iloc[1] < candle5['close'].iloc[-1] and candle5['close'].iloc[-1] < candle5['open'].iloc[1] + 0.5:
                        if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                            if GetBeforeHigh(candle5):
                                switch1 = False; switch2 = True; switch3 = True; switchLong = 5
                                UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchLong, 'switchLong');
                                # 시장가 매수
                                BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                # 포지션 정보 가져오기
                                position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                # 지정가 매도
                                buy_sell, name, odno = SellLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price+2); sleep(0.1)
                                # 알림
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "매수(전략1 5분봉)"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)
        # [전략1]30분봉, 숏
        if After944():
            if abs(body30_) < abs(body30):
                if first30 < 0 and body30_ > 0 and body30 < 0:
                    if candle30['high'].iloc[-1] > candle30['open'].iloc[1] and candle30['open'].iloc[1] > candle30['close'].iloc[-1] and candle30['close'].iloc[-1] > candle30['open'].iloc[1] - 0.5:
                        if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                            if GetBeforeLow(candle30):
                                switch1 = False; switch2 = True; switch3 = True; switchShort = 30
                                UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchShort, 'switchShort');
                                # 시장가 매도
                                SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                # 포지션 정보 가져오기
                                position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                # 지정가 매수
                                buy_sell, name, odno = BuyLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price-2); sleep(0.1)
                                # 알림
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "매도(전략1 30분봉)"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)
        # [전략1]10분봉, 숏
        if After914():
            if abs(body10_) < abs(body10):
                if first10 < 0 and body10_ > 0 and body10 < 0:
                    if candle10['high'].iloc[-1] > candle10['open'].iloc[1] and candle10['open'].iloc[1] > candle10['close'].iloc[-1] and candle10['close'].iloc[-1] > candle10['open'].iloc[1] - 0.5:
                        if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                            if GetBeforeLow(candle10):
                                switch1 = False; switch2 = True; switch3 = True; switchShort = 10
                                UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchShort, 'switchShort');
                                # 시장가 매도
                                SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                # 포지션 정보 가져오기
                                position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                # 지정가 매수
                                buy_sell, name, odno = BuyLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price-2); sleep(0.1)
                                # 알림
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "매도(전략1 10분봉)"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)
        # [전략1]5분봉, 숏
        if After914():
            if abs(body5_) < abs(body5):
                if first5 < 0 and body5_ > 0 and body5 < 0:
                    if candle5['high'].iloc[-1] > candle5['open'].iloc[1] and candle5['open'].iloc[1] > candle5['close'].iloc[-1] and candle5['close'].iloc[-1] > candle5['open'].iloc[1] - 0.5:
                        if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                            if GetBeforeLow(candle5):
                                switch1 = False; switch2 = True; switch3 = True; switchShort = 5
                                UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchShort, 'switchShort');
                                # 시장가 매도
                                SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                # 포지션 정보 가져오기
                                position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                # 지정가 매수
                                buy_sell, name, odno = BuyLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price-2); sleep(0.1)
                                # 알림
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "매도(전략1 5분봉)"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)

        # [전략2]30분봉, 롱
        if After944():
            if abs(body30) < 1 and first30 > 0:
                if candle30['low'].iloc[-1] < candle30['open'].iloc[1] and candle30['open'].iloc[1] < candle30['close'].iloc[-1] and candle30['close'].iloc[-1] < candle30['open'].iloc[1] + 0.5:
                    if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                        if GetBeforeHigh(candle30):
                            switch1 = False; switch2 = True; switch3 = True; switchLong = 30
                            UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchLong, 'switchLong');
                            # 시장가 매수
                            BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                            # 포지션 정보 가져오기
                            position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                            # 지정가 매도
                            buy_sell, name, odno = SellLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price+2); sleep(0.1)
                            # 알림
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "매수(전략2 30분봉)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
        # [전략2]10분봉, 롱
        if After914():
            if abs(body10) < 1 and first30 > 0:
                if candle10['low'].iloc[-1] < candle10['open'].iloc[1] and candle10['open'].iloc[1] < candle10['close'].iloc[-1] and candle10['close'].iloc[-1] < candle10['open'].iloc[1] + 0.5:
                    if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                        if GetBeforeHigh(candle10):
                            switch1 = False; switch2 = True; switch3 = True; switchLong = 10
                            UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchLong, 'switchLong');
                            # 시장가 매수
                            BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                            # 포지션 정보 가져오기
                            position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                            # 지정가 매도
                            buy_sell, name, odno = SellLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price+2); sleep(0.1)
                            # 알림
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "매수(전략2 10분봉)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)

        # [전략2]30분봉, 숏
        if After944():
            if abs(body30) < 1 and first30 < 0:
                if candle30['high'].iloc[-1] > candle30['open'].iloc[1] and candle30['open'].iloc[1] > candle30['close'].iloc[-1] and candle30['close'].iloc[-1] > candle30['open'].iloc[1] - 0.5:
                    if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                        if GetBeforeLow(candle30):
                            switch1 = False; switch2 = True; switch3 = True; switchShort = 30
                            UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchShort, 'switchShort');
                            # 시장가 매도
                            SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                            # 포지션 정보 가져오기
                            position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                            # 지정가 매수
                            buy_sell, name, odno = BuyLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price-2); sleep(0.1)
                            # 알림
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "매도(전략2 30분봉)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
        # [전략2]10분봉, 숏
        if After914():
            if abs(body10) < 1 and first30 < 0:
                if candle10['high'].iloc[-1] > candle10['open'].iloc[1] and candle10['open'].iloc[1] > candle10['close'].iloc[-1] and candle10['close'].iloc[-1] > candle10['open'].iloc[1] - 0.5:
                    if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                        if GetBeforeLow(candle10):
                            switch1 = False; switch2 = True; switch3 = True; switchShort = 10
                            UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchShort, 'switchShort');
                            # 시장가 매도
                            SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                            # 포지션 정보 가져오기
                            position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                            # 지정가 매수
                            buy_sell, name, odno = BuyLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price-2); sleep(0.1)
                            # 알림
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "매도(전략2 10분봉)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)


        # [전략3]30분봉, 롱
        if After944():
            if abs(body30) < 1.5 and abs(body30_) < abs(body30):
                if body30_ < 0 and body30 > 0:
                    if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                        if indicator30['ma20'].iloc[-1] < indicator30['ma10'].iloc[-1] and indicator30['ma10'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                            if candle30['open'].iloc[1] < candle30['close'].iloc[-1] and candle30['close'].iloc[-1] < candle30['open'].iloc[1] + 3:
                                if GetBeforeHigh(candle30):
                                    switch1 = False; switch2 = True; switch3 = True; switchLong = 30
                                    UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchLong, 'switchLong');
                                    # 시장가 매수
                                    BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                    # 포지션 정보 가져오기
                                    position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                    # 지정가 매도
                                    buy_sell, name, odno = SellLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price+2); sleep(0.1)
                                    # 알림
                                    t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                    message = "{} {}".format(t, "매수(전략3 30분봉)"); SendMessage(message, discord); print(message)
                                    with open('Log.txt', 'a') as fa:
                                        fa.write('\n'); fa.write(message)
        # [전략3]10분봉, 롱
        if After914():
            if abs(body10) < 1.5 and abs(body10_) < abs(body10):
                if body10_ < 0 and body10 > 0:
                    if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                        if indicator10['ma20'].iloc[-1] < indicator10['ma10'].iloc[-1] and indicator10['ma10'].iloc[-1] < indicator10['ma5'].iloc[-1]:
                            if candle10['open'].iloc[1] < candle10['close'].iloc[-1] and candle10['close'].iloc[-1] < candle10['open'].iloc[1] + 3:
                                if GetBeforeHigh(candle10):
                                    switch1 = False; switch2 = True; switch3 = True; switchLong = 10
                                    UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchLong, 'switchLong');
                                    # 시장가 매수
                                    BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                    # 포지션 정보 가져오기
                                    position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                    # 지정가 매도
                                    buy_sell, name, odno = SellLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price+2); sleep(0.1)
                                    # 알림
                                    t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                    message = "{} {}".format(t, "매수(전략3 10분봉)"); SendMessage(message, discord); print(message)
                                    with open('Log.txt', 'a') as fa:
                                        fa.write('\n'); fa.write(message)
        # [전략3]5분봉, 롱
        if After914():
            if abs(body5) < 1.5 and abs(body5_) < abs(body5):
                if body5_ < 0 and body5 > 0:
                    if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                        if indicator5['ma20'].iloc[-1] < indicator5['ma10'].iloc[-1] and indicator5['ma10'].iloc[-1] < indicator5['ma5'].iloc[-1]:
                            if candle5['open'].iloc[1] < candle5['close'].iloc[-1] and candle5['close'].iloc[-1] < candle5['open'].iloc[1] + 3:
                                if GetBeforeHigh(candle5):
                                    switch1 = False; switch2 = True; switch3 = True; switchLong = 5
                                    UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchLong, 'switchLong');
                                    # 시장가 매수
                                    BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                    # 포지션 정보 가져오기
                                    position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                    # 지정가 매도
                                    buy_sell, name, odno = SellLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price+2); sleep(0.1)
                                    # 알림
                                    t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                    message = "{} {}".format(t, "매수(전략3 5분봉)"); SendMessage(message, discord); print(message)
                                    with open('Log.txt', 'a') as fa:
                                        fa.write('\n'); fa.write(message)

        # [전략3]30분봉, 숏
        if After944():
            if abs(body30) < 1.5 and abs(body30_) < abs(body30):
                if body30_ > 0 and body30 < 0:
                    if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                        if indicator30['ma20'].iloc[-1] > indicator30['ma10'].iloc[-1] and indicator30['ma10'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                            if candle30['open'].iloc[1] > candle30['close'].iloc[-1] and candle30['close'].iloc[-1] > candle30['open'].iloc[1] - 3:
                                if GetBeforeLow(candle30):
                                    switch1 = False; switch2 = True; switch3 = True; switchShort = 30
                                    UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchShort, 'switchShort');
                                    # 시장가 매도
                                    SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                    # 포지션 정보 가져오기
                                    position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                    # 지정가 매수
                                    buy_sell, name, odno = BuyLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price-2); sleep(0.1)
                                    # 알림
                                    t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                    message = "{} {}".format(t, "매도(전략3 30분봉)"); SendMessage(message, discord); print(message)
                                    with open('Log.txt', 'a') as fa:
                                        fa.write('\n'); fa.write(message)
        # [전략3]10분봉, 숏
        if After914():
            if abs(body10) < 1.5 and abs(body10_) < abs(body10):
                if body10_ > 0 and body10 < 0:
                    if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                        if indicator10['ma20'].iloc[-1] > indicator10['ma10'].iloc[-1] and indicator10['ma10'].iloc[-1] > indicator10['ma5'].iloc[-1]:
                            if candle10['open'].iloc[1] > candle10['close'].iloc[-1] and candle10['close'].iloc[-1] > candle10['open'].iloc[1] - 3:
                                if GetBeforeLow(candle10):
                                    switch1 = False; switch2 = True; switch3 = True; switchShort = 10
                                    UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchShort, 'switchShort');
                                    # 시장가 매도
                                    SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                    # 포지션 정보 가져오기
                                    position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                    # 지정가 매수
                                    buy_sell, name, odno = BuyLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price-2); sleep(0.1)
                                    # 알림
                                    t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                    message = "{} {}".format(t, "매도(전략3 10분봉)"); SendMessage(message, discord); print(message)
                                    with open('Log.txt', 'a') as fa:
                                        fa.write('\n'); fa.write(message)

        # [전략3]5분봉, 숏
        if After914():
            if abs(body5) < 1.5 and abs(body5_) < abs(body5):
                if body5_ > 0 and body5 < 0:
                    if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                        if indicator5['ma20'].iloc[-1] > indicator5['ma10'].iloc[-1] and indicator5['ma10'].iloc[-1] > indicator5['ma5'].iloc[-1]:
                            if candle5['open'].iloc[1] > candle5['close'].iloc[-1] and candle5['close'].iloc[-1] > candle5['open'].iloc[1] - 3:
                                if GetBeforeLow(candle5):
                                    switch1 = False; switch2 = True; switch3 = True; switchShort = 5
                                    UpdateParameter(switch1, 'switch1'); UpdateParameter(switch2, 'switch2'); UpdateParameter(switch3, 'switch3'); UpdateParameter(switchShort, 'switchShort');
                                    # 시장가 매도
                                    SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, qty); sleep(0.1)
                                    # 포지션 정보 가져오기
                                    position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
                                    # 지정가 매수
                                    buy_sell, name, odno = BuyLimit(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity, price-2); sleep(0.1)
                                    # 알림
                                    t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                    message = "{} {}".format(t, "매도(전략3 5분봉)"); SendMessage(message, discord); print(message)
                                    with open('Log.txt', 'a') as fa:
                                        fa.write('\n'); fa.write(message)

def ClosePosition():
    global switch2, switchLong, switchShort, appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, discord
    if switch2:
        switch2 = False; UpdateParameter(switch2, 'switch2')
        # 포지션 정보 가져오기
        position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
        # 포지션이 있으면
        if quantity > 0:
            '''
            보조지표 캔들
                indicator5, indicator10, indicator30
            당일 캔들
                candle5, candle10, candle30
            현재봉 (종가 - 시가)
                body5, body10, body30
            직전봉 (종가 - 시가)
                body5_, body10_, body30_
            최초봉 (종가 - 시가)
                first5, first10, first30
            '''
            candle5, indicator5 = Get5(appkey, appsecret, token, date)  # 5분봉
            candle10, indicator10 = Get10(appkey, appsecret, token, date)  # 10분봉
            candle30, indicator30 = Get30(appkey, appsecret, token, date)  # 30분봉
            # 현재봉
            body5 = candle5['close'].iloc[-1] - candle5['open'].iloc[-1]
            body10 = candle10['close'].iloc[-1] - candle10['open'].iloc[-1]
            body30 = candle30['close'].iloc[-1] - candle30['open'].iloc[-1]
            # 직전봉
            body5_ = candle5['close'].iloc[-2] - candle5['open'].iloc[-2]
            body10_ = candle10['close'].iloc[-2] - candle10['open'].iloc[-2]
            body30_ = candle30['close'].iloc[-2] - candle30['open'].iloc[-2]

            if position == "매수":
                # 5분봉
                if switchLong == 5:
                    if body5 > 0:
                        if abs(body5) < 1:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price+1)
                            # 알림
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격+1)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if candle5['high'].iloc[-2] > candle5['high'].iloc[-1]:
                            SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                            # 알림
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                    if body5 < 0:
                        if candle5['close'].iloc[-1] > indicator5['ma5'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price+0.5)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격+0.5)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if max(candle5['high'].iloc[:-1]) < candle5['high'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                            if abs(body5_) < abs(body5):
                                SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                                # 알림
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)
                    if candle5['close'].iloc[-1] < indicator5['ma5'].iloc[-1]:
                        SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                        # 알림
                        t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                        message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                        with open('Log.txt', 'a') as fa:
                            fa.write('\n'); fa.write(message)
                # 10분봉
                if switchLong == 10:
                    if body10 > 0:
                        if abs(body10) < 1:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price+1)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격+1)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if candle10['high'].iloc[-2] > candle10['high'].iloc[-1]:
                            SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                            # 알림
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                    if body10 < 0:
                        if candle10['close'].iloc[-1] > indicator10['ma5'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price+0.5)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격+0.5)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if max(candle10['high'].iloc[:-1]) < candle10['high'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                            if abs(body10_) < abs(body10):
                                SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)
                    if candle10['close'].iloc[-1] < indicator10['ma5'].iloc[-1]:
                        SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                        # 알림
                        t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                        message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                        with open('Log.txt', 'a') as fa:
                            fa.write('\n'); fa.write(message)

                # 30분봉
                if switchLong == 30:
                    if body30 > 0:
                        if abs(body30) < 1:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price+1)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격+1)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if candle30['high'].iloc[-2] > candle30['high'].iloc[-1]:
                            SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                    if body30 < 0:
                        if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price+0.5)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격+0.5)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if max(candle30['high'].iloc[:-1]) < candle30['high'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                            if abs(body30_) < abs(body30):
                                SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)
                    if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                        SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                        t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                        message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                        with open('Log.txt', 'a') as fa:
                            fa.write('\n'); fa.write(message)

            elif position == "매도":
                # 5분봉
                if switchShort == 5:
                    if body5 < 0:
                        if abs(body5) < 1:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price-1)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격-1)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if candle5['low'].iloc[-2] < candle5['low'].iloc[-1]:
                            BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                    if body5 > 0:
                        if candle5['close'].iloc[-1] < indicator5['ma5'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price-0.5)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격-0.5)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if min(candle5['low'].iloc[:-1]) > candle5['low'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                            if abs(body5_) < abs(body5):
                                BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)
                    if candle5['close'].iloc[-1] > indicator5['ma5'].iloc[-1]:
                        BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                        t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                        message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                        with open('Log.txt', 'a') as fa:
                            fa.write('\n'); fa.write(message)

                # 10분봉
                if switchShort == 10:
                    if body10 < 0:
                        if abs(body10) < 1:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price-1)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격-1)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if candle10['low'].iloc[-2] < candle10['low'].iloc[-1]:
                            BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                    if body10 > 0:
                        if candle10['close'].iloc[-1] < indicator10['ma5'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price-0.5)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격-0.5)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if min(candle10['low'].iloc[:-1]) > candle10['low'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                            if abs(body10_) < abs(body10):
                                BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)
                    if candle10['close'].iloc[-1] > indicator10['ma5'].iloc[-1]:
                        BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                        t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                        message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                        with open('Log.txt', 'a') as fa:
                            fa.write('\n'); fa.write(message)
                # 30분봉
                if switchShort == 30:
                    if body30 < 0:
                        if abs(body30) < 1:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price-1)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격-1)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if candle30['low'].iloc[-2] < candle30['low'].iloc[-1]:
                            BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                    if body30 > 0:
                        if candle30['close'].iloc[-1] < indicator30['ma5'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price-0.5)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격-0.5)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                        if min(candle30['low'].iloc[:-1]) > candle30['low'].iloc[-1]:
                            buy_sell, name, odno = ModifyOrderLimitWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno, price)
                            t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                            message = "{} {}".format(t, "지정가 변경(진입가격)"); SendMessage(message, discord); print(message)
                            with open('Log.txt', 'a') as fa:
                                fa.write('\n'); fa.write(message)
                            if abs(body30_) < abs(body30):
                                BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                                t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                                message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                                with open('Log.txt', 'a') as fa:
                                    fa.write('\n'); fa.write(message)
                    if candle30['close'].iloc[-1] > indicator30['ma5'].iloc[-1]:
                        BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
                        t = datetime.now(); t.strftime('%Y-%m-%d %H:%M:%S')
                        message = "{} {}".format(t, "종가청산"); SendMessage(message, discord); print(message)
                        with open('Log.txt', 'a') as fa:
                            fa.write('\n'); fa.write(message)

# 포지션 종료
def Close1515():
    global switchLong, switchShort, appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno
    # 포지션 정보 가져오기
    position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
    # 포지션이 있으면
    if quantity > 0:
        if position == "매수":
            SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
        elif position == "매도":
            BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
        # 미체결 주문 제거
        CancelOrderWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno)

def StopLoss():
    global switch3, switchLong, switchShort, appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno
    t = datetime.now()
    print(t)
    if switch3:
        # 포지션 정보 가져오기
        position, price, quantity = GetBalance(appkey, appsecret, token, CANO, ACNT_PRDT_CD); sleep(0.1)
        # 포지션이 있으면
        if quantity > 0:
            df = GetKOSPI200(appkey, appsecret, token, 3600, date)
            if position == "매수":
                if df['close'].iloc[-1] < price - 1:
                    SellMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
            elif position == "매도":
                if df['close'].iloc[-1] > price + 1:
                    BuyMarket(appkey, appsecret, token, CANO, ACNT_PRDT_CD, ticker, quantity)
        # 미체결 주문 제거
        else:
            CancelOrderWhole(appkey, appsecret, token, CANO, ACNT_PRDT_CD, odno)
            switch3 = False; UpdateParameter(switch3, 'switch3')

# Main 
m5 = ["04", "09", "14", "19", "24", "29", "34", "39", "44", "49", "54", "59"]
scheduleOpen = []  # OpenPosition 스케줄
scheduleClose = []  # ClosePosition 스케줄
for i in range(9,15):
    if i == 9:
        h = '09'
    else:
        h = str(i)
    for m in m5:
        scheduleOpen.append('{}:{}:{}'.format(h, m, 58))
        scheduleClose.append('{}:{}:{}'.format(h, m, 57))


# 09시 Reset
schedule.every().day.at("09:00:00").do(ResetToday)

schedule.every().seconds.do(StopLoss)
for i in scheduleOpen:
    schedule.every().day.at(i).do(OpenPosition)
for i in scheduleClose:
    schedule.every().day.at(i).do(ClosePosition)
# 15시 15분 강제청산
schedule.every().day.at("15:15:00").do(Close1515)

while True:
    schedule.run_pending()
    sleep(1)