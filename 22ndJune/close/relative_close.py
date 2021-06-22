from datetime import datetime
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
            instrument_token, previous_session_date + timedelta(hours=15), datetime.now().replace(second=0, microsecond=0), "3minute"))
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
        start_new_thread(on_candle, (self.instrument_token,))

    def get_last_candle(self):
        return self.candles.iloc[-1]

    def get_penultimate_candle(self):
        return self.candles.iloc[-2]

    def get_candles(self):
        return self.candles


def get_timestamp():
    return datetime.now(tzoffset(None, 19800)).isoformat(' ', 'seconds')


def get_ltp(instrument_token):
    return kite.ltp(instrument_token)[str(instrument_token)]['last_price']

# Source for tech indicator : https://github.com/arkochhar/Technical-Indicators/blob/master/indicator/indicators.py


def ExponentialMovingAverage(df, base, target, period, alpha=False):
    """
    Function to compute Exponential Moving Average (EMA)
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        base : String indicating the column name from which the EMA needs to be computed from
        target : String indicates the column name to which the computed data needs to be stored
        period : Integer indicates the period of computation in terms of number of candles
        alpha : Boolean if True indicates to use the formula for computing EMA using alpha (default is False)
    Returns :
        df : Pandas DataFrame with new column added with name 'target'
    """

    con = pd.concat([df[:period][base].rolling(
        window=period).mean(), df[period:][base]])

    if (alpha == True):
        # (1 - alpha) * previous_val + alpha * current_val where alpha = 1 / period
        df[target] = con.ewm(alpha=1 / period, adjust=False).mean()
    else:
        # ((current_val - previous_val) * coeff) + previous_val where coeff = 2 / (period + 1)
        df[target] = con.ewm(span=period, adjust=False).mean()

    df[target].fillna(0, inplace=True)
    return df


def ATR(df, period, ohlc=['open', 'high', 'low', 'close']):
    """
    Function to compute Average True Range (ATR)
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
    Returns :
        df : Pandas DataFrame with new columns added for
            True Range (TR)
            ATR (ATR_$period)
    """
    atr = 'ATR_' + str(period)

    # Compute true range only if it is not computed and stored earlier in the df
    if not 'TR' in df.columns:
        df['h-l'] = df[ohlc[1]] - df[ohlc[2]]
        df['h-yc'] = abs(df[ohlc[1]] - df[ohlc[3]].shift())
        df['l-yc'] = abs(df[ohlc[2]] - df[ohlc[3]].shift())

        df['TR'] = df[['h-l', 'h-yc', 'l-yc']].max(axis=1)

        df.drop(['h-l', 'h-yc', 'l-yc'], inplace=True, axis=1)

    # Compute ExponentialMovingAverage of true range using ATR formula after ignoring first row
    ExponentialMovingAverage(df, 'TR', atr, period, alpha=True)

    return df


supertrend_period = 21
supertrend_multiplier = 3


def SUPERTREND(df, period=supertrend_period, multiplier=supertrend_multiplier, ohlc=['open', 'high', 'low', 'close']):
    """
    Function to compute SUPERTREND
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        multiplier : Integer indicates value to multiply the ATR
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
    Returns :
        df : Pandas DataFrame with new columns added for
            True Range (TR), ATR (ATR_$period)
            SUPERTREND (ST_$period_$multiplier)
            SUPERTREND Direction (STX_$period_$multiplier)
    """

    ATR(df, period, ohlc=ohlc)
    atr = 'ATR_' + str(period)
    st = 'ST_' + str(period)  # + '_' + str(multiplier)
    stx = 'STX_' + str(period)  # + '_' + str(multiplier)

    """
    SUPERTREND Algorithm :
        BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
        BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR
        FINAL UPPERBAND = IF( (Current BASICUPPERBAND < Previous FINAL UPPERBAND) or (Previous Close > Previous FINAL UPPERBAND))
                            THEN (Current BASIC UPPERBAND) ELSE Previous FINALUPPERBAND)
        FINAL LOWERBAND = IF( (Current BASIC LOWERBAND > Previous FINAL LOWERBAND) or (Previous Close < Previous FINAL LOWERBAND))
                            THEN (Current BASIC LOWERBAND) ELSE Previous FINAL LOWERBAND)
        SUPERTREND = IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close <= Current FINAL UPPERBAND)) THEN
                        Current FINAL UPPERBAND
                    ELSE
                        IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close > Current FINAL UPPERBAND)) THEN
                            Current FINAL LOWERBAND
                        ELSE
                            IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close >= Current FINAL LOWERBAND)) THEN
                                Current FINAL LOWERBAND
                            ELSE
                                IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close < Current FINAL LOWERBAND)) THEN
                                    Current FINAL UPPERBAND
    """

    # Compute basic upper and lower bands
    df['basic_ub'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 + multiplier * df[atr]
    df['basic_lb'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 - multiplier * df[atr]

    # Compute final upper and lower bands
    df['final_ub'] = 0.00
    df['final_lb'] = 0.00
    for i in range(period, len(df)):
        df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or \
            df[ohlc[3]].iat[i - 1] > df['final_ub'].iat[i - 1] else \
            df['final_ub'].iat[i - 1]
        df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or \
            df[ohlc[3]].iat[i - 1] < df['final_lb'].iat[i - 1] else \
            df['final_lb'].iat[i - 1]

    # Set the SUPERTREND value
    df[st] = 0.00
    for i in range(period, len(df)):
        df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[
            i] <= df['final_ub'].iat[i] else \
            df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[i] > \
            df['final_ub'].iat[i] else \
            df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] >= \
            df['final_lb'].iat[i] else \
            df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] < \
            df['final_lb'].iat[i] else 0.00

        # Mark the trend direction up/down
    df[stx] = np.where((df[st] > 0.00), np.where(
        (df[ohlc[3]] < df[st]), False, True), np.NaN)

    # Remove basic and final bands from the columns
    df.drop(['basic_ub', 'basic_lb', 'final_ub',
            'final_lb'], inplace=True, axis=1)

    df.fillna(0, inplace=True)
    return df


kite = Zerodha()


# Set access token loads the stored session.
# Name chosen to keep it compatible with kiteconnect.
kite.set_access_token()

today = datetime.today()
banknifty_instrument_token = 260105

historical = kite.historical_data(
    banknifty_instrument_token, today - timedelta(days=314), today-timedelta(days=1), "day")
historical_data = DataFrame(historical)


historical_data["ema210"] = EMA(historical_data.close, timeperiod=210)
historical_data["ema21"] = EMA(historical_data.close, timeperiod=21)

previous_session_ohlc = historical[-1]


previous_day_candle = historical_data.iloc[-1]

previous_session_date = previous_session_ohlc['date'].replace(tzinfo=None)
banknifty_close = int(round(previous_day_candle['close'], -2))

if banknifty_close >= previous_day_candle.ema210:
    print("Long Term Trend: Positive")
else:
    print("Long Term Trend: Negative")

if banknifty_close >= previous_day_candle.ema21:
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
    'instrument_token', 'tradingsymbol']].head(7)
call_instrument_token, call_tradingsymbol = monthly_options.values[5]
put_instrument_token, put_tradingsymbol = monthly_options.values[6]
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

    candles = ticker.get_candles().copy()
    relative_candles = tickers[instrument_token].get_relative_ticker(
    ).get_candles().copy()

    candles['rsi13'] = RSI(candles['close'], timeperiod=13)
    candles['rsi21'] = RSI(candles['close'], timeperiod=21)
    candles['ema21'] = EMA(candles['close'], timeperiod=21)
    candles = SUPERTREND(candles, period=21, multiplier=3)
    candles = SUPERTREND(candles, period=13, multiplier=2)
    candles = SUPERTREND(candles, period=8, multiplier=1)

    penultimate_candle = candles.iloc[-2]
    last_candle = candles.iloc[-1]
    tradingsymbol = tickertape[instrument_token]

    relative_candles['rsi13'] = RSI(relative_candles['close'], timeperiod=13)
    relative_candles['rsi21'] = RSI(relative_candles['close'], timeperiod=21)
    relative_candles['ema21'] = EMA(relative_candles['close'], timeperiod=21)
    relative_candles = SUPERTREND(relative_candles, period=21, multiplier=3)
    relative_candles = SUPERTREND(relative_candles, period=13, multiplier=2)
    relative_candles = SUPERTREND(relative_candles, period=8, multiplier=1)

    last_relative_candle = relative_candles.iloc[-1]
    penultimate_relative_candle = relative_candles.iloc[-2]

    try:
        if instrument_token not in open_trades:
            if not penultimate_candle.STX_13:
                if not penultimate_candle.STX_8:
                    if last_candle.STX_21:
                        if last_candle.STX_13:
                            if last_candle.STX_8:

                                try:

                                    last_traded_price = get_ltp(
                                        instrument_token)
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
            if not last_relative_candle.STX_21:
                if not last_relative_candle.STX_13:
                    if not last_relative_candle.STX_8:
                        if last_candle.STX_13:
                            if last_candle.STX_8:

                                try:

                                    last_traded_price = get_ltp(
                                        instrument_token)
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

            if not last_relative_candle.STX_13:
                if not last_relative_candle.STX_8:
                    if last_candle.STX_13:
                        if last_candle.STX_8:

                            try:

                                last_traded_price = get_ltp(
                                    instrument_token)
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
            if not last_candle.STX_13:

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
            if last_relative_candle.STX_13:
                if last_relative_candle.STX_8:

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
            if last_relative_candle.rsi21 < 21:
                if last_relative_candle.rsi21 >= 21:

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
    except:
        print("Error in execution")
        pass


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
