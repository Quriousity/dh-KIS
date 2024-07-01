# 설치

### 계좌정보/API정보
```
vi conf.json
```
#### conf.json
```
{
    "appkey": "",
    "appsecret": "",
    "CANO": "",
    "ACNT_PRDT_CD": "",
    "Ticker": "101000",
    "qty": 1
}
```
### 가상환경 설치
```
python -m venv mg
```
### 가상환경 활성화
#### Linux/MacOS
```
source mg/bin/activate
```
#### Windows (cmd)
```
mg\Scripts\activate
```

# 실행
### 가상환경 활성화
#### Linux/MacOS
```
source mg/bin/activate
```
#### Windows (cmd)
```
mg\Scripts\activate
```
### 실행
```
python dh.py
```