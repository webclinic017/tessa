from kiteconnect import ticker
from talib import RSI, WMA
from _thread import start_new_thread
import talib
import numpy as np
from pprint import pprint
from jugaad_trader import Zerodha
import pandas as pd
import pytz
from datetime import datetime, timedelta
import csv
from pandas.tseries.offsets import BDay

print("Om Namahshivaya:")


# historical_data = pd.DataFrame(kite.historical_data(
#     260105, today - timedelta(days=34), today, "day"))

# df = SuperTrend(historical_data, period=21, multiplier=3,
#                 ohlc=['open', 'high', 'low', 'close'])
# df = SuperTrend(historical_data, period=13, multiplier=2,
#                 ohlc=['open', 'high', 'low', 'close'])
# df = SuperTrend(historical_data, period=8, multiplier=1,
#                 ohlc=['open', 'high', 'low', 'close'])
# print(df)


# Source for tech indicator : https://github.com/arkochhar/Technical-Indicators/blob/master/indicator/indicators.py
def EMA(df, base, target, period, alpha=False):
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

    # Compute EMA of true range using ATR formula after ignoring first row
    EMA(df, 'TR', atr, period, alpha=True)

    return df


supertrend_period = 21
supertrend_multiplier = 3


def SuperTrend(df, period=supertrend_period, multiplier=supertrend_multiplier, ohlc=['open', 'high', 'low', 'close']):
    """
    Function to compute SuperTrend
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        multiplier : Integer indicates value to multiply the ATR
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
    Returns :
        df : Pandas DataFrame with new columns added for
            True Range (TR), ATR (ATR_$period)
            SuperTrend (ST_$period_$multiplier)
            SuperTrend Direction (STX_$period_$multiplier)
    """

    ATR(df, period, ohlc=ohlc)
    atr = 'ATR_' + str(period)
    st = 'ST_' + str(period)  # + '_' + str(multiplier)
    stx = 'STX_' + str(period)  # + '_' + str(multiplier)

    """
    SuperTrend Algorithm :
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

    # Set the Supertrend value
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

def get_timestamp():
    return datetime.now(IST).strftime('%Y:%m:%d %H:%M:%S %Z %z')

def get_ltp(instrument_token):
    return kite.ltp(instrument_token)[str(instrument_token)]['last_price']

# get the standard UTC time
UTC = pytz.utc

# get the time zone of the specified location
IST = pytz.timezone('Asia/Kolkata')

today = datetime.today()
previous_trading_day = (datetime.today() - BDay(1)).strftime('%Y-%m-%d')

kite = Zerodha()


# Set access token loads the stored session.
# Name chosen to keep it compatible with kiteconnect.
kite.set_access_token()



# def buy(instrument_token):
#     if instrument_token not in open_trades:
#         buy_price = get_ltp(instrument_token)
#         orderbook.write("Bought " + ticker_dictionary.get(instrument_token, 'No Key Found')['name'] + " at " + str(buy_price))
#         open_trades.append(instrument_token)

# def sell(instrument_token):
#     if instrument_token in open_trades:
#         sell_price = get_ltp(instrument_token)
#         orderbook.write("Sold " + ticker_dictionary.get(instrument_token, 'No Key Found')['name'] + " at " + str(sell_price) )
#         open_trades.remove(instrument_token)


banknifty_instrument_token = 260105

previous_trading_day_banknifty_ohlc = kite.historical_data(
    banknifty_instrument_token, previous_trading_day, previous_trading_day, "day")[0]

banknifty_high = round(previous_trading_day_banknifty_ohlc['high'])
banknifty_high = banknifty_high - (banknifty_high % 100)
banknifty_low = round(previous_trading_day_banknifty_ohlc['low'])
banknifty_low = banknifty_low - (banknifty_low % 100)

nfo_instruments = pd.DataFrame(kite.instruments("NFO"))

banknifty_instruments = nfo_instruments.loc[(
    nfo_instruments.name == 'BANKNIFTY')]


# print(banknifty_instruments)
# watchlist_instruments = banknifty_instruments.loc[banknifty_instruments.strike == 35000]
# print(watchlist_instruments)

watchlist = []
tickertape = {}
strikes = []

for strike in range(banknifty_low, banknifty_high, 100):
    if strike not in strikes:
        strikes.append(strikes)

        monthly_options = banknifty_instruments.loc[banknifty_instruments.strike == strike, [
            'instrument_token', 'tradingsymbol']].head(2)
        call_instrument_token, call_tradingsymbol = monthly_options.values[0]
        put_instrument_token, put_tradingsymbol = monthly_options.values[1]
        tickertape[call_instrument_token] = call_tradingsymbol
        tickertape[put_instrument_token] = put_tradingsymbol
        watchlist.append(call_instrument_token)
        watchlist.append(call_instrument_token)

print(f"Tickertape: {tickertape}")

ticks210 = {}
volume = {}
candles = {}
candle_writers = {}
tick_writers = {}


for instrument_token in watchlist:

    ticks210[instrument_token] = []
    volume[instrument_token] = 0
    candles[instrument_token] = pd.DataFrame(kite.historical_data(
        instrument_token, previous_trading_day + " 15:00:00", previous_trading_day + " 15:21:00", "minute"))
    candle_writers[instrument_token] = csv.writer(
        open(tickertape[instrument_token] + ".csv", "w"))
    tick_writers[instrument_token] = csv.writer(
        open(tickertape[instrument_token] + "_ticks.csv", "w"))


tradebook = open('tradebook.txt', "w")
orderbook = open("orderbook.txt", "w")
super_tradebook = open('super_tradebook.txt', 'w')
rsi_tradebook = open('rsi_tradebook.txt', 'w')

double_tradebook = open('double_tradebook.txt', 'w')
triple_tradebook = open('triple_tradebook.txt', 'w')

instrument_token = ''
ltp = ''
open_positions = True
open_trades = []
triple_trades = []
double_trades = []


kws = kite.ticker()


def on_candle(instrument_token, ticks, candles):

    last_candle = candles[instrument_token].iloc[-1]
    candle_open = ( last_candle.open + last_candle.close ) / 2
    candle_high = max(ticks)
    candle_low = min(ticks)
    candle_close = ticks[-1]
    candle_close = (candle_open + candle_high + candle_low + candle_close) / 4
    candle_volume = volume
    candle_data = [get_timestamp(), candle_open, candle_high,
                   candle_low, candle_close, candle_volume]

    candle_dataframe_length = len(candles)
    candles.loc[candle_dataframe_length] = candle_data
    candle_writers[instrument_token].writerow(candle_data)
    

    candle_df = candles.copy()

    candle_df['rsi13'] = RSI(candle_df['close'], timeperiod=13)
    candle_df['rsi21'] = RSI(candle_df['close'], timeperiod=21)
    candle_df['rsi34'] = RSI(candle_df['close'], timeperiod=34)
    candle_df['ema21'] = talib.EMA(candle_df['close'], timeperiod=21)
    candle_df['wma21'] = WMA(candle_df['close'], timeperiod=21)
    supertrend_df = SuperTrend(candle_df, period=21, multiplier=3)
    supertrend_df = SuperTrend(supertrend_df, period=13, multiplier=2)
    supertrend_df = SuperTrend(supertrend_df, period=8, multiplier=1)

    penultimate_candle = candle_df.iloc[-2]
    last_candle = candle_df.iloc[-1]
    symbol = tickertape[instrument_token]

    super_candle = supertrend_df.iloc[-1]

    if instrument_token not in double_trades:
        if super_candle.STX_13:
            if super_candle.STX_8:
                if last_candle.ema21 < candle_close:
                    double_trades.append(instrument_token)
                    print(
                        f"Double supertrend buy signal, {symbol} at {get_timestamp()} ltp: {get_ltp(instrument_token)} ")
                    double_tradebook.write(
                        f"\nDouble supertrend buy signal, {symbol} at {get_timestamp()} ltp: {get_ltp(instrument_token)} ")

        if penultimate_candle.rsi21 < 21:
            if last_candle.rsi21 >= 21:
                if penultimate_candle.rsi13 < 13:
                    if last_candle.rsi13 >= 13:
                        triple_trades.append(instrument_token)
                        print(
                            f"Double RSI buy signal, {symbol} at {get_timestamp()} ltp: {get_ltp(instrument_token)} ")
                        rsi_tradebook.write(
                            f"\nDouble RSI buy signal, {symbol} at {get_timestamp()} ltp: {get_ltp(instrument_token)} ")

    elif instrument_token in double_trades:
        if not super_candle.STX_8:
            double_trades.remove(instrument_token)
            print(
                f"Supertrend 8 sell signal, {symbol} at {get_timestamp()} ltp: {get_ltp(instrument_token)} ")
            super_tradebook.write(
                f"\nSupertrend 8 sell signal, {symbol} at {get_timestamp()} ltp: {ltp} ")
        elif penultimate_candle.rsi13 >= 87:
            if last_candle.rsi13 <= 87:
                double_trades.remove(instrument_token)
                print(
                    f"RSI 13 sell signal, {symbol} at {get_timestamp()} ltp: {get_ltp(instrument_token)} ")
                rsi_tradebook.write(
                    f"\nRSI 13 sell signal, {symbol} at {get_timestamp()} ltp: {get_ltp(instrument_token)} ")


def on_ticks(ws, ticks):

    # Callback to receive ticks.
    for tick in ticks:

        instrument_token = tick['instrument_token']
        ltp = tick['last_price']
        ohlc = tick['ohlc']
        last_quantity = tick['last_quantity']

        tick_writers[instrument_token].writerow(
            [get_timestamp(), ltp, last_quantity, ohlc])
        ticks210[instrument_token].append(ltp)
        volume[instrument_token] += last_quantity

        if(len(ticks210[instrument_token]) == 210):

            start_new_thread(on_candle, (instrument_token, ticks210[instrument_token], candles[instrument_token]))

            ticks210[instrument_token] = []
            volume[instrument_token] = 0


def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe(watchlist)

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_QUOTE, watchlist)


def on_close(ws, code, reason):
    # On connection close stop the event loop.
    # Reconnection will not happen after executing `ws.stop()`
    # for instrument_token in watchlist:
    #     candles[instrument_token].to_csv(tickers[instrument_token]+"_df.csv")
    ws.stop()


# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()
