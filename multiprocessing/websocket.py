from jugaad_trader import Zerodha
from datetime import datetime, timedelta
from dateutil.tz import tzoffset
from pandas import DataFrame
from talib import EMA
from csv import writer
from threading import Thread
from strategy import on_candle

kite = Zerodha()


# Set access token loads the stored session.
# Name chosen to keep it compatible with kiteconnect.
kite.set_access_token()

def get_timestamp():
    return datetime.now(tzoffset(None, 19800)).isoformat(' ', 'seconds')

def get_ltp(instrument_token):
    return kite.ltp(instrument_token)[str(instrument_token)]['last_price']

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

        self.tick_store = []
        self.volume = 0
        Thread(target = on_candle, args=(self.instrument_token,))

    def get_last_candle(self):
        return self.candles.iloc[-1]

    def get_penultimate_candle(self):
        return self.candles.iloc[-2]

    def get_candles(self):
        return self.candles
    
    def get_ltp(self):
        return kite.ltp(self.instrument_token)[str(self.instrument_token)]['last_price']


today = datetime.today()
banknifty_instrument_token = 260105

historical = kite.historical_data(
    banknifty_instrument_token, today - timedelta(days=314), today - timedelta(days=1), "day")
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


nfo_instruments = DataFrame(kite.instruments("NFO"))

banknifty_instruments = nfo_instruments.loc[(
    nfo_instruments.name == 'BANKNIFTY')]

tickertape = {}
strikes = []

# monthly_options = banknifty_instruments.loc[banknifty_instruments.strike == banknifty_close, [
#     'instrument_token', 'tradingsymbol']].head(2)

high_put_option = banknifty_instruments.loc[banknifty_instruments.strike == banknifty_high, [
    'instrument_token', 'tradingsymbol']].head(6)

low_call_option = banknifty_instruments.loc[banknifty_instruments.strike == banknifty_low, [
    'instrument_token', 'tradingsymbol']].head(5)


# high_put_instrument_token, high_put_tradingsymbol = high_put_option.values[1]
# low_call_instrument_token, low_call_tradingsymbol = low_call_option.values[0]
# tickertape[high_put_instrument_token] = high_put_tradingsymbol
# tickertape[low_call_instrument_token] = low_call_tradingsymbol

call_instrument_token, call_tradingsymbol = low_call_option.values[4]
put_instrument_token, put_tradingsymbol = high_put_option.values[5]

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
