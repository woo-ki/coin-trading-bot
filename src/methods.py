# -*- coding:utf-8 -*-
import time
import pyupbit
import pandas as pd
import numpy
import math


# 프린트 메소드
def log_print(message):
    now = time.localtime()
    now = "[%04d/%02d/%02d %02d:%02d:%02d]" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    print(now, message)


# 종목, 캔들등 api 호출 시간지연 메소드
def delay_for_normal_api():
    time.sleep(1)


# 거래 api 호출 시간지연 메소드
def delay_for_deal_api():
    time.sleep(10)


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
            time.sleep(0.1)

        except Exception as e:
            log_print(e)
            get_top_coin_list(interval, top)

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


# 볼린저 밴드를 구해준다
# ohlcv: 분봉/일봉 정보
# period: 기간
# st: 기준 날짜(-1, -2, -3 등 최근일자부터 -1씩 추가)
def get_bb(ohlcv, period, st):
    dic_bb = dict()

    ohlcv = ohlcv[::-1]
    ohlcv = ohlcv.shift(st + 1)
    close = ohlcv["close"].iloc[::-1]

    unit = 2.0
    bb_center = numpy.mean(close[len(close) - period:len(close)])
    band1 = unit * numpy.std(close[len(close) - period:len(close)])

    dic_bb['ma'] = float(bb_center)
    dic_bb['upper'] = float(bb_center + band1)
    dic_bb['lower'] = float(bb_center - band1)

    return dic_bb


# 이동평균선 수치를 구해준다
# ohlcv: 분봉/일봉 정보
# period: 기간
# st: 기준 날짜(-1, -2, -3 등 최근일자부터 -1씩 추가)
def get_ma(ohlcv, period, st):
    close = ohlcv["close"]
    ma = close.rolling(period).mean()
    return float(ma[st])


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


# 실제 평균 객단가를 반환하는 메소드
# upbit : 로그인 된 업비트 객체
# target_coin : 조회할 코인 티커
# invest_balance : 투자 원금
# except_balance : 투자예외 지정금
def get_real_avg_buy_price(upbit, target_coin, invest_balance, except_balance):
    # 내가 보유한 코인중 타겟 코인의 정보를 가져온다.
    my_coin = ""
    try:
        for balance in upbit.get_balances():
            if "KRW-" + balance["currency"] == target_coin:
                my_coin = balance
        delay_for_normal_api()
    except Exception as e:
        log_print(e)
        get_real_avg_buy_price(upbit, target_coin, invest_balance, except_balance)

    # 내 코인의 평균 객단가(업비트 표기)
    upbit_avg_buy_price = float(my_coin["avg_buy_price"])

    # 내 코인의 평균 객단가(거래에 사용한 금액기준 표기)
    # 현재 원화 잔고를 받아와서 거래가능 금액을 계산한다. (현재 잔고 - 투자 예외 잔고)
    try:
        now_balance = int(upbit.get_balance("KRW")) - except_balance
    except Exception as e:
        log_print(e)
        get_real_avg_buy_price(upbit, target_coin, invest_balance, except_balance)
    delay_for_normal_api()
    # 코인 투자금액(투자원금 - 현재잔고)
    used_money = invest_balance - now_balance
    # 투자금 기준 평단가를 계산한다. 코인 투자금액 / 코인 갯수
    custom_avg_buy_price = used_money / float(my_coin["balance"])

    # 업비트 평단가보다 직접 계산한 평단가가 높으면
    if custom_avg_buy_price >= upbit_avg_buy_price:
        # 실제 평단가는 직접 계산한 평단가로 사용한다
        real_avg_buy_price = custom_avg_buy_price
    # 업비트 평단가가 직접 계산한 평단가보다 높으면
    else:
        # 실제 평단가는 업비트 평단가로 사용한다
        real_avg_buy_price = upbit_avg_buy_price
    return real_avg_buy_price


# 타겟코인 시장분석 후 매도하는 로직
# upbit : 로그인 된 업비트 객체
# target_coin : 매도할 코인 티커
# invest_balance : 투자 원금
# except_balance : 투자예외 지정금
# custom_revenue : 커스텀 수익율
def sell_logic(upbit, target_coin, invest_balance, except_balance, custom_revenue=0.0):
    # log_print("매도로직을 시작합니다.")
    # log_print("거래 대상: " + str(target_coin))

    # 시장상황 분석
    market_status = check_market_status(target_coin)

    # 목표 수익율 설정
    target_revenue = select_revenue_rate(market_status)

    # 커스텀 수익율 있는경우 목표 수익율 재지정
    if custom_revenue != 0:
        target_revenue = custom_revenue

    # log_print("시장 상황: " + market_status + ", 목표 수익율: " + str(round((target_revenue - 1.0) * 100, 1)) + '%')

    real_avg_buy_price = get_real_avg_buy_price(upbit, target_coin, invest_balance, except_balance)

    # 목표 가격을 정하고 목표 가격보다 현재 가격이 높고, 코인의 매도세가 시작된 경우 매도한다.
    target_price = real_avg_buy_price * target_revenue
    now_price = pyupbit.get_current_price(target_coin)
    # 1분봉 기준 rsi지표 생성
    try:
        df_1 = pyupbit.get_ohlcv(target_coin, "minute1")
    except Exception as e:
        log_print(e)
        sell_logic(upbit, target_coin, invest_balance, except_balance, custom_revenue)
    before_rsi_1 = get_rsi(df_1, 14, -1)
    now_rsi_1 = get_rsi(df_1, 14, -2)
    is_rsi_1_degradation = before_rsi_1 / now_rsi_1 < 0.97
    if now_price >= target_price and is_rsi_1_degradation:
        upbit.sell_market_order(target_coin, upbit.get_balance(target_coin))
        log_print(str(target_coin) + " 코인을 모두 판매했습니다.")
        delay_for_deal_api()
        return True
    else:
        # log_print("수익률에 도달하지 못했습니다.")
        delay_for_normal_api()
        return False


# 매수 대상인지 체크하는 메소드
# target_coin : 대상 코인 티커
# interval : 봉 기준시간(minute5, minute60, etc...)
def check_purchase_target(target_coin, interval):
    # 기준 지표 통과여부
    rsi_passed = False  # rsi 지표
    ma_passed = False   # ma 골든 크로스
    bb_passed = False   # 볼린저 밴드
    vb_passed = False   # 변동성 돌파 전략

    # 분봉 또는 일봉 정보를 가져온다.
    df = pyupbit.get_ohlcv(target_coin, interval)
    delay_for_normal_api()

    # 지금 코인가격을 구해온다
    now_price = df["close"][-1]

    # 기준봉 2개의 rsi 지표를 구한다
    rsi_14_comparison = get_rsi(df, 14, -2)         # 직전 봉 rsi14
    rsi_14_now = get_rsi(df, 14, -1)                # 현재 봉 rsi14
    # 직전 rsi14 대비 5%상승한 경우
    if rsi_14_now / rsi_14_comparison > 1.05:
        rsi_passed = True

    # 기준 이평선 정보를 구한다
    ma6 = get_ma(df, 6, -1)     # 6개봉 이평선
    ma24 = get_ma(df, 24, -1)   # 24개봉 이평선
    # 골든크로스에 충족되면
    if ma6 >= ma24:
        ma_passed = True

    # 볼린저 밴드 데이터를 구해온다
    bb = get_bb(df, 20, -1)
    bb_upper = float(bb["upper"])
    bb_lower = float(bb["lower"])
    bb_ma = float(bb["ma"])
    bb_max = (bb_upper - bb_ma) * 0.2 + bb_ma
    bb_min = bb_ma - (bb_ma - bb_lower) * 0.5
    # 볼린저밴드 최소값 < 현재가격 < 볼린저밴드 최대값 , 지금 봉이 양봉인경우
    if bb_min < now_price < bb_max and df["close"][-1] - df["close"][-1] > 0:
        bb_passed = True

    # 변동성 돌파 필요 데이터를 구해온다.
    last_max = df["high"][-2]
    last_min = df["low"][-2]
    now_open = df["open"][-1]
    # 변동성 돌파 전략 지금가격 > (전고가 - 전저가) * 0.5 + 지금봉시작가
    if now_price > (last_max - last_min) * 0.5 + now_open:
        vb_passed = True

    # 결과값 딕셔너리를 반환해준다
    return {
        "rsi": rsi_passed,
        "ma": ma_passed,
        "bb": bb_passed,
        "vb": vb_passed
    }


# 대상코인 매수 함수
# upbit : 로그인 된 업비트 객체
# target_coin : 매도할 코인 티커
# invest_balance : 투자 원금
# except_balance : 투자예외 지정금
# check_result : 어떤 매수로직이 참인지 담고있는 딕셔너리
def buy_target_coin(upbit, target_coin, invest_balance, except_balance, check_result):
    # 투자 대상 거래 수수료
    target_info = upbit.get_chance(target_coin)     # 투자 코인 시장정보
    delay_for_normal_api()
    buy_fees = float(target_info["bid_fee"])        # 투자 코인 매수 수수료

    # 1회당 매수금액 설정
    budget_for_buy_once = invest_balance * 0.075                                         # 1회 매수 금액
    try:
        now_my_balance = int(upbit.get_balance("KRW")) - except_balance                     # 현재 잔고
    except Exception as e:
        log_print(e)
        buy_target_coin(upbit, target_coin, invest_balance, except_balance, check_result)
    min_buy_price = float(target_info["market"]["bid"]["min_total"])                    # 최소 매수 금액

    # 현재 잔고가 최소주문금액 이상인 경우에만 매수 로직 실행
    if now_my_balance >= min_buy_price * (1 + buy_fees):
        # 현재 잔고가 최소 주문금액 2회를 할 수 없는경우
        if now_my_balance < math.ceil(min_buy_price * (1 + buy_fees)) * 2:
            budget_for_buy_once = math.floor(now_my_balance / (1 + buy_fees))           # 1회 매수 금액 = 현재 잔고 전액
        else:
            budget_for_buy_once = math.floor(budget_for_buy_once / (1 + buy_fees))      # 수수료 공제포함 1회 주문금액
            # 1회 매수금액이 최소 주문금액보다 작은경우
            if budget_for_buy_once < min_buy_price:
                budget_for_buy_once = min_buy_price                                     # 1회 매수 금액 = 최소 주문 금액
            # 1회 매수를 한 이후 잔액이 최소 주문금액보다 작은경우
            if now_my_balance - (budget_for_buy_once * (1 + buy_fees)) < min_buy_price:
                budget_for_buy_once = math.floor(now_my_balance / (1 + buy_fees))       # 1회 매수 금액 = 수수료 공제 포함 현재 잔고 전액
        # 매수 실행
        buy_result = upbit.buy_market_order(target_coin, budget_for_buy_once)

        # 매수 전략 문자열 만들기
        buy_standard = ""
        for key in check_result:
            if buy_standard == "":
                if key == "rsi":
                    buy_standard += "rsi 상승"
                elif key == "ma":
                    buy_standard += "ma 골든크로스"
                elif key == "bb":
                    buy_standard += "볼린저 밴드 표준범위"
                elif key == "vb":
                    buy_standard += "변동성 돌파"
            else:
                if key == "rsi":
                    buy_standard += ", rsi 상승"
                elif key == "ma":
                    buy_standard += ", ma 골든크로스"
                elif key == "bb":
                    buy_standard += ", 볼린저 밴드 표준범위"
                elif key == "vb":
                    buy_standard += ", 변동성 돌파"
        log_print("매수 전략: " + buy_standard)
        log_print(str(target_coin) + " 매수 성공: " + str(buy_result["price"]) + "원")
        delay_for_deal_api()
        return True
    else:
        #     # 리얼객단가 가져오기
        #     real_avg_buy_price = get_real_avg_buy_price(upbit, target_coin, invest_balance, except_balance)
        #     # 현재 코인 가격 가져오기
        #     now_coin_price = pyupbit.get_current_price(target_coin)
        #     delay_for_normal_api()
        #
        #     # 현재 코인 가격이 실제 객단가보다 1% 이상 낮은경우
        #     if (real_avg_buy_price - now_coin_price) / real_avg_buy_price > 0.01:
        #         # 보유 코인의 25% 손절
        #         upbit.sell_market_order(target_coin, upbit.get_balance(target_coin) * 0.25)
        #         log_print(str(target_coin) + " 코인을 25% 손절했습니다")
        #         delay_for_deal_api()
        return False


# 나의 업비트 평균단가 체크하기
def check_my_upbit_avg_price(upbit, target_coin):
    my_coin = ""
    for balance in upbit.get_balances():
        if "KRW-" + balance["currency"] == target_coin:
            my_coin = balance
    delay_for_normal_api()
    if my_coin == "":
        return float(0.0)
    else:
        return float(my_coin["avg_buy_price"])


# 순환매수매도 모드 체크
# upbit : 로그인 된 업비트 객체
# target_coin : 조회할 코인 티커
# invest_balance : 투자 원금
# except_balance : 투자예외 지정금
def check_cycle_mode(upbit, target_coin, invest_balance, except_balance):
    # 내가 보유한 코인중 타겟 코인의 정보를 가져온다.
    my_coin = ""
    try:
        for balance in upbit.get_balances():
            if "KRW-" + balance["currency"] == target_coin:
                my_coin = balance
        delay_for_normal_api()
    except Exception as e:
        log_print(e)
        check_cycle_mode(upbit, target_coin, invest_balance, except_balance)

    # 내 코인의 평균 객단가(업비트 표기)
    upbit_avg = float(my_coin["avg_buy_price"])
    real_avg = get_real_avg_buy_price(upbit, target_coin, invest_balance, except_balance)

    # 실제 평단가와 업비트 평단가가 3퍼센트 이상 차이나면 순환매도매수라고 정의한다
    if real_avg >= upbit_avg * 1.02:
        return True
    else:
        return False


# 순환매 익절 실행
def good_sell_at_cycle_mode(upbit, target_coin, interval, invest_balance, except_balance):
    # 순환매 익절 대상 체크
    now_price = pyupbit.get_current_price(target_coin)
    delay_for_normal_api()
    my_coin_cnt = float(upbit.get_balance(target_coin))
    # 내 코인의 평균 객단가(업비트 표기)
    upbit_avg_buy_price = check_my_upbit_avg_price(upbit, target_coin)
    # 직전 볼린저밴드와 지금 볼린저밴드를 구해온다
    df = pyupbit.get_ohlcv(target_coin, interval)
    delay_for_normal_api()
    bb_before = get_bb(df, 20, -2)
    bb_now = get_bb(df, 20, -1)
    # 직전 코인 종가를 구해온다
    before_price = df["close"][-1]
    # 1분봉 기준 rsi지표 생성
    df_1 = pyupbit.get_ohlcv(target_coin, "minute1")
    before_rsi_1 = get_rsi(df_1, 14, -1)
    now_rsi_1 = get_rsi(df_1, 14, -2)
    is_rsi_1_degradation = before_rsi_1 / now_rsi_1 < 0.95

    # 조건1 현재 코인가격 * 보유 코인 수 / 투자예산 > 0.5 인가
    is_volume_passed = now_price * my_coin_cnt / invest_balance > 0.5
    # 조건1-2 현재 코인가격 * 보유 코인 수 / 투자예산 > 0.65 인가
    is_volume_passed2 = now_price * my_coin_cnt / invest_balance > 0.65
    # 조건2 나의 업비트 평단가보다 현재가가 높아지는 순간(직전에는 도달하지 못했다가 지금 도달한 경우)
    # rsi 1분봉을 기점으로 하락이 시작되는 타이밍
    is_grow_then_upbit_avg = before_price < upbit_avg_buy_price <= now_price and is_rsi_1_degradation
    # 조건3 볼린저밴드가 미들라인 아래에 있다가 미들라인에 도달한 경우
    # rsi 1분봉을 기점으로 하락이 시작되는 타이밍
    bb_grow1 = float(bb_before["ma"]) - before_price > 0
    bb_grow2 = float(bb_now["ma"]) - now_price < 0
    is_bb_grow_passed = bb_grow1 and bb_grow2 and is_rsi_1_degradation

    #  조건1과 2를 충족
    if is_volume_passed and is_grow_then_upbit_avg:
        # 보유 수량의 50퍼센트를 판매한다
        upbit.sell_market_order(target_coin, float(upbit.get_balance(target_coin)) * 0.5)
        log_print("순환매 업비트 평단 기준 익절 실행: " + str(target_coin) + " 코인을 50% 판매했습니다.")
        delay_for_deal_api()
        return True
    # 조건1-2와 3을 충족
    elif is_volume_passed2 and is_bb_grow_passed:
        # 보유 수량의 25퍼센트를 판매한다
        upbit.sell_market_order(target_coin, float(upbit.get_balance(target_coin)) * 0.25)
        log_print("순환매 볼린저밴드 기준 익절 실행: " + str(target_coin) + " 코인을 25% 판매했습니다.")
        delay_for_deal_api()
        return True
    # 비중이 50프로가 안되면
    elif not is_volume_passed:
        # 추가로 매수할 자금은 남아있는지 체크
        now_balance = int(upbit.get_balance("KRW")) - except_balance      # 현재 잔고
        target_info = upbit.get_chance(target_coin)                       # 투자 코인 시장정보
        delay_for_normal_api()

        buy_fees = float(target_info["bid_fee"])                          # 투자 코인 매수 수수료
        min_buy_price = float(target_info["market"]["bid"]["min_total"])  # 최소 매수 금액

        # 남아있지 않다면
        if now_balance < min_buy_price + min_buy_price * buy_fees:
            # 5초 단위로 순환매 가능대상 체크
            time.sleep(5)
            good_sell_at_cycle_mode(upbit, target_coin, interval, invest_balance, except_balance)
        # 잔액이 남아있다면
        else:
            # 매수위해 순환매 익절로직 종료
            return False
    # 비중이 50%는 넘었지만 다른 조건이 안된다면
    else:
        # 그냥 다음로직 실행
        return False


# 손절로직
# upbit : 로그인 된 업비트 객체
# target_coin : 매도할 코인 티커
# invest_balance : 투자 원금
# except_balance : 투자예외 지정금
# stop_loss_point : 손절 비율
def stop_loss_logic(upbit, target_coin, invest_balance, except_balance, stop_loss_point):
    # 시장상황 분석
    market_status = check_market_status(target_coin)

    real_avg_buy_price = get_real_avg_buy_price(upbit, target_coin, invest_balance, except_balance)

    # 조건1. 손절가보다 현재가가 낮다.
    # 조건2. 코인이 하락장이다
    # 조건3. 여전히 매도세가 진행중이다.
    target_price = real_avg_buy_price * stop_loss_point
    now_price = pyupbit.get_current_price(target_coin)
    # 1분봉 기준 rsi지표 생성
    try:
        df_1 = pyupbit.get_ohlcv(target_coin, "minute1")
    except Exception as e:
        log_print(e)
        stop_loss_logic(upbit, target_coin, invest_balance, except_balance, stop_loss_point)
    before_rsi_1 = get_rsi(df_1, 14, -1)
    now_rsi_1 = get_rsi(df_1, 14, -2)
    is_rsi_1_degradation = before_rsi_1 / now_rsi_1 < 0.97
    if now_price < target_price and is_rsi_1_degradation and market_status == "하락장":
        upbit.sell_market_order(target_coin, upbit.get_balance(target_coin))
        log_print(str(target_coin) + " 코인을 모두 손절했습니다.")
        delay_for_deal_api()
        return True
    else:
        # log_print("수익률에 도달하지 못했습니다.")
        delay_for_normal_api()
        return False


# 매수로직
# upbit : 로그인 된 업비트 객체
# target_coin : 대상 코인 티커
# interval : 봉 기준시간(minute5, minute60, etc...)
# invest_balance : 투자 원금
# except_balance : 투자예외 지정금
# init_purchase : 진입과 동시에 코인을 구매할지 여부
# check_result : init_purchase가 True인 경우 어떤 체크값들이 True인지 담고있는 딕셔너리
def buy_logic(upbit, target_coin, interval, invest_balance, except_balance, init_purchase=False, check_result=""):
    # 잔고부족으로 매수를 멈춰야 하는 경우
    stop_buy = False
    # 매수 로직 최초 진입시간을 체크한다.
    buy_logic_start = time.time()
    # 매수 시간텀 메모를 위해 buy_time 변수를 선언한다
    buy_time = ""
    # 보유코인 판매모드인 경우
    if init_purchase:
        # 대상 코인을 바로 시장가 매수한다.
        buy_target_coin(upbit, target_coin, invest_balance, except_balance, check_result)
        # 코인 구매 시간을 저장한다
        buy_time = time.time()

    while True:
        # 매도 로직을 실행한다
        now_time = time.time()
        # 매수 시작한지 180분이 경과하지 않았을 때 / 0.7% 익절
        if now_time - buy_logic_start < 10800:
            sell_result = sell_logic(upbit, target_coin, invest_balance, except_balance, 1.007)
        # 매수 시작한지 180분 경과 360분 경과 전 / 0.5% 익절
        elif 10800 <= now_time - buy_logic_start < 21600:
            sell_result = sell_logic(upbit, target_coin, invest_balance, except_balance, 1.005)
        # 매수 시작 후 360분 이상 경과 / 0.2% 까지 익절
        else:
            sell_result = sell_logic(upbit, target_coin, invest_balance, except_balance, 1.002)

        # 매도에 성공한 경우
        if sell_result:
            # 매수로직을 종료한다
            break

        # 손절 로직
        # 코인 거래를 시작한지 2시간이 경과했고, 매수중지 상태인 경우 진입
        if buy_logic_start - time.time() >= 60 * 60 * 2 and stop_buy:
            stop_loss_result = stop_loss_logic(upbit, target_coin, invest_balance, except_balance, 0.99)
        else:
            stop_loss_result = False

        # 손절한 경우
        if stop_loss_result:
            # 매수 로직을 종료한다
            break

        # # 순환매수매도 모드에 진입했는지 체크한다.
        # is_cycle_mode = check_cycle_mode(upbit, target_coin, invest_balance, except_balance)
        #
        # # 순환매 모드에 진입했다면
        # if is_cycle_mode:
        #     # 순환매 진행
        #     good_sell_at_cycle_mode(upbit, target_coin, interval, invest_balance, except_balance)

        # 구매중지가 안된 경우에만 매수 로직을 체크한다.
        # 구매중지는 잔고가 없는경우에만 Ture가 된다.
        if not stop_buy:
            # 매수 대상인지 체크에 필요한 변수 선언 및 값 지정
            check_result = dict(filter(lambda el: el[1] is True, check_purchase_target(target_coin, interval).items()))
            purchase_level = len(check_result)
            buy_sign = False
            if purchase_level == 4:
                buy_minute = 2
            elif purchase_level == 3:
                buy_minute = 5
            else:
                buy_minute = 7
            buy_term = 60 * buy_minute

            # 매수 신호가 2개이상 충족하는가
            if purchase_level >= 2:
                # 수익율이 0.2% 미만이 맞는가 0.2프로 미만인 경우에만 매수진행
                target_price = get_real_avg_buy_price(upbit, target_coin, invest_balance, except_balance) * 1.002
                now_price = pyupbit.get_current_price(target_coin)
                delay_for_normal_api()
                if now_price < target_price:
                    # 구매한 이력이 없는가
                    if buy_time == "":
                        buy_sign = True
                    # 구매까지의 충분한 시간이 경과했는가
                    elif time.time() - buy_time >= buy_term:
                        buy_sign = True

            # 매수 신호가 전달되는 경우
            if buy_sign:
                # 대상 코인을 바로 시장가 매수한다.
                buy_result = buy_target_coin(upbit, target_coin, invest_balance, except_balance, check_result)
                # 정상적으로 구매를 한경우
                if buy_result:
                    # 코인 구매 시간을 저장한다
                    buy_time = time.time()
                    stop_buy = False
                else:
                    log_print("잔고가 모두 소진되어 매수는 중지합니다.")
                    stop_buy = True
