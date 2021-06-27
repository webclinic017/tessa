
class Ticker:
    def __init__(self, instrument_token, tradingsymbol, highest_high, lowest_low) -> None:
        self.instrument_token = instrument_token
        self.tradingsymbol = tradingsymbol
        self.highest_high = highest_high
        self.lowest_low = lowest_low
        self.open_long_trade = False
        self.open_short_trade = False

    def __repr__(self):
        return f"Instrument token: {self.instrument_token}, Trading symbol: {self.tradingsymbol}, Highest high: {self.highest_high}, Lowest low: {self.lowest_low}, Open Long Trade: {self.open_long_trade}, Open Short Trade: {self.open_short_trade}"


tessa = Ticker(21, "Charlie", 1.618, 0.96)
print(tessa)