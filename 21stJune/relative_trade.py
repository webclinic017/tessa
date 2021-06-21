from helpers import get_timestamp
from pandas import DataFrame
from csv import writer
from jugaad_trader import Zerodha
from talib import RSI, WMA, EMA
from _thread import start_new_thread
import talib
import numpy as np
import pandas as pd
import pytz
from datetime import datetime, timedelta
from dateutil.tz import tzoffset
import csv
from helpers import *
import logging

print("Om Namahshivaya:")
logging.basicConfig(filename='tradebook.log', level=logging.DEBUG)


class Ticker:
    def __init__(self, instrument_token, tradingsymbol) -> None:
        self.instrument_token = instrument_token
        self.tradingsymbol = tradingsymbol
        self.tick_store = []  # store the last_traded_prices
        self.volume = 0  # store the volume of the current_candle
        self.candles = DataFrame(kite.historical_data(
            instrument_token, previous_session_date + timedelta(hours=15), previous_session_date + timedelta(hours=15, minutes=21), "minute"))
        self.candle_writer = writer(open(tradingsymbol + ".csv", "w"))
        self.tick_writer = writer(open(tradingsymbol + "_ticks.csv", "w"))
        self.open_trade = False
        self.log = open(self.tradingsymbol + "_log.txt", "w")

    def set_relative_ticker(self, relative_ticker):
        self.relative_ticker = relative_ticker

    def get_relative_ticker(self):
        return self.relative_ticker

    def write_tick(self, tick) -> None:
        ltp = tick['last_price']
        ohlc = tick['ohlc']
        last_quantity = tick['last_quantity']

        self.tick_writer.writerow(
            [get_timestamp(), ltp, last_quantity, ohlc])
        self.tick_store.append(ltp)
        self.volume += last_quantity
        if len(self.tick_store) == 161:
            self.write_candle()

    def write_candle(self) -> None:
        candle_open = self.tick_store[0]
        candle_high = max(self.tick_store)
        candle_low = min(self.tick_store)
        candle_close = self.tick_store[-1]
        candle_volume = self.volume
        candle_data = [get_timestamp(), candle_open, candle_high,
                       candle_low, candle_close, candle_volume]

        candle_dataframe_length = len(self.candles)
        self.candles.loc[candle_dataframe_length] = candle_data
        self.candle_writer.writerow(candle_data)

        self.tick_store = []
        self.volume = 0
        start_new_thread(self.on_candle, tuple(self.instrument_token))

    def get_last_candle(self):
        return self.candles.iloc[-1]

    def get_penultimate_candle(self):
        return self.candles.iloc[-2]


kite = Zerodha()


# Set access token loads the stored session.
# Name chosen to keep it compatible with kiteconnect.
kite.set_access_token()

today = datetime.today()
banknifty_instrument_token = 260105

historical = kite.historical_data(
    banknifty_instrument_token, today - timedelta(days=314), today, "day")
historical_data = DataFrame(historical)

historical_data["ema210"] = EMA(historical_data.close, timeperiod=210)
historical_data["ema21"] = EMA(historical_data.close, timeperiod=21)

previous_session_ohlc = historical[-1]
previous_day_cadle = historical_data.iloc[-1]

previous_session_date = previous_session_ohlc['date']
banknifty_close = int(round(previous_session_ohlc['close'], -2))

if banknifty_close >= previous_day_cadle.ema210:
    print("Long Term Trend: Positive")
else:
    print("Long Term Trend: Negative")

if banknifty_close >= previous_day_cadle.ema21:
    print("Short Term Trend: Positive")
else:
    print("Short Term Trend: Negative")

banknifty_high = int(round(previous_session_ohlc['high'], -2))
banknifty_low = int(round(previous_session_ohlc['low'], -2))

nfo_instruments = pd.DataFrame(kite.instruments("NFO"))

banknifty_instruments = nfo_instruments.loc[(
    nfo_instruments.name == 'BANKNIFTY')]

tickertape = {}
strikes = []

monthly_options = banknifty_instruments.loc[banknifty_instruments.strike == banknifty_close, [
    'instrument_token', 'tradingsymbol']].head(2)
call_instrument_token, call_tradingsymbol = monthly_options.values[0]
put_instrument_token, put_tradingsymbol = monthly_options.values[1]
tickertape[call_instrument_token] = call_tradingsymbol
tickertape[put_instrument_token] = put_tradingsymbol
watchlist = (call_instrument_token, put_instrument_token)

tickers = {}

tickers[call_instrument_token] = Ticker(
    call_instrument_token, call_tradingsymbol)
tickers[put_instrument_token] = Ticker(put_instrument_token, put_tradingsymbol)

tickers[call_instrument_token].set_relative_ticker(
    tickers[put_instrument_token])
tickers[put_instrument_token].set_relative_ticker(
    tickers[call_instrument_token])


tradebook = open('tradebook.txt', "w")
orderbook = open("orderbook.txt", "w")


instrument_token = ''
ltp = ''
open_positions = True
open_trades = []


print(f"Tickertape: {tickertape}")
kws = kite.ticker()


def on_candle(instrument_token):
    ticker = tickers[instrument_token]

    candles = ticker.candles.copy()
    relative_last_candle = tickers[instrument_token].get_relative_ticker(
    ).get_last_candle()

    candles['rsi13'] = RSI(candles['close'], timeperiod=13)
    candles['rsi21'] = RSI(candles['close'], timeperiod=21)
    candles['ema21'] = EMA(candles['close'], timeperiod=21)
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

                            try:

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
                                open_trades.append(instrument_token)
                                print(
                                    f"Triple Supertrend Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")
                                orderbook.write(
                                    f"\nTriple Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

                            except:
                                print(
                                    f"Eroor placing Triple Supertrend Buy Order for {tradingsymbol} succesfully orders {buy_order_id}")

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
                            ticker.log.write(
                                f"\nTriple Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

                            tradebook.write(
                                f"\nTriple Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    if instrument_token not in open_trades:
        if not relative_last_candle.STX_21:
            if not relative_last_candle.STX_13:
                if not relative_last_candle.STX_8:
                    if last_candle.STX_13:
                        if last_candle.STX_8:

                            try:

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
                                open_trades.append(instrument_token)
                                print(
                                    f"Relative Supertrend Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")
                                orderbook.write(
                                    f"\nRelative Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

                            except:
                                print(
                                    f"Error placing Relative Supertrend Buy Order for {tradingsymbol} succesfully orders {buy_order_id}")

                            print(
                                f"Relative Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                            ticker.log.write(
                                f"\nRelative Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                            tradebook.write(
                                f"\nRelative Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    if instrument_token not in open_trades:
        if penultimate_candle.rsi21 < 21:
            if last_candle.rsi21 >= 21:
                if penultimate_candle.rsi13 < 13:
                    if last_candle.rsi13 >= 13:

                        try:

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
                            open_trades.append(instrument_token)
                            print(
                                f"Triple RSI Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")
                            orderbook.write(
                                f"\nTriple RSI: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                        except:
                            print(
                                f"Error placing Triple RSI Buy Order for {tradingsymbol} succesfully orders {buy_order_id}")
                        print(
                            f"Triple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                        ticker.log.write(
                            f"\nTriple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

                        tradebook.write(
                            f"\nTriple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    elif instrument_token in open_trades:
        if not super_candle.STX_13:

            try:

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
                open_trades.remove(instrument_token)
                print(
                    f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                orderbook.write(
                    f"\nTriple Supertrend: Supertrend 13 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
            except:
                print(
                    f"Error Triple Supertrend 13 placing Sell Order for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")

            print(
                f"Triple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
            ticker.log.write(
                f"\nTriple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
            tradebook.write(
                f"\nTriple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    elif instrument_token in open_trades:
        if relative_last_candle.STX_13:
            if relative_last_candle.STX_8:

                try:

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
                    open_trades.remove(instrument_token)
                    print(
                        f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                    orderbook.write(
                        f"\nRelative Supertrend: Supertrend 13 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                except:
                    print(
                        f"Error placing Sell Order for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                print(
                    f"Relative Double Supertrend Sell signal for {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                ticker.log.write(
                    f"\nRelative Double Supertrend Sell signal for {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                tradebook.write(
                    f"\nRelative Double Supertrend Sell signal for {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

    elif instrument_token in open_trades:
        if penultimate_candle.rsi13 > 87:
            if last_candle.rsi13 <= 87:

                try:

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
                    open_trades.remove(instrument_token)
                    print(
                        f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                    orderbook.write(
                        f"\nTriple RSI: RSI 13 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                except:
                    print(
                        f"Error placing Sell Order for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                print(
                    f"Triple RSI 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                ticker.log.write(
                    f"\nTriple RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                tradebook.write(
                    f"\nTriple RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

    elif instrument_token in open_trades:
        if relative_last_candle.rsi21 < 21:
            if relative_last_candle.rsi21 >= 21:

                try:

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
                    open_trades.remove(instrument_token)
                    print(
                        f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                    orderbook.write(
                        f"\nRelative RSI: RSI 21 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                except:
                    print(
                        f"Error placing Sell Order for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                print(
                    f"Triple Relative RSI 21 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                ticker.log.write(
                    f"\nTriple Relative RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                tradebook.write(
                    f"\nTriple Relative RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")


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
