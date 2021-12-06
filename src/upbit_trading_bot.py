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
    # methods.log_print("투자 봇 가동")
    # 내 원화 잔고를 가져온다
    my_balance = int(upbit.get_balance("KRW"))

    # 투자금액 지정
    invest_rate = 0.2                               # 자산의 20%만 투자한다
    invest_min = 100000                             # 최소 10만원 이상 투자한다
    invest_balance = int(my_balance * invest_rate)  # 투자금 계산
    if invest_balance < invest_min:                 # 투자금이 최소 투자금보다 작은경우
        if my_balance < invest_min:                 # 투자원금이 최소 투자금보다 작은경우
            invest_balance = my_balance             # 투자금 = 원금 전체
        else:                                       # 투자원금이 최소 투자금보다 큰경우
            invest_balance = invest_min             # 투자금 = 최소 투자금
    now_balance = invest_balance
    # methods.log_print("투자금 지정 완료: " + str(invest_balance) + "원")

    # 투자대상 선정(1시간봉 기준 2개의 거래량 상위 or 보유코인)
    # methods.log_print("거래 대상 선정 시작")

    # 내 보유 코인을 가져온다
    my_coins = methods.get_my_coins(upbit)

    # 매수 매도 로직 실행여부
    sell_sign = False
    buy_sign = False

    # 보유 코인이 있는경우
    if len(my_coins) > 0:
        # 거래대상 코인 = 보유 코인
        target_coins = my_coins
        # 매도신호 on
        sell_sign = True
    # 보유 코인이 없는경우
    else:
        # 거래량 상위 코인 목록을 가져온다
        target_coins = methods.get_top_coin_list("minute60", 10)
    # 거래대상 코인 목록을 출력한다
    target_coins_str = ""
    for target in target_coins:
        if target_coins_str == "":
            target_coins_str += str(target)
        else:
            target_coins_str += (", " + str(target))
    # methods.log_print("거래 대상 목록 선정 완료: " + target_coins_str)

    # 매도신호가 들어온 경우
    if sell_sign:
        # 타겟 코인들을 루프 돌면서
        for target_coin in target_coins:
            # 매도로직을 실행해준다.
            sell_result = methods.sell_logic(upbit, target_coin, invest_balance, now_balance)
            # 매도가 완료되었다면
            if sell_result:
                # 거래 대상 목록에서 매도한 코인을 제외한다.
                target_coins.remove(target_coin)

    # 거래 대상 목록이 다 사라진 경우
    if len(target_coins) == 0:
        # 거래 대상 선정부터 다시한다.
        continue
    # 거래 대상이 남아있는 경우
    else:
        # 매수 신호를 보낸다.
        buy_sign = True

    # 매수 신호가 들어온 경우
    # if buy_sign:
        # 이미 구매한 코인이 있는경우
        # if sell_sign:
            # 매수로직을 진행한다.
            # 매수로직에는 매도로직이 함께한다
            # 매수간 텀은 최소 5분이상 둔다.
            # 매수로직은 대상체크 메소드와 구매 메소드 2개로 이루어진다.
            # 보유한 코인을 모두 다 판매한 경우 매수로직이 종료된다.
            # methods.log_print("매수로직 짜야함")

            # 보유한 코인을 모두 판매하고 나온경우
            # methods.log_print("보유한 코인을 모두 판매하였습니다. 봇을 다시 실행합니다.")
        # 구매한 코인이 없는경우
        # else:
            # 거래 대상들을 돌면서 구매할만한 코인이 있는지 확인한다.
            # for target_coin in target_coins:
                # 구매대상 있는지 검사 로직
                # purchase_check = methods.check_purchase_target()
                # 구매대상에 해당하는 경우
                # if purchase_check:
                    # 해당 코인을 루프돌며 거래하는 로직으로 들어간다
                    # methods.print('매수로직 짜야행')
                # 구매대상에 해당하지 않는 경우
                # else:
                #     continue
            # 루프를 다 돌았으나 구매대상이 없는경우 => 다시 최초 로직으로
            # methods.log_print("구매에 적합한 대상이 없습니다. 봇을 다시 실행합니다.")

        # ------------------------------------------------------------------ 아래 참조해서 매수로직 다시짜자

        # last_buy_time = time.time()
        # while True:
        #
        #
        #     # 상황별 분봉 정보
        #     candle_interval = "minute5"     # 기본 분봉 5분봉
        #     df = pyupbit.get_ohlcv(target_coin, candle_interval, 200)
        #     candles = list()
        #     # 양봉, 음봉 분기 및 시가 종가 데이터 담기
        #     for i in range(-1, -21, -1):
        #         if df["close"][i] - df["open"][i] >= 0:
        #             candle_type = "plus"
        #         else:
        #             candle_type = "minus"
        #         temp = {
        #             "index": df.index[i],
        #             "candle_type": candle_type,
        #             "open": df["open"][i],
        #             "close": df["close"][i]
        #         }
        #         candles.append(temp)
        #     now_candle = candles[0]
        #     buy_sign = False
        #
        #     now_rsi_14 = methods.get_rsi(df, 14, -1)
        #     comparison_rsi_14 = ""
        #     if now_candle["candle_type"] == "minus":
        #         buy_sign = False
        #     else:
        #         comparison_candle = ""
        #         near_minus_candle = ""
        #         near_minus_rsi_14 = float(0.0)
        #         comparison_rsi_14 = float(0.0)
        #         for i in range(1, len(candles)):
        #             if candles[i]["candle_type"] == "minus":
        #                 if comparison_candle == "":
        #                     comparison_candle = candles[i]
        #                     near_minus_candle = candles[i]
        #                     comparison_rsi_14 = methods.get_rsi(df, 14, (i * -1 - 1))
        #                     near_minus_rsi_14 = methods.get_rsi(df, 14, (i * -1 - 1))
        #                 else:
        #                     if comparison_candle["open"] <= candles[i]["open"]:
        #                         comparison_candle = candles[i]
        #                         comparison_rsi_14 = methods.get_rsi(df, 14, (i * -1 - 1))
        #                     else:
        #                         break
        #
        #         if near_minus_rsi_14 > 0 and comparison_rsi_14 > 0 and now_rsi_14 > 0:
        #             if near_minus_rsi_14 / comparison_rsi_14 <= 0.75 and now_rsi_14 / near_minus_rsi_14 >= 1.1:
        #                 buy_sign = True
        #
        #     # 투자 대상 거래 수수료
        #     target_info = upbit.get_chance(target_coin)     # 투자 코인 시장정보
        #     buy_fees = float(target_info["bid_fee"])        # 투자 코인 매수 수수료
        #     sell_fees = float(target_info["ask_fee"])       # 투자 코인 매도 수수료
        #     # 매수로직
        #     if buy_sign:
        #         methods.log_print("매수로직을 시작합니다.")
        #         # 1회당 매수금액 설정
        #         budget_for_buy_once = invest_balance * 0.1                                          # 1회 매수 금액
        #         now_my_balance = int(upbit.get_balance("KRW"))                                      # 현재 잔고
        #         min_buy_price = float(target_info["market"]["bid"]["min_total"])                    # 최소 매수 금액
        #
        #         # 현재 잔고가 최소주문금액 이상인 경우에만 매수 로직 실행
        #         if now_my_balance >= min_buy_price * (1 + buy_fees):
        #             # 현재 잔고가 최소 주문금액 2회를 할 수 없는경우
        #             if now_my_balance < math.ceil(min_buy_price * (1 + buy_fees)) * 2:
        #                 budget_for_buy_once = math.floor(now_my_balance / (1 + buy_fees))           # 1회 매수 금액 = 현재 잔고 전액
        #             else:
        #                 budget_for_buy_once = math.floor(budget_for_buy_once / (1 + buy_fees))      # 수수료 공제포함 1회 주문금액
        #                 # 1회 매수금액이 최소 주문금액보다 작은경우
        #                 if budget_for_buy_once < min_buy_price:
        #                     budget_for_buy_once = min_buy_price                                     # 1회 매수 금액 = 최소 주문 금액
        #                 # 1회 매수를 한 이후 잔액이 최소 주문금액보다 작은경우
        #                 if now_my_balance - (budget_for_buy_once * (1 + buy_fees)) < min_buy_price:
        #                     budget_for_buy_once = math.floor(now_my_balance / (1 + buy_fees))       # 1회 매수 금액 = 수수료 공제 포함 현재 잔고 전액
        #             buy_result = upbit.buy_market_order(target_coin, budget_for_buy_once)
        #             methods.log_print("매수 성공: " + str(buy_result["price"]))
        #             time.sleep(1)
        #         else:
        #             methods.log_print("잔액부족 매수실패")
        #     else:
        #         methods.log_print("시장 상황이 적합하지 않습니다. 매수로직을 건너뜁니다.")


