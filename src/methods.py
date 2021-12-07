# -*- coding:utf-8 -*-
import time
import pyupbit
import pandas as pd


# 프린트 메소드
def log_print(message):
    now = time.localtime()
    now = "[%04d/%02d/%02d %02d:%02d:%02d]" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    print(now, message)


# 일반 api 호출 시간지연 메소드
def delay_for_normal_api():
    time.sleep(0.07)


# 거래 api 호출 시간지연 메소드
def delay_for_exchange_api():
    time.sleep(3)


# 거래대금이 많은 순으로 코인 리스트를 얻는다.
# interval : Interval 기간(day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month)
# top : 상위 몇개를 확인할것인지 지정
def get_top_coin_list(interval, top):
    # 원화 마켓의 코인 티커를 리스트로 담아요.
    tickers = pyupbit.get_tickers("KRW", True, False, True)
    delay_for_normal_api()

    # 딕셔너리를 하나 만듭니다.
    dic_coin_money = dict()

    # for문을 돌면서 모든 코인들을 순회합니다.
    for ticker in tickers:
        if ticker["market_warning"] != "NONE":
            # log_print(ticker["market"] + "은 정상적인 상태가 아닙니다 목록에서 제외합니다.")
            continue
        try:
            # 캔들 정보를 가져온다.
            df = pyupbit.get_ohlcv(ticker["market"], interval)
            # 최근 2개 봉의 거래대금을 합산한다
            volume_money = float(df['value'][-2]) + float(df['value'][-1])
            # 이걸 위에서 만든 딕셔너리에 넣어줍니다. Key는 코인의 티커, Value는 위에서 구한 거래대금
            dic_coin_money[ticker["market"]] = volume_money
            # 티커와 거래액을 출력해 봅니다.
            # print(ticker["market"], dic_coin_money[ticker["market"]])
            # api 최대 호출 횟수 피하기 위한 시간텀
            delay_for_normal_api()

        except Exception as e:
            log_print(e)

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


# 내가 소유한 코인 목록을 받아오는 메소드
def get_my_coins(upbit):
    balances = upbit.get_balances()
    delay_for_normal_api()
    my_coins = list()
    for balance in balances:
        if balance["currency"] == "KRW" or float(balance["avg_buy_price"]) == float(0):
            continue
        my_coin = "KRW-" + balance["currency"]
        my_coins.append(my_coin)
    return my_coins


# 시장상황 분석 메소드 (하락장, 상승장, 일반장 구분)
def check_market_status(target_coin):
    df_60 = pyupbit.get_ohlcv(target_coin, "minute60")  # 60분봉 정보
    delay_for_normal_api()
    rsi_14_before = get_rsi(df_60, 14, -4)              # 3시간 전 rsi14 지표
    rsi_14_after = get_rsi(df_60, 14, -2)               # 1시간 전 rsi14 지표
    condition = rsi_14_after / rsi_14_before            # 1시간 전 지표 / 3시간 전 지표(장 상황 체크기준)
    market_status = "일반장"                             # 장 상태(일반장)
    if condition >= 1.1:
        market_status = "상승장"                         # 장 상태(상승장) 체크기준이 1.1 이상인 경우
    elif condition < 0.95:
        market_status = "하락장"                         # 장 상태(하락장) 체크기준이 0.95 이하인 경우

    return market_status


# 목표 수익율 지정 메소드
def select_revenue_rate(market_status):
    target_revenue = 1.02
    if market_status == "일반장":
        target_revenue = 1.02
    elif market_status == "상승장":
        target_revenue = 1.03
    elif market_status == "하락장":
        target_revenue = 1.01

    return target_revenue


# 타겟코인 시장분석 후 매도하는 로직
# upbit : 로그인 된 업비트 객체
# target_coin : 매도할 코인 티커
# invest_balance : 투자 원금
# now_balance : 투자금 잔액
def sell_logic(upbit, target_coin, invest_balance, now_balance):
    # log_print("매도로직을 시작합니다.")
    # log_print("거래 대상: " + str(target_coin))

    # 시장상황 분석
    market_status = check_market_status(target_coin)

    # 목표 수익율 설정
    target_revenue = select_revenue_rate(market_status)

    # log_print("시장 상황: " + market_status + ", 목표 수익율: " + str(round((target_revenue - 1.0) * 100, 1)) + '%')

    # 내가 보유한 코인중 타겟 코인의 정보를 가져온다.
    my_coin = ""
    for balance in upbit.get_balances():
        if "KRW-" + balance["currency"] == target_coin:
            my_coin = balance
    delay_for_normal_api()

    # 투자금 기준 평단가를 계산한다. (투자원금 - 현재잔고) / 코인 갯수
    avg_buy_price = (invest_balance - now_balance) / float(my_coin["balance"])

    # 투자금 기준 평단가가 업비트에 기재된 평단가보다 낮은 경우
    if avg_buy_price < float(my_coin["avg_buy_price"]):
        # 평단가는 업비트에 기재된 평단가를 기준으로 한다.
        avg_buy_price = float(my_coin["avg_buy_price"])

    # 목표 가격을 정하고 목표 가격보다 현재 가격이 높은경우 매도한다.
    target_price = avg_buy_price * target_revenue
    now_price = pyupbit.get_current_price(target_coin)
    if now_price >= target_price:
        upbit.sell_market_order(target_coin, float(my_coin["balance"]))
        log_print(str(target_coin) + " 코인을 모두 판매했습니다.")
        delay_for_exchange_api()
        return True
    else:
        # log_print("수익률에 도달하지 못했습니다.")
        delay_for_normal_api()
        return False


# 매수 대상인지 체크하는 메소드
# target_coin : 대상 코인 티커
# interval : 봉 기준시간(minute5, minute60, etc...)
def check_purchase_target(target_coin, interval):
    df = pyupbit.get_ohlcv(target_coin, interval)   # 기준 봉 시간
    delay_for_normal_api()

    # 지표기준들/ rsi, ma, 볼린저밴드, 이동성돌파등 True, False로 구분

    # 기준봉 2개의 rsi 지표를 구한다
    rsi_14_comparison = get_rsi(df, 14, -2)         # 직전 봉 rsi14
    rsi_14_now = get_rsi(df, 14, -1)                # 현재 봉 rsi14
    # rsi
    # 로직 고도화 시켜야함
    is_purchase_target = False
    # 매수 대상이 맞다면
    if is_purchase_target:
        return True
    # 매수 대상이 아니라면
    else:
        return False


# 대상코인 매수 함수
def buy_target_coin(ticker):
    print("구매한당")


# 매수로직
def buy_logic():
    print("매수로직은 매도로직도 포함해야하고 매수대상 체크도 해야하고 실제 매수함수도 포함해야한다")
    print("조건은 트레이딩봇에 넣어놓았다")
