from talib import RSI, WMA
from _thread import start_new_thread
import talib
import numpy as np
import pandas as pd
import pytz
from datetime import datetime, timedelta
from dateutil.tz import tzoffset
import csv
from ticker import Ticker
from helpers import *
from helpers import get_ltp, get_timestamp
from ticker import *

print("Om Namahshivaya:")


instrument_token = ''
ltp = ''
open_positions = True
open_trades = []


print(f"Tickertape: {tickertape}")
kws = kite.ticker()


def on_candle(instrument_tokenss):

    
    candles = tickers[instrument_token].candles.copy()
    relative_last_candle = tickers[instrument_token].get_relative_ticker(
    ).get_last_candle()

    candles['rsi13'] = RSI(candles['close'], timeperiod=13)
    candles['rsi21'] = RSI(candles['close'], timeperiod=21)
    candles['ema21'] = talib.EMA(candles['close'], timeperiod=21)
    supertrend_df = SUPERTREND(candles, period=21, multiplier=3)
    supertrend_df = SUPERTREND(supertrend_df, period=13, multiplier=2)
    supertrend_df = SUPERTREND(supertrend_df, period=8, multiplier=1)

    penultimate_candle = candles.iloc[-2]
    last_candle = candles.iloc[-1]
    tradingsymbol = tickertape[instrument_token]

    super_candle = supertrend_df.iloc[-1]
    penultimate_super_candle = supertrend_df.iloc[-2]

    if instrument_token not in open_trades:
        if not penultimate_super_candle.STX_13:
            if not penultimate_super_candle.STX_8:
                if super_candle.STX_21:
                    if super_candle.STX_13:
                        if super_candle.STX_8:
                            open_trades.append(instrument_token)
                            last_traded_price = get_ltp(instrument_token)
                            timestamp = get_timestamp()
                            buy_order_id = kite.place_order(tradingsymbol=tradingsymbol,
                                                            exchange=kite.EXCHANGE_NFO,
                                                            transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                            quantity=25,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_NRML,
                                                            variety=kite.VARIETY_REGULAR,
                                                            price=last_traded_price,
                                                            )
                            print(
                                f"Triple Supertrend Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")

                            # stoploss_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
                        #         exchange=kite.EXCHANGE_NFO,
                        #         transaction_type=kite.TRANSACTION_TYPE_SELL,
                        #         quantity=25,
                        #         order_type=kite.ORDER_TYPE_SL,
                        #         product=kite.PRODUCT_NRML,
                        #         variety=kite.VARIETY_REGULAR,
                            #         trigger_price=last_traded_price-21,
                        #         price=last_traded_price-21,
                        #         )
                            # print(f"Sell Order placed for {tradingsymbol} succesfully orders {stoploss_order_id}")

                            print(
                                f"Triple Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                            orderbook.write(
                                f"\nTriple Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                            tradebook.write(
                                f"\nTriple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    if instrument_token not in open_trades:
        if not relative_last_candle.STX_21:
            if not relative_last_candle.STX_13:
                if not relative_last_candle.STX_8:
                    if last_candle.STX_13:
                        if last_candle.STX_8:
                            buy_order_id = kite.place_order(tradingsymbol=tradingsymbol,
                                                            exchange=kite.EXCHANGE_NFO,
                                                            transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                            quantity=25,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_NRML,
                                                            variety=kite.VARIETY_REGULAR,
                                                            price=last_traded_price,
                                                            )
                            print(
                                f"Triple Supertrend Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")



    if instrument_token not in open_trades:
                if penultimate_candle.rsi21 < 21:
                    if last_candle.rsi21 >= 21:
                        if penultimate_candle.rsi13 < 13:
                            if last_candle.rsi13 >= 13:
                                open_trades.append(instrument_token)
                                last_traded_price = get_ltp(instrument_token)
                                timestamp = get_timestamp()
                                buy_order_id = kite.place_order(tradingsymbol=tradingsymbol,
                                                                exchange=kite.EXCHANGE_NFO,
                                                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                quantity=25,
                                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                                product=kite.PRODUCT_NRML,
                                                                variety=kite.VARIETY_REGULAR,
                                                                price=last_traded_price,
                                                                )
                                print(
                                    f"Triple RSI Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")

                                print(
                                    f"Triple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                                orderbook.write(
                                    f"\nTriple RSI: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                                tradebook.write(
                                    f"\nTriple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                              
    elif instrument_token in open_trades:
        if not super_candle.STX_13:
            open_trades.remove(instrument_token)
            last_traded_price = get_ltp(instrument_token)
            timestamp = get_timestamp()
            sell_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
                                             exchange=kite.EXCHANGE_NFO,
                                             transaction_type=kite.TRANSACTION_TYPE_SELL,
                                             quantity=25,
                                             order_type=kite.ORDER_TYPE_LIMIT,
                                             product=kite.PRODUCT_NRML,
                                             variety=kite.VARIETY_REGULAR,
                                             price=last_traded_price,
                                             )
            print(
                f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")

            print(
                f"Triple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
            orderbook.write(
                f"\nTriple Supertrend: Supertrend 13 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
            tradebook.write(
                f"\nTriple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    elif instrument_token in open_trades:
        if relative_last_candle.STX_13:
            if relative_last_candle.STX_13:
                sell_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
                                                 exchange=kite.EXCHANGE_NFO,
                                                 transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                 quantity=25,
                                                 order_type=kite.ORDER_TYPE_LIMIT,
                                                 product=kite.PRODUCT_NRML,
                                                 variety=kite.VARIETY_REGULAR,
                                                 price=last_traded_price,
                                                 )
                print(
                    f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")

    elif instrument_token in open_trades:
        if penultimate_candle.rsi21 > 79:
            if last_candle.rsi21 <= 79:
                open_trades.remove(instrument_token)
                last_traded_price = get_ltp(instrument_token)
                timestamp = get_timestamp()
                sell_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
                                                 exchange=kite.EXCHANGE_NFO,
                                                 transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                 quantity=25,
                                                 order_type=kite.ORDER_TYPE_LIMIT,
                                                 product=kite.PRODUCT_NRML,
                                                 variety=kite.VARIETY_REGULAR,
                                                 price=last_traded_price,
                                                 )
                print(
                    f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                print(
                    f"Triple RSI 21 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                orderbook.write(
                    f"\nTriple RSI: RSI 21 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                tradebook.write(
                    f"\nTriple RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
           

def on_ticks(ws, ticks):

    # Callback to receive ticks.
    for tick in ticks:

        instrument_token = tick['instrument_token']
        tickers[instrument_token].write_tick(tick)


def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe(watchlist)

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_QUOTE, watchlist)


def on_close(ws, code, reason):
    # On connection close stop the event loop.
    # Reconnection will not happen after executing `ws.stop()`
    for instrument_token in watchlist:
        tickers[instrument_token].candles.to_csv(
            tickertape[instrument_token]+".csv", index=False)
    tradebook.close()
    orderbook.close()
    ws.stop()


# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()
