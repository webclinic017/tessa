import pandas as pd
from jugaad_trader import Zerodha
from datetime import datetime, timedelta
from pandas import DataFrame
from dateutil.tz import tzoffset

kite = Zerodha()


# Set access token loads the stored session.
# Name chosen to keep it compatible with kiteconnect.
kite.set_access_token()

today = datetime.today()
banknifty_instrument_token = 260105


def get_timestamp():
    return datetime.now(tzoffset(None, 19800)).isoformat(' ', 'seconds')

historical = kite.historical_data(
    banknifty_instrument_token, today - timedelta(days=314), today, "day")
historical_data = DataFrame(historical)

print(historical_data.tail())


previous_session_ohlc = historical[-2]


previous_day_candle = historical_data.iloc[-2]

previous_session_date = previous_session_ohlc['date'].date()
banknifty_close = int(round(previous_day_candle['close'], -2))
candles = DataFrame(kite.historical_data(
    banknifty_instrument_token, previous_session_date + timedelta(hours=15), datetime.now(tzoffset(None, 19800)), "3minute"))
print(candles)
print(datetime.now().replace(second=0, microsecond=0))
