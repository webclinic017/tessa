
from pprint import pprint
from jugaad_trader import Zerodha
import pandas as pd
import pytz
from datetime import datetime, timedelta
import csv
from pandas.tseries.offsets import BDay
print("Om Namahshivaya:")

kite = Zerodha()

# Set access token loads the stored session.
# Name chosen to keep it compatible with kiteconnect.
kite.set_access_token()



class Ticker:
    def __init__(self, instrument_token, tradingsymbol, highest_high, lowest_low) -> None:
        self.instrument_token = instrument_token
        self.tradingsymbol = tradingsymbol
        self.highest_high = highest_high
        self.lowest_low = lowest_low
        self.open_long_trade = False
        self.open_short_trade = False


today = datetime.today()

today_data = ""
historical_data = ""

nse_instruments = pd.DataFrame(kite.instruments('NSE'))
stock_instruments = nse_instruments.loc[nse_instruments.lot_size == 1]
stock_instruments = stock_instruments.loc[stock_instruments.tick_size == 0.05]


trading_dates = pd.DataFrame(kite.historical_data(
    260105, today - timedelta(days=34), today - timedelta(days=1), "day"))
trading_dates = trading_dates.tail(21).date.apply(datetime.date).tolist()

for date in trading_dates:
    invalid = []
    for index, row in stock_instruments.iterrows():

        instrument_token = row['instrument_token']
        tradingsymbol = row['tradingsymbol']
        try:
            last_day_candle = pd.DataFrame(kite.historical_data(
                instrument_token, date, date, "day"))
            last_day_candle = last_day_candle.iloc[-1]
            if (last_day_candle.high - last_day_candle.low) < 2.1:
                invalid.append(index)

        except Exception as e:

            invalid.append(index)
            continue

    stock_instruments = stock_instruments.drop(invalid)

stock_instruments.loc[["instrument_token", "tradingsymbol", "name"]].to_csv(
    "stock_instruments.csv", index=False)

# tickers = []
# watchlist = []
# invalid = []



# for index, row in stock_instruments.iterrows():

#     instrument_token = row['instrument_token']
#     tradingsymbol = row['tradingsymbol']
#     try:
#         historical_data = pd.DataFrame(kite.historical_data(
#             instrument_token, today - timedelta(days=34), today - timedelta(days=1), "day"))
#         historical_data = historical_data.tail(-1).tail(21)
#         last_day_candle = historical_data.iloc[-1]
#         if (last_day_candle.high - last_day_candle.low) >= 2.1:
#             highest_high = historical_data['high'].max()
#             lowest_low = historical_data['low'].min()
#             # print(instrument_token, tradingsymbol, highest_high)

#             tickers.append(
#                 Ticker(instrument_token, tradingsymbol, highest_high, lowest_low))
#             watchlist.append(instrument_token)

#     except Exception as e:

#         invalid.append(index)
#         continue

# stock_instruments = stock_instruments.drop(invalid)
# print(stock_instruments)
