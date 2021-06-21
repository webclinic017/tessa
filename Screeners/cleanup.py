import pandas as pd
from jugaad_trader import Zerodha

kite = Zerodha()

# Set access token loads the stored session.
# Name chosen to keep it compatible with kiteconnect.
kite.set_access_token()

nse_bse_symbols = pd.read_csv("/workspaces/tessa/Screeners/nse_bse_tradingsymbols.csv")

bse_instruments = pd.DataFrame(kite.instruments("BSE"))
nse_instruments = pd.DataFrame(kite.instruments("NSE"))

nse_bse_symbols['nse_instrument_token'] = None
nse_bse_symbols['bse_instrument_token'] = None

dropped = []
for index, row in nse_bse_symbols.iterrows():
    try:

        nse_instrument_token = nse_instruments.loc[nse_instruments.tradingsymbol == row['nse_tradingsymbol']].values[0][0]
        bse_instrument_token = bse_instruments.loc[bse_instruments.tradingsymbol == row['bse_tradingsymbol']].values[0][0]
        row['nse_instrument_token'] = nse_instrument_token
        row['bse_instrument_token'] = bse_instrument_token
    except:
        dropped.append(index)
print(dropped)
for index in dropped:
    nse_bse_symbols.drop(index, inplace=True)
print(nse_bse_symbols.head())
nse_bse_symbols.to_csv("/workspaces/tessa/Screeners/common_instruments.csv", index=False)
