# import pandas as pd
# from jugaad_trader import Zerodha
# from datetime import datetime, timedelta

# kite = Zerodha()


# # Set access token loads the stored session.
# # Name chosen to keep it compatible with kiteconnect.
# kite.set_access_token()

# today = datetime.today()


# banknifty_instrument_token = 260105

# previous_session_ohlc = kite.historical_data(
#     banknifty_instrument_token, today - timedelta(days=21), today, "day")[-1]

# previous_session_date = previous_session_ohlc['date']


# banknifty_high = round(previous_session_ohlc['high'])
# banknifty_high = banknifty_high - (banknifty_high % 100)
# banknifty_low = round(previous_session_ohlc['low'])
# banknifty_low = banknifty_low - (banknifty_low % 100)

# nfo_instruments = pd.DataFrame(kite.instruments("NFO"))

# banknifty_instruments = nfo_instruments.loc[(
#     nfo_instruments.name == 'BANKNIFTY')]

# call_option = banknifty_instruments.loc[(banknifty_instruments.strike == banknifty_low) & (banknifty_instruments.instrument_type == 'CE')]
# print(call_option)


import numpy
import talib
from talib import stream

close = numpy.random.random(61)
output = talib.SMA(close)
charlie = numpy.append(close, numpy.random.random(1))
latest = stream.SMA(charlie)




print(output, latest)