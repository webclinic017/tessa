# Ticker 
 - instrument_token = instrument_token
        self.tradingsymbol = tradingsymbol
        self.tick_store = [] # store the last_traded_prices
        self.volume = 0 # store the volume of the current_candle
        self.candles = pd.DataFrame(kite.historical_data(instrument_token, previous_trading_day + " 15:00:00", previous_trading_day + " 15:21:00", "minute"))
        self.candle_writer = csv.writer(open(tradingsymbol+ ".csv", "w"))
        self.tick_writer = csv.writer(open(tradingsymbol + "_ticks.csv", "w"))
        self.log = open(tradingsymbol + "_log.txt", "w")
        self.buy_orderid = ""
        self.stoploss_orderid = ""
        self.sell_orderid = ""

# Order management


# Algo


Websocket -> Algo (Ticker) <-> Order Placement
