from Supertrend.threaded_supertrend import on_candle
import pandas as pd
from datetimemanager import previous_trading_day, get_timestamp
from main import kite
import csv
from _thread import start_new_thread
from helpers import *
import talib

class Ticker:
    def __init__(self, instrument_token, tradingsymbol) -> None:
        self.instrument_token = instrument_token
        self.tradingsymbol = tradingsymbol
        self.tick_store = [] # store the last_traded_prices
        self.volume = 0 # store the volume of the current_candle
        self.candles = pd.DataFrame(kite.historical_data(instrument_token, previous_trading_day + " 15:00:00", previous_trading_day + " 15:21:00", "minute"))
        self.candle_writer = csv.writer(open(tradingsymbol+ ".csv", "w"))
        self.tick_writer = csv.writer(open(tradingsymbol + "_ticks.csv", "w"))
        self.log = open(tradingsymbol + "_log.txt", "w")

    def write_tick(self, tick) -> None:
        ltp = tick['last_price']
        ohlc = tick['ohlc']
        last_quantity = tick['last_quantity']

        self.tick_writer.writerow(
            [get_timestamp(), ltp, last_quantity, ohlc])
        self.tick_store.append(ltp)
        self.volume += last_quantity
        if len(self.tick_store) == 210:
            self.write_candle()

    def write_candle(self) -> None:
        candle_open = self.tick_store[0]
        candle_high = max(self.tick_store)
        candle_low = min(self.tick_store)
        candle_close = self.tick_store[-1]
        candle_volume = self.volume
        candle_data = [get_timestamp(), candle_open, candle_high,
                    candle_low, candle_close, candle_volume]

        candle_dataframe_length = len(self.candles)
        self.candles.loc[candle_dataframe_length] = candle_data
        self.candle_writer.writerow(candle_data)

        self.tick_store = []
        self.volume = 0
        start_new_thread(self.on_candle, tuple())


    def on_candle(self) -> None:

        candle_df = self.candles.copy()
        
        candle_df['rsi13'] = RSI(candle_df['close'], timeperiod=13)
        candle_df['rsi21'] = RSI(candle_df['close'], timeperiod=21)
        candle_df['rsi34'] = RSI(candle_df['close'], timeperiod=34)
        candle_df['ema21'] = talib.EMA(candle_df['close'], timeperiod=21)
        candle_df['wma21'] = WMA(candle_df['close'], timeperiod=21)
        supertrend_df = SuperTrend(candle_df, period=21, multiplier=3)
        supertrend_df = SuperTrend(supertrend_df, period=13, multiplier=2)
        supertrend_df = SuperTrend(supertrend_df, period=8, multiplier=1)

        timestamp = get_timestamp()
        penultimate_candle = candle_df.iloc[-2]
        last_candle = candle_df.iloc[-1]
        
    
        super_candle = supertrend_df.iloc[-1]

        if instrument_token not in triple_trades:
            if super_candle.STX_21:
                if super_candle.STX_13:
                    if super_candle.STX_8:
                        triple_trades.append(instrument_token)
                        print(
                            f"Triple supertrend buy signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")
                        super_tradebook.write(
                            f"\nTriple supertrend buy signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")

            if penultimate_candle.rsi34 < 34:
                if last_candle.rsi34 >= 34:
                    if penultimate_candle.rsi21 < 21:
                        if last_candle.rsi21 >= 21:
                            if penultimate_candle.rsi13 < 13:
                                if last_candle.rsi13 >= 13:
                                    triple_trades.append(instrument_token)
                                    print(
                                        f"Triple RSI buy signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")
                                    rsi_tradebook.write(
                                        f"\nTriple RSI buy signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")

        elif instrument_token in triple_trades:
            if not super_candle.STX_13:
                triple_trades.remove(instrument_token)
                print(
                    f"Triple Supertrend sell signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")
                super_tradebook.write(
                    f"\nTriple Supertrend sell signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")
            elif penultimate_candle.rsi21 > 79:
                if last_candle.rsi21 <= 79:
                    triple_trades.remove(instrument_token)
                    print(
                        f"Triple RSI sell signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")
                    rsi_tradebook.write(
                        f"\nTriple RSI sell signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")

        if instrument_token not in double_trades:
            if super_candle.STX_13:
                if super_candle.STX_8:
                    if last_candle.ema21 < candle_close:
                        double_trades.append(instrument_token)
                        print(
                            f"Double supertrend buy signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")
                        double_tradebook.write(
                            f"\nDouble supertrend buy signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")

            if penultimate_candle.rsi21 < 21:
                if last_candle.rsi21 >= 21:
                    if penultimate_candle.rsi13 < 13:
                        if last_candle.rsi13 >= 13:
                            triple_trades.append(instrument_token)
                            print(
                                f"Double RSI buy signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")
                            rsi_tradebook.write(
                                f"\nDouble RSI buy signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")

        elif instrument_token in double_trades:
            if not super_candle.STX_8:
                double_trades.remove(instrument_token)
                print(
                    f"Supertrend 8 sell signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")
                super_tradebook.write(
                    f"\nSupertrend 8 sell signal, {self.tradingsymbol} at {timestamp} ltp: {ltp} ")
            elif penultimate_candle.rsi13 >= 87:
                if last_candle.rsi13 <= 87:
                    double_trades.remove(instrument_token)
                    print(
                        f"RSI 13 sell signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")
                    rsi_tradebook.write(
                        f"\nRSI 13 sell signal, {self.tradingsymbol} at {timestamp} ltp: {get_ltp(instrument_token)} ")

