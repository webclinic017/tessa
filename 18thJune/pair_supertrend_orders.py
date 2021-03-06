from kiteconnect import ticker
from talib import RSI, WMA
from _thread import start_new_thread
import talib
import numpy as np
from jugaad_trader import Zerodha
import pandas as pd
from datetime import datetime, timedelta
from dateutil import tzoffset
import csv

print("Om Namahshivaya:")


# historical_data = pd.DataFrame(kite.historical_data(
#     260105, today - timedelta(days=34), today, "day"))

# df = SUPERTREND(historical_data, period=21, multiplier=3,
#                 ohlc=['open', 'high', 'low', 'close'])
# df = SUPERTREND(historical_data, period=13, multiplier=2,
#                 ohlc=['open', 'high', 'low', 'close'])
# df = SUPERTREND(historical_data, period=8, multiplier=1,
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

def get_timestamp():
    return datetime.now(IST).strftime('%Y:%m:%d %H:%M:%S %Z %z')

def get_ltp(instrument_token):
    return kite.ltp(instrument_token)[str(instrument_token)]['last_price']


today = datetime.today()



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

previous_session_ohlc = kite.historical_data(
    banknifty_instrument_token, today - timedelta(days=21), today, "day")[-1]

previous_session_date = previous_session_ohlc['date']

banknifty_close = round(previous_session_ohlc['close'])
banknifty_close = banknifty_close - (banknifty_close % 100)
banknifty_high = round(previous_session_ohlc['high'])
banknifty_high = banknifty_high - (banknifty_high % 100)
banknifty_low = round(previous_session_ohlc['low'])
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

# for strike in range(banknifty_low, banknifty_high, 100):
#     if strike not in strikes:
#         strikes.append(strikes)

#         monthly_options = banknifty_instruments.loc[banknifty_instruments.strike == strike, [
#             'instrument_token', 'tradingsymbol']].head(2)
#         call_instrument_token, call_tradingsymbol = monthly_options.values[0]
#         put_instrument_token, put_tradingsymbol = monthly_options.values[1]
#         tickertape[call_instrument_token] = call_tradingsymbol
#         tickertape[put_instrument_token] = put_tradingsymbol
#         watchlist.append(call_instrument_token)
#         watchlist.append(put_instrument_token)

monthly_options = banknifty_instruments.loc[banknifty_instruments.strike == banknifty_close, [
    'instrument_token', 'tradingsymbol']].head(2)
call_instrument_token, call_tradingsymbol = monthly_options.values[0]
put_instrument_token, put_tradingsymbol = monthly_options.values[1]
tickertape[call_instrument_token] = call_tradingsymbol
tickertape[put_instrument_token] = put_tradingsymbol
watchlist.append(call_instrument_token)
watchlist.append(put_instrument_token)



ticks210 = {}
volume = {}
candles = {}
candle_writers = {}
tick_writers = {}


for instrument_token in watchlist:

    ticks210[instrument_token] = []
    volume[instrument_token] = 0
    candles[instrument_token] = pd.DataFrame(kite.historical_data(instrument_token, previous_session_date + timedelta(hours=15), previous_session_date + timedelta(hours=15, minutes=21), "minute"))
    tick_writers[instrument_token] = csv.writer(
        open(tickertape[instrument_token] + "_ticks.csv", "w"))


tradebook = open('tradebook.txt', "w")
orderbook = open("orderbook.txt", "w")

triple_tradebook = open("triple_tradebook.txt", "w")
triple_orderbook = open("triple_orderbook.txt", "w")
double_tradebook = open("double_tradebook.txt", "w")
double_orderbook = open("double_orderbook.txt", "w")

instrument_token = ''
ltp = ''
open_positions = True
open_trades = []
triple_trades = []
double_trades = []

print(f"Tickertape: {tickertape}")
kws = kite.ticker()


def on_candle(instrument_token, ticks, candles, volume):

    candle_open = ticks[0]
    candle_high = max(ticks)
    candle_low = min(ticks)
    candle_close = ticks[-1]
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
    supertrend_df = SUPERTREND(candle_df, period=21, multiplier=3)
    supertrend_df = SUPERTREND(supertrend_df, period=13, multiplier=2)
    supertrend_df = SUPERTREND(supertrend_df, period=8, multiplier=1)

    penultimate_candle = candle_df.iloc[-2]
    last_candle = candle_df.iloc[-1]
    tradingsymbol = tickertape[instrument_token]

    super_candle = supertrend_df.iloc[-1]
    penultimate_super_candle = supertrend_df.iloc[-2]

    if instrument_token not in triple_trades:
        if not penultimate_super_candle.STX_13:
            if not penultimate_super_candle.STX_8:
                if super_candle.STX_21:
                    if super_candle.STX_13:
                        if super_candle.STX_8:
                            triple_trades.append(instrument_token)
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
                            print(f"Triple Supertrend Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")

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
                            orderbook.write(f"\nTriple Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                            tradebook.write(
                                f"\nTriple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                            triple_orderbook.write(f"\nTriple Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                            triple_tradebook.write(
                                    f"\nTriple Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
    
    if instrument_token not in triple_trades:
        if penultimate_candle.rsi34 < 34:
            if last_candle.rsi34 >= 34:
                if penultimate_candle.rsi21 < 21:
                    if last_candle.rsi21 >= 21:
                        if penultimate_candle.rsi13 < 13:
                            if last_candle.rsi13 >= 13:
                                triple_trades.append(instrument_token)
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
                                print(f"Triple RSI Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")

                                print(
                                    f"Triple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                                orderbook.write(f"\nTriple RSI: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                                tradebook.write(
                                    f"\nTriple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                                triple_orderbook.write(f"\nTriple RSI: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                                triple_tradebook.write(
                                    f"\nTriple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    elif instrument_token in triple_trades:
        if not super_candle.STX_13:
            triple_trades.remove(instrument_token)
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
            print(f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")

            print(
                f"Triple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
            orderbook.write(f"\nTriple Supertrend: Supertrend 13 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
            tradebook.write(
                f"\nTriple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
            triple_orderbook.write(f"\nTriple Supertrend: Supertrend 13 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
            triple_tradebook.write(
                f"\nTriple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    elif instrument_token in triple_trades:
        if penultimate_candle.rsi21 > 79:
            if last_candle.rsi21 <= 79:
                triple_trades.remove(instrument_token)
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
                print(f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                print(
                    f"Triple RSI 21 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                orderbook.write(f"\nTriple RSI: RSI 21 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                tradebook.write(
                    f"\nTriple RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                triple_orderbook.write(f"\nTriple RSI: RSI 21 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                triple_tradebook.write(
                f"\nTriple RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    # if instrument_token not in double_trades:
    #     if super_candle.STX_13:
    #         if super_candle.STX_8:
    #             if last_candle.ema21 < candle_close:
    #                 double_trades.append(instrument_token)
    #                 last_traded_price = get_ltp(instrument_token)
    #                 timestamp = get_timestamp()
    #                 print(
    #                     f"Double Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
    #                 orderbook.write(f"\nDouble Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
    #                 tradebook.write(
    #                     f"\nDouble Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
    #                 double_orderbook.write(f"\nDouble Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
    #                 double_tradebook.write(
    #                     f"\nDouble Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    #     if penultimate_candle.rsi21 < 21:
    #         if last_candle.rsi21 >= 21:
    #             if penultimate_candle.rsi13 < 13:
    #                 if last_candle.rsi13 >= 13:
    #                     double_trades.append(instrument_token)
    #                     last_traded_price = get_ltp(instrument_token)
    #                     timestamp = get_timestamp()
    #                     print(
    #                         f"Double RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
    #                     orderbook.write(f"\nDouble RSI: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
    #                     tradebook.write(
    #                         f"\nDouble RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
    #                     double_orderbook.write(f"\nDouble RSI: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
    #                     double_tradebook.write(
    #                         f"\nDouuble RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    # elif instrument_token in double_trades:
    #     if not super_candle.STX_8:
    #         double_trades.remove(instrument_token)
    #         last_traded_price = get_ltp(instrument_token)
    #         timestamp = get_timestamp()
    #         print(
    #             f"Double Supertrend sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
    #         orderbook.write(f"\nDouble Supertrend: Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
    #         tradebook.write(
    #             f"\nDouble Supertrend sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
    #         double_orderbook.write(f"\nDouble Supertrend: Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
    #         double_tradebook.write(
    #             f"\nDouble Supertrend sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

    #     elif penultimate_candle.rsi13 >= 87:
    #         if last_candle.rsi13 <= 87:
    #             last_traded_price = get_ltp(instrument_token)
    #             timestamp = get_timestamp()
    #             print(
    #                 f"Double RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
    #             orderbook.write(f"\nDouble RSI: Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
    #             tradebook.write(
    #                 f"\nDouble RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
    #             double_orderbook.write(f"\nDouble RSI: Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
    #             double_tradebook.write(
    #                 f"\nDouble RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")


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

        if(len(ticks210[instrument_token]) == 161):

            start_new_thread(on_candle, (instrument_token, ticks210[instrument_token], candles[instrument_token], volume[instrument_token]))

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
    for instrument_token in watchlist:
        candles[instrument_token].to_csv(tickertape[instrument_token]+".csv", index=False)
    ws.stop()


# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()
