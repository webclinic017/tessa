


from _thread import start_new_thread
import talib
from talib import RSI, WMA
import numpy as np
from pprint import pprint
from jugaad_trader import Zerodha
import pandas as pd
import pytz
from datetime import datetime, timedelta, tzinfo
import csv
from pandas.tseries.offsets import BDay
from dateutil.tz import tzoffset

print("Om Namahshivaya:")


# get the standard UTC time
UTC = pytz.utc

# get the time zone of the specified location
IST = pytz.timezone('Asia/Kolkata')

today = datetime.today()
previous_trading_day = (datetime.today() - BDay(1)).strftime('%Y-%m-%d')

kite = Zerodha()


# Set access token loads the stored session.
# Name chosen to keep it compatjible with kiteconnect.
kite.set_access_token()

banknifty_instrument_token = 260105


historical_data = kite.historical_data(
    banknifty_instrument_token, today - timedelta(days=21), today, "day")[-1]

print(type(historical_data))
previous_trading_day = historical_data['date']

# tzinfo = tzoffset(None, 19800)
# print(datetime.now(tzoffset(None, 19800)).isoformat(' ', 'seconds'))
# print(kite.historical_data(
#     banknifty_instrument_token, previous_trading_day, today, "day")[-1])

previous_trading_day_banknifty_ohlc = kite.historical_data(
    banknifty_instrument_token, previous_trading_day, previous_trading_day, "day")[0]
banknifty_close = round(previous_trading_day_banknifty_ohlc['close'])
banknifty_close = banknifty_close - (banknifty_close % 100)
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

print(f"Tickertape: {tickertape}")

def get_ltp(instrument_token):
    return kite.ltp(instrument_token)[str(instrument_token)]['last_price']

for instrument_token in watchlist:
    last_traded_price = get_ltp(instrument_token)
    order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
	                                exchange=kite.EXCHANGE_NFO,
	                                transaction_type=kite.TRANSACTION_TYPE_BUY,
	                                quantity=25,
	                                order_type=kite.ORDER_TYPE_LIMIT,
	                                product=kite.PRODUCT_NRML,
	                                variety=kite.VARIETY_AMO,
	                                price=last_traded_price,
	                                )
    print(order_id)
    stoploss_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
	                                exchange=kite.EXCHANGE_NFO,
	                                transaction_type=kite.TRANSACTION_TYPE_SELL,
	                                quantity=25,
	                                order_type=kite.ORDER_TYPE_SL,
	                                product=kite.PRODUCT_NRML,
	                                variety=kite.VARIETY_AMO,
                                    trigger_price=last_traded_price-21,
	                                price=last_traded_price-21,
	                                )
    print(stoploss_order_id)
    




