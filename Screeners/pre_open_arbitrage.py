import pandas as pd
from jugaad_trader import Zerodha

kite = Zerodha()

# Set access token loads the stored session.
# Name chosen to keep it compatible with kiteconnect.
kite.set_access_token()

common_instruments = pd.read_csv("Screeners/common_instruments.csv")

watchlist = []

for index, row in common_instruments.iterrows():
 
    ltp_nse = kite.ltp(row['nse_instrument_token'])[str(row['nse_instrument_token'])]['last_price']
    ltp_bse = kite.ltp(row['bse_instrument_token'])[str(row['bse_instrument_token'])]['last_price']

    if(ltp_nse == ltp_nse):
        print("=", end="")
        continue
    elif(ltp_nse > ltp_bse):
        print("LTP is higher in NSE is greater than that in BSE")
    
    else:
        print("LTP is higher in BSE is greater than that in NSE")
    print("Difference: ", ltp_nse - ltp_bse, ltp_nse, ltp_bse)
    watchlist.append(index)