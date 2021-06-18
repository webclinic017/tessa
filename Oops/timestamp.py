


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
print(datetime.now(tzoffset(None, 19800)).isoformat(' ', 'seconds'))
print(kite.historical_data(
    banknifty_instrument_token, previous_trading_day, today, "day")[-1])


