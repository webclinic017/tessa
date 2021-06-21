from datetime import datetime, timedelta
from jugaad_trader import Zerodha
import pandas as pd
from datetime import datetime, timedelta
from talib import RSI, EMA
from more_itertools import pairwise
# from talib.stream import RSI, EMA
import numpy as np

print("Om Namahshivaya:")

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

nfo_instruments = pd.DataFrame(kite.instruments('NFO'))
banknifty_instruments = nfo_instruments.loc[nfo_instruments.name == 'BANKNIFTY']

banknifty_future_instruments = banknifty_instruments.loc[banknifty_instruments.instrument_type=="FUT"]
near_future_instrument_token = banknifty_future_instruments.iloc[-1].instrument_token
print(near_future_instrument_token)

today = datetime.today()
historical_data = pd.DataFrame(kite.historical_data(260105, today - timedelta(days=1618), today, "day"))
trading_dates = historical_data['date']




overall_pandl = 0
pl = []
for from_date, to_date in pairwise(trading_dates):
    from_date = from_date.date()
    to_date = to_date.date()
    historical_data = pd.DataFrame(kite.historical_data(260105, from_date, to_date, "3minute")).head(122)
    open_trades = False
    open_long_trade = False
    open_short_trade = False
    long_buy_price = 0
    long_sell_price = 0
    short_buy_price = 0
    short_sell_price = 0
    long_pandl = 0
    overall_long_pandl = 0
    overall_short_pandl = 0
    short_pandl = 0
    p_and_l = 0

    for i in range(21, len(historical_data)):
        candles = historical_data.copy().head(i)
        candles['rsi13'] = RSI(candles['close'], timeperiod=13)
        candles['rsi21'] = RSI(candles['close'], timeperiod=21)
        candles['ema21'] = EMA(candles['close'], timeperiod=21)
        supertrend_df = SUPERTREND(candles, period=21, multiplier=3)
        supertrend_df = SUPERTREND(supertrend_df, period=13, multiplier=2)
        supertrend_df = SUPERTREND(supertrend_df, period=8, multiplier=1)

        penultimate_candle = candles.iloc[-2]
        last_candle = candles.iloc[-1]

        super_candle = supertrend_df.iloc[-1]
        penultimate_super_candle = supertrend_df.iloc[-2]

        if not open_long_trade:
            if not penultimate_super_candle.STX_13:
                if not penultimate_super_candle.STX_8:
                    if super_candle.STX_21:
                        if super_candle.STX_13:
                            if super_candle.STX_8:
                                open_long_trade = True
                                long_buy_price = (last_candle.high + last_candle.close)/2

                                print(
                                    f"Triple Supertrend long signal at {last_candle.date} ltp: {long_buy_price}")
                                    
        if not open_long_trade:
            if penultimate_candle.rsi21 < 21:
                if last_candle.rsi21 >= 21:
                    if penultimate_candle.rsi13 < 13:
                        if last_candle.rsi13 >= 13:
                            open_long_trade = True
                            long_buy_price = (last_candle.high + last_candle.close)/2
                            print(
                                f"Double RSI long signal at {last_candle.date} ltp: {long_buy_price}")



        elif open_long_trade:
            if not super_candle.STX_13:
                open_long_trade = False
                long_sell_price = (last_candle.low + last_candle.close)/2
                long_pandl += long_sell_price - long_buy_price
                p_and_l += long_sell_price - long_buy_price
                open_long_trade = False

                print(
                    f"Supertrend 13 sell signal at {last_candle.date} ltp: {long_sell_price}")
                long_buy_price = 0
                long_sell_price = 0

    
        elif open_long_trade:
            if penultimate_candle.rsi13 > 87:
                if last_candle.rsi13 <= 87:
                    open_long_trade = False
                    long_sell_price = (last_candle.low + last_candle.close)/2
                    long_pandl += long_sell_price - long_buy_price
                    p_and_l += long_sell_price - long_buy_price
                    
                    print(
                        f"RSI 13 sell signal at {last_candle.date} ltp: {long_sell_price}")
                    long_buy_price = 0
                    long_sell_price = 0

        if not open_short_trade:
            if penultimate_super_candle.STX_13:
                if penultimate_super_candle.STX_8:
                    if not super_candle.STX_21:
                        if not super_candle.STX_13:
                            if not super_candle.STX_8:
                                open_short_trade = True
                                short_buy_price = (last_candle.high + last_candle.close)/2

                                print(
                                    f"Triple Supertrend Short signal at {last_candle.date} ltp: {short_buy_price}")
                                    
        if not open_short_trade:
            if penultimate_candle.rsi21 > 79:
                if last_candle.rsi21 <= 79:
                    if penultimate_candle.rsi13 > 87:
                        if last_candle.rsi13 <= 87:

                            open_short_trade = True
                            short_buy_price = (last_candle.high + last_candle.close)/2

                            print(
                                f"Double RSI Short signal at {last_candle.date} ltp: {short_buy_price}")


        elif open_short_trade:
            if super_candle.STX_13:

                open_short_trade = False
                short_sell_price = (last_candle.low + last_candle.close)/2
                short_pandl +=  short_buy_price - short_sell_price
                p_and_l += long_sell_price - long_buy_price
               

                print(
                    f"Supertrend 13 sell signal at {last_candle.date} ltp: {short_sell_price}")
                short_buy_price = 0
                short_sell_price = 0

    
        elif open_short_trade:
            if penultimate_candle.rsi13 > 87:

                open_short_trade = False
                short_sell_price = (last_candle.low + last_candle.close)/2
                short_pandl +=  short_buy_price - short_sell_price
                p_and_l += long_sell_price - long_buy_price
               

                print(
                    f"Supertrend 13 sell signal at {last_candle.date} ltp: {short_sell_price}")

                short_buy_price = 0
                short_sell_price = 0


        else:
            continue
    overall_pandl += p_and_l
    overall_long_pandl += long_pandl
    overall_short_pandl += short_pandl
    pl.append(p_and_l)

    print("P&L:", p_and_l)
    print("Long P&L:", long_pandl)
    print("Short P&L:", short_pandl)

print("Overall P&L:", overall_pandl)
print("Max Profit:", max(pl))
print("Max Loss:", min(pl))