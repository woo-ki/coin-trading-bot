# -*- coding:utf-8 -*-
import math
import time
import pyupbit
import methods

access = "9F2w4TJy72xoFimpg9XcPF1byOgk4BPVjYRU2Aeg"  # 본인 값으로 변경
secret = "BNwix0tO4IPIn4GzWcxqVnRxVxItxJPh4sm3DYj5"  # 본인 값으로 변경

# 업비트 객체를 만듭니다.
upbit = pyupbit.Upbit(access, secret)

while True:
    methods.log_print("투자 봇 가동")
    # 내 원화 잔고를 가져온다
    my_balance = int(upbit.get_balance("KRW"))

    # 투자금액 지정
    invest_rate = 0.1                               # 자산의 10%만 투자한다
    invest_min = 100000                             # 최소 10만원 이상 투자한다
    invest_balance = int(my_balance * invest_rate)  # 투자금 계산
    if invest_balance < invest_min:                 # 투자금이 최소 투자금보다 작은경우
        if my_balance < invest_min:                 # 투자원금이 최소 투자금보다 작은경우
            invest_balance = my_balance             # 투자금 = 원금 전체
        else:                                       # 투자원금이 최소 투자금보다 큰경우
            invest_balance = invest_min             # 투자금 = 최소 투자금
    methods.log_print("투자금 지정 완료: " + str(invest_balance) + "원")

    # 투자대상 선정(1시간봉 기준 2개의 거래량 1등)
    methods.log_print("투자 대상 선정 시작")
    target_coins = methods.get_top_coin_list("minute60", 10)
    target_coins_str = ""
    for target in target_coins:
        if target_coins_str == "":
            target_coins_str += str(target)
        else:
            target_coins_str += (", " + str(target))
    methods.log_print("투자 대상 선정 완료: " + target_coins_str)

    for target_coin in target_coins:
        methods.log_print("투자대상 단일화: " + str(target_coin))
        # 투자 대상 거래 수수료
        target_info = upbit.get_chance(target_coin)     # 투자 코인 시장정보
        buy_fees = float(target_info["bid_fee"])        # 투자 코인 매수 수수료
        sell_fees = float(target_info["ask_fee"])       # 투자 코인 매도 수수료

        while True:
            # 하락장, 상승장, 일반장 구분
            df_60 = pyupbit.get_ohlcv(target_coin, "minute60")  # 60분봉 정보
            rsi_14_before = methods.get_rsi(df_60, 14, -4)      # 3시간 전 rsi14 지표
            rsi_14_after = methods.get_rsi(df_60, 14, -2)       # 1시간 전 rsi14 지표
            condition = rsi_14_after / rsi_14_before            # 1시간 전 지표 / 4시간 전 지표(장 상황 체크기준)
            market_status = "normal"                            # 장 상태(일반장)
            if condition >= 1.1:
                market_status = "fire"                          # 장 상태(상승장) 체크기준이 1.1 이상인 경우
            elif condition < 0.95:
                market_status = "cold"                          # 장 상태(하락장) 체크기준이 0.95 이하인 경우
            methods.log_print("시장 상황: " + market_status)

            # 상황별 분봉 정보
            candle_interval = "minute5"     # 기본 분봉 5분봉
            df = pyupbit.get_ohlcv(target_coin, candle_interval, 200)
            candles = list()
            # 양봉, 음봉 분기 및 시가 종가 데이터 담기
            for i in range(-1, -21, -1):
                if df["close"][i] - df["open"][i] >= 0:
                    candle_type = "plus"
                else:
                    candle_type = "minus"
                temp = {
                    "index": df.index[i],
                    "candle_type": candle_type,
                    "open": df["open"][i],
                    "close": df["close"][i]
                }
                candles.append(temp)
            now_candle = candles[0]
            buy_sign = False

            now_rsi_14 = methods.get_rsi(df, 14, -1)
            comparison_rsi_14 = ""
            if now_candle["candle_type"] == "minus":
                buy_sign = False
            else:
                comparison_candle = ""
                near_minus_candle = ""
                near_minus_rsi_14 = float(0.0)
                comparison_rsi_14 = float(0.0)
                for i in range(1, len(candles)):
                    if candles[i]["candle_type"] == "minus":
                        if comparison_candle == "":
                            comparison_candle = candles[i]
                            near_minus_candle = candles[i]
                            comparison_rsi_14 = methods.get_rsi(df, 14, (i * -1 - 1))
                            near_minus_rsi_14 = methods.get_rsi(df, 14, (i * -1 - 1))
                        else:
                            if comparison_candle["open"] <= candles[i]["open"]:
                                comparison_candle = candles[i]
                                comparison_rsi_14 = methods.get_rsi(df, 14, (i * -1 - 1))
                            else:
                                break

                if near_minus_rsi_14 > 0 and comparison_rsi_14 > 0 and now_rsi_14 > 0:
                    if near_minus_rsi_14 / comparison_rsi_14 <= 0.75 and now_rsi_14 / near_minus_rsi_14 >= 1.1:
                        buy_sign = True

            # 매수로직
            if buy_sign:
                methods.log_print("매수로직을 시작합니다.")
                # 1회당 매수금액 설정
                budget_for_buy_once = invest_balance * 0.1                                          # 1회 매수 금액
                now_my_balance = int(upbit.get_balance("KRW"))                                      # 현재 잔고
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
                    buy_result = upbit.buy_market_order(target_coin, budget_for_buy_once)
                    methods.log_print("매수 성공: " + str(buy_result["price"]))
                    time.sleep(1)
                else:
                    methods.log_print("잔액부족 매수실패")
            else:
                methods.log_print("시장 상황이 적합하지 않습니다. 매수로직을 건너뜁니다.")

            # 매도로직(대상 코인을 매수한 경우에만 진입)
            if methods.is_has_coin(upbit.get_balances(), target_coin):
                methods.log_print("매도로직을 시작합니다.")
                is_break = False
                for coin in upbit.get_balances():
                    if "KRW-" + coin["currency"] != target_coin:
                        continue
                    # 목표 수익율 설정
                    target_revenue = 1.005
                    if market_status == "normal":
                        target_revenue = 1.005
                    elif market_status == "fire":
                        target_revenue = 1.02
                    elif market_status == "cold":
                        target_revenue = 1.002

                    target_price = float(coin["avg_buy_price"]) * target_revenue
                    if pyupbit.get_current_price(target_coin) >= target_price:
                        upbit.sell_market_order(coin, float(coin["balance"]))
                        methods.log_print("코인을 모두 판매했습니다. 10초 뒤 대상 선정을 다시 시작합니다.")
                        is_break = True
                    else:
                        methods.log_print("수익률에 도달하지 못했습니다. 10초 뒤 시장상황 분석 로직을 다시 시작합니다.")
            else:
                methods.log_print("코인을 구매하지 않았습니다. 10초 뒤 대상 선정을 다시 시작합니다.")
                is_break = True
            time.sleep(10)
            if is_break:
                break
