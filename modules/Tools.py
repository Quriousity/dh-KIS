import pickle

from os import path
from datetime import datetime


# 경로 확인 후 있으면 가져오고 없으면 현재값으로 만드는 함수:
def CheckParameter(parameter, parameterName):
    if path.exists('./{}.pickle'.format(parameterName)):
        with open('{}.pickle'.format(parameterName), 'rb') as fr:
            parameter = pickle.load(fr)
    else:
        with open('{}.pickle'.format(parameterName), 'wb') as fw:
            pickle.dump(parameter, fw)

# 파라미터 변경되면 기록하는 함수
def UpdateParameter(parameter, parameterName):
    with open('{}.pickle'.format(parameterName), 'wb') as fw:
        pickle.dump(parameter, fw)

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