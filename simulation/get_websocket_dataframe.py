
import pandas as pd
from datetime import datetime

mydateparser = lambda x: pd.datetime.strptime(x, '%Y:%m:%d %H:%M:%S IST  %z')
ce_file = '/workspaces/tessa/simulation/ticks_ce.csv'
ce_ticks = pd.read_csv(ce_file, parse_dates=['date'], date_parser=mydateparser)
ce_ticks['instrument_token'] = 12739586
print(ce_ticks.dtypes)
# ce_ticks.date = pd.to_datetime(ce_ticks.date, format='%Y:%m:%d %H:%M:%S IST %z')
# print(ce_ticks.head())

pe_file = '/workspaces/tessa/simulation/ticks_pe.csv'

pe_ticks = pd.read_csv(pe_file, parse_dates=['date'], date_parser=mydateparser)
pe_ticks['instrument_token'] = 12739842
print(pe_ticks.dtypes)

data = pd.concat([ce_ticks, pe_ticks])


# data.date = pd.to_datetime(data.date, format='%Y:%m:%d %H:%M:%S IST  %z')

# data.date = data['date'].apply(datetime.strftime("%Y:%m:%d %H:%M:%S"))

# print(data.head())
data = data.set_index('date')
print(data.dtypes)
dataframe = data.sort_values(by='date')
dataframe.to_csv("/workspaces/tessa/simulation/streaming_data.csv")
