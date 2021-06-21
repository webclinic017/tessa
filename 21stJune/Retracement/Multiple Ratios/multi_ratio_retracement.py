from datetime import datetime
from dateutil.tz import tzoffset
from pandas._libs.tslibs import Timestamp
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
from dateutil.tz import tzoffset

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


def get_timestamp():
    return datetime.now(tzoffset(None, 19800)).isoformat(' ', 'seconds')


def get_ltp(instrument_token):
    return kite.ltp(instrument_token)[str(instrument_token)]['last_price']


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

previous_session_ohlc = kite.historical_data(
    banknifty_instrument_token, today - timedelta(days=21), today, "day")[-1]

previous_session_date = previous_session_ohlc['date']


banknifty_high = round(previous_session_ohlc['high'])
banknifty_high = banknifty_high - (banknifty_high % 100)
banknifty_low = round(previous_session_ohlc['low'])
banknifty_low = banknifty_low - (banknifty_low % 100)

nfo_instruments = pd.DataFrame(kite.instruments("NFO"))

banknifty_instruments = nfo_instruments.loc[(
    nfo_instruments.name == 'BANKNIFTY')]

# call_option = banknifty_instruments.loc[[banknifty_instruments.strike == banknifty_low ]
# print(call_option)


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
        watchlist.append(put_instrument_token)

print(f"Tickertape: {tickertape}")

ticks210 = {}
volume = {}
candles = {}
candle_writers = {}
tick_writers = {}
fibonacci = {}
ratios = [0.236, 0.382, 0.50, 0.618, 0.786, 1.00, 1.618, 2.618, 4.236]


for instrument_token in watchlist:

    ticks210[instrument_token] = []
    volume[instrument_token] = 0
    fibonacci[instrument_token] = {}
    previous_session_ohlc = kite.historical_data(
        instrument_token, today - timedelta(days=21), today, "day")[-1]

    for ratio in ratios:
        retracement = previous_session_ohlc['high'] - (
            previous_session_ohlc['high'] - previous_session_ohlc['low']) * ratio

        fibonacci[instrument_token][ratio] = retracement

    candles[instrument_token] = pd.DataFrame(kite.historical_data(
        instrument_token, previous_session_date + timedelta(hours=15), previous_session_date + timedelta(hours=15, minutes=21), "minute"))

    candle_writers[instrument_token] = csv.writer(
        open(tickertape[instrument_token] + ".csv", "w"))
    tick_writers[instrument_token] = csv.writer(
        open(tickertape[instrument_token] + "_ticks.csv", "w"))


tradebook = open('tradebook.txt', "w")
orderbook = open("orderbook.txt", "w")

instrument_token = ''
ltp = ''
open_positions = True
open_trades = []
triple_trades = []
double_trades = []


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

    penultimate_candle = candles.iloc[-2]
    last_candle = candles.iloc[-1]
    tradingsymbol = tickertape[instrument_token]

    if instrument_token not in open_trades:
        for ratio in ratios:
            retracement_value = fibonacci[instrument_token][ratio]
            if penultimate_candle.low <= retracement_value:
                if penultimate_candle.close >= retracement_value:
                    if last_candle.high >= penultimate_candle.high:
                        if last_candle.low >= penultimate_candle.low:
                            open_trades.append(instrument_token)
                            timestamp = get_timestamp()
                            last_traded_price = get_ltp(instrument_token)
                            print(
                                f"{ratio} retracement - {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                            tradebook.write(
                                f"{ratio} retracement - {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

    if instrument_token in open_trades:
        if last_candle.high <= penultimate_candle.high:
            if last_candle.low <= penultimate_candle.low:
                open_trades.remove(instrument_token)
                timestamp = get_timestamp()
                last_traded_price = get_ltp(instrument_token)
                print(
                    f"Sell signal - {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                tradebook.write(
                    f"Sell signal - {tradingsymbol} at {timestamp} ltp: {last_traded_price}")


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

            start_new_thread(on_candle, (instrument_token,
                             ticks210[instrument_token], candles[instrument_token], volume))

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
