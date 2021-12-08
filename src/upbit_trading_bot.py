# -*- coding:utf-8 -*-
import time
import pyupbit
import methods

access = "9F2w4TJy72xoFimpg9XcPF1byOgk4BPVjYRU2Aeg"  # 본인 값으로 변경
secret = "BNwix0tO4IPIn4GzWcxqVnRxVxItxJPh4sm3DYj5"  # 본인 값으로 변경

# 업비트 객체를 만듭니다.
upbit = pyupbit.Upbit(access, secret)
methods.log_print("Upbit Auto Trading Bot 가동")

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
    except_balance = my_balance - invest_balance    # 투자예외 지정금 = 원화 잔고 - 투자금
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
        # 투자금에 코인을 구매하는데 사용한 비용을 더해준다. (정확한 평단가 관리 목적)
        balances = dict()
        for balance in upbit.get_balances():
            if balance["currency"] == "KRW":
                continue
            temp = {
                "balance": balance["balance"],
                "avg_buy_price": balance["avg_buy_price"]
            }
            balances["KRW-" + balance["currency"]] = temp
        for target_coin in target_coins:
            invest_balance += int(float(balances[target_coin]["balance"]) * float(balances[target_coin]["avg_buy_price"]))
        methods.log_print("보유 코인이 있습니다. 투자원금을 조정합니다: " + str(invest_balance) + "원")
        # 매도신호 on
        sell_sign = True
    # 보유 코인이 없는경우
    else:
        # 거래량 상위 코인 목록을 가져온다
        target_coins = methods.get_top_coin_list("minute60", 5)
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
            sell_result = methods.sell_logic(upbit, target_coin, invest_balance, except_balance)
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
    if buy_sign:
        # 이미 구매한 코인이 있는경우
        if sell_sign:
            # 타겟 코인들을 루프 돌면서
            for target_coin in target_coins:
                # 매수로직을 진행한다.
                methods.buy_logic(upbit, target_coin, "minute5", invest_balance, except_balance)

            # 보유한 코인을 모두 판매하고 나온경우
            # methods.log_print("보유한 코인을 모두 판매하였습니다. 봇을 다시 실행합니다.")
        # 구매한 코인이 없는경우
        else:
            # 거래 대상들을 돌면서 구매할만한 코인이 있는지 확인한다.
            for target_coin in target_coins:
                # 구매대상 있는지 검사 로직
                check_result = dict(filter(lambda el: el[1] is True, methods.check_purchase_target(target_coin, "minute5").items()))
                purchase_level = len(check_result)
                # 구매대상에 해당하는 경우
                if purchase_level >= 2:
                    # 매수로직 진입시간을 저장한다
                    buy_logic_start = time.time()
                    # 매수로직을 진행한다.
                    methods.buy_logic(upbit, target_coin, "minute5", invest_balance, except_balance, True, check_result)
                    # 매수로직이 종료된 시간이 최초 진입시간보다 5분 이상 경과했으면 봇을 다시 실행한다.
                    if time.time() - buy_logic_start >= 300:
                        break
            # 구매대상이 없거나 매수로직이 모두 끝난경우
            # methods.log_print("거래가 종료되었습니다. 봇을 다시 실행합니다.")
