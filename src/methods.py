import time
import pyupbit
import pandas as pd


# 거래대금이 많은 순으로 코인 리스트를 얻는다.
# interval : Interval 기간(day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month)
# top : 상위 몇개를 확인할것인지 지정
def get_top_coin_list(interval, top):
    # 원화 마켓의 코인 티커를 리스트로 담아요.
    tickers = pyupbit.get_tickers("KRW")

    # 딕셔너리를 하나 만듭니다.
    dic_coin_money = dict()

    # for문을 돌면서 모든 코인들을 순회합니다.
    for ticker in tickers:
        try:
            # 캔들 정보를 가져온다.
            df = pyupbit.get_ohlcv(ticker, interval)
            # 최근 2개 봉의 거래대금을 합산한다
            volume_money = float(df['value'][-2]) + float(df['value'][-1])
            # 이걸 위에서 만든 딕셔너리에 넣어줍니다. Key는 코인의 티커, Value는 위에서 구한 거래대금
            dic_coin_money[ticker] = volume_money
            # 티커와 거래액을 출력해 봅니다.
            # print(ticker, dic_coin_money[ticker])
            # api 최대 호출 횟수 피하기 위한 시간텀
            time.sleep(0.07)

        except Exception as e:
            print("exception:", e)

    # 딕셔너리를 값으로 정렬하되 숫자가 큰 순서대로 정렬합니다.
    dic_sorted_coin_money = sorted(dic_coin_money.items(), key=lambda x: x[1], reverse=True)

    # 빈 리스트를 만듭니다.
    coin_list = list()

    # 코인을 셀 변수를 만들어요.
    cnt = 0

    # 티커와 거래대금 많은 순으로 정렬된 딕셔너리를 순회하면서
    for coin_data in dic_sorted_coin_money:
        # 코인 개수를 증가시켜주는데..
        cnt += 1

        # 파라메타로 넘어온 top의 수보다 작으면 코인 리스트에 코인 티커를 넣어줍니다.
        # 즉 top에 10이 들어갔다면 결과적으로 top 10에 해당하는 코인 티커가 coin_list에 들어갑니다.
        if cnt <= top:
            coin_list.append(coin_data[0])
        else:
            break

    # 코인 리스트를 리턴해 줍니다.
    return coin_list


# RSI지표 수치를 구해준다.
# ohlcv: 분봉/일봉 정보
# period: 기간
# st: 기준 날짜(-1, -2, -3 등 최근일자부터 -1씩 추가)
def get_rsi(ohlcv, period, st):
    ohlcv["close"] = ohlcv["close"]
    delta = ohlcv["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    rs = _gain / _loss
    return float(pd.Series(100 - (100 / (1 + rs)), name="RSI").iloc[st])


# 티커에 해당하는 코인이 매수된 상태면 참을 리턴하는함수
def is_has_coin(balances, ticker):
    has_coin = False
    for value in balances:
        real_ticker = value['unit_currency'] + "-" + value['currency']
        if ticker == real_ticker:
            has_coin = True
    return has_coin


# 프린트 메소드
def log_print(message):
    now = time.localtime()
    now = "[%04d/%02d/%02d %02d:%02d:%02d]" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    print(now, message)

