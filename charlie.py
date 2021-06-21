import pandas as pd

data = pd.read_csv("/home/ubuntu/tessa/18thJune/BANKNIFTY21JUN34600CE.csv")
data["range"] = data['open'] - data['close']
data["wick_range"] = data['high'] - data['low'] 

print("Max range:", data["range"].max())
print("Max wick range:", data["wick_range"].max())