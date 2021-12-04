#-*- coding:utf-8 -*-

import time
import pyupbit

access = "9F2w4TJy72xoFimpg9XcPF1byOgk4BPVjYRU2Aeg"          # 본인 값으로 변경
secret = "BNwix0tO4IPIn4GzWcxqVnRxVxItxJPh4sm3DYj5"          # 본인 값으로 변경
upbit = pyupbit.Upbit(access, secret)

while True:
    time.sleep(5)
    for ticker in pyupbit.get_tickers("KRW"):
        if ticker == "KRW-HUM":
            df = pyupbit.get_ohlcv(ticker, "minute5", 1)
            print(df)
            break
# target = "KRW-POWR"
# coin_now_price = pyupbit.get_current_price(target)
# coin_target_price = coin_now_price * 0.998
#
# balance_won = upbit.get_balance("KRW")
# print(pyupbit.get_tick_size(coin_target_price) * (balance_won / coin_target_price))
#
# print(upbit.buy_limit_order(target, pyupbit.get_tick_size(coin_target_price), (balance_won / coin_target_price)))

# my_coins = []
#
# for coin in upbit.get_balances():
#     ticker = coin["currency"]
#     if ticker == "KRW":
#         continue
#     temp = {
#         "currency": "KRW-" + coin["currency"],
#         "balance": float(coin["balance"]),
#         "avg_buy_price": float(coin["avg_buy_price"]),
#         "now_price": pyupbit.get_current_price("KRW-" + coin["currency"])
#     }
#     temp["revenue"] = (temp["now_price"] - temp["avg_buy_price"]) / temp["avg_buy_price"] * 100.0
#     my_coins.append(temp)
#
# print(my_coins)
# for coin in my_coins:
#     print(upbit.sell_limit_order(coin["currency"], pyupbit.get_tick_size(coin["avg_buy_price"] * 1.03), 25))


# coins = pyupbit.get_tickers(fiat="KRW")


# for coin in coins:
#     print(coin, pyupbit.get_current_price(coin))
#     time.sleep(0.06)
#
# if coin == "KRW-BTC" or coin == "KRW-SAND":
#     upbit.buy_market_order(coin, 5000)

# btc_balance = upbit.get_balance("KRW-BTC")
# print(btc_balance)

# print(upbit.sell_market_order("KRW-BTC", btc_balance))
