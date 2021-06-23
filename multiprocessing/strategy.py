from helpers import *
from talib import RSI


def on_candle(instrument_token):
    ticker = tickers[instrument_token]

    candles = ticker.get_candles().copy()
    relative_candles = tickers[instrument_token].get_relative_ticker(
    ).get_candles().copy()

    candles['rsi13'] = RSI(candles['close'], timeperiod=13)
    candles['rsi21'] = RSI(candles['close'], timeperiod=21)
    candles['ema21'] = EMA(candles['close'], timeperiod=21)
    candles = SUPERTREND(candles, period=21, multiplier=3)
    candles = SUPERTREND(candles, period=13, multiplier=2)
    candles = SUPERTREND(candles, period=8, multiplier=1)

    penultimate_candle = candles.iloc[-2]
    last_candle = candles.iloc[-1]
    tradingsymbol = ticker.tradingsymbol

    relative_candles['rsi13'] = RSI(relative_candles['close'], timeperiod=13)
    relative_candles['rsi21'] = RSI(relative_candles['close'], timeperiod=21)
    relative_candles['ema21'] = EMA(relative_candles['close'], timeperiod=21)
    relative_candles = SUPERTREND(relative_candles, period=21, multiplier=3)
    relative_candles = SUPERTREND(relative_candles, period=13, multiplier=2)
    relative_candles = SUPERTREND(relative_candles, period=8, multiplier=1)

    last_relative_candle = relative_candles.iloc[-1]
    penultimate_relative_candle = relative_candles.iloc[-2]

    try:
        if instrument_token not in open_trades:
            if not penultimate_candle.STX_13:
                if not penultimate_candle.STX_8:
                    if last_candle.STX_21:
                        if last_candle.STX_13:
                            if last_candle.STX_8:

                                try:

                                    last_traded_price = get_ltp(
                                        instrument_token)
                                    timestamp = get_timestamp()
                                    buy_order_id = kite.place_order(tradingsymbol=tradingsymbol,
                                                                    exchange=kite.EXCHANGE_NFO,
                                                                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                    quantity=25,
                                                                    order_type=kite.ORDER_TYPE_LIMIT,
                                                                    product=kite.PRODUCT_NRML,
                                                                    variety=kite.VARIETY_REGULAR,
                                                                    price=last_traded_price,
                                                                    )
                                    open_trades.append(instrument_token)
                                    print(
                                        f"Triple Supertrend Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")
                                    orderbook.write(
                                        f"\nTriple Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

                                except:
                                    print(
                                        f"Eroor placing Triple Supertrend Buy Order for {tradingsymbol} succesfully orders {buy_order_id}")

                                    # stoploss_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
                                    #         exchange=kite.EXCHANGE_NFO,
                                    #         transaction_type=kite.TRANSACTION_TYPE_SELL,
                                    #         quantity=25,
                                    #         order_type=kite.ORDER_TYPE_SL,
                                    #         product=kite.PRODUCT_NRML,
                                    #         variety=kite.VARIETY_REGULAR,
                                    #         trigger_price=last_traded_price-21,
                                    #         price=last_traded_price-21,
                                    #         )
                                    # print(f"Sell Order placed for {tradingsymbol} succesfully orders {stoploss_order_id}")

                                print(
                                    f"Triple Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                                ticker.log.write(
                                    f"\nTriple Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

                                tradebook.write(
                                    f"\nTriple Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

        if instrument_token not in open_trades:
            if not last_relative_candle.STX_21:
                if not last_relative_candle.STX_13:
                    if not last_relative_candle.STX_8:
                        if last_candle.STX_13:
                            if last_candle.STX_8:

                                try:

                                    last_traded_price = get_ltp(
                                        instrument_token)
                                    timestamp = get_timestamp()
                                    buy_order_id = kite.place_order(tradingsymbol=tradingsymbol,
                                                                    exchange=kite.EXCHANGE_NFO,
                                                                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                    quantity=25,
                                                                    order_type=kite.ORDER_TYPE_LIMIT,
                                                                    product=kite.PRODUCT_NRML,
                                                                    variety=kite.VARIETY_REGULAR,
                                                                    price=last_traded_price,
                                                                    )
                                    open_trades.append(instrument_token)
                                    print(
                                        f"Relative Supertrend Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")
                                    orderbook.write(
                                        f"\nRelative Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

                                except:
                                    print(
                                        f"Error placing Relative Supertrend Buy Order for {tradingsymbol} succesfully orders {buy_order_id}")

                                print(
                                    f"Relative Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                                ticker.log.write(
                                    f"\nRelative Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                                tradebook.write(
                                    f"\nRelative Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

        if instrument_token not in open_trades:

            if not last_relative_candle.STX_13:
                if not last_relative_candle.STX_8:
                    if last_candle.STX_13:
                        if last_candle.STX_8:

                            try:

                                last_traded_price = get_ltp(
                                    instrument_token)
                                timestamp = get_timestamp()
                                buy_order_id = kite.place_order(tradingsymbol=tradingsymbol,
                                                                exchange=kite.EXCHANGE_NFO,
                                                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                quantity=25,
                                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                                product=kite.PRODUCT_NRML,
                                                                variety=kite.VARIETY_REGULAR,
                                                                price=last_traded_price,
                                                                )
                                open_trades.append(instrument_token)
                                print(
                                    f"Relative Supertrend Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")
                                orderbook.write(
                                    f"\nRelative Supertrend: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

                            except:
                                print(
                                    f"Error placing Relative Supertrend Buy Order for {tradingsymbol} succesfully orders {buy_order_id}")

                            print(
                                f"Relative Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                            ticker.log.write(
                                f"\nRelative Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                            tradebook.write(
                                f"\nRelative Supertrend buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

        if instrument_token not in open_trades:
            if penultimate_candle.rsi21 < 21:
                if last_candle.rsi21 >= 21:
                    if penultimate_candle.rsi13 < 13:
                        if last_candle.rsi13 >= 13:

                            try:

                                last_traded_price = get_ltp(instrument_token)
                                timestamp = get_timestamp()
                                buy_order_id = kite.place_order(tradingsymbol=tradingsymbol,
                                                                exchange=kite.EXCHANGE_NFO,
                                                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                quantity=25,
                                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                                product=kite.PRODUCT_NRML,
                                                                variety=kite.VARIETY_REGULAR,
                                                                price=last_traded_price,
                                                                )
                                open_trades.append(instrument_token)
                                print(
                                    f"Triple RSI Buy Order placed for {tradingsymbol} succesfully orders {buy_order_id}")
                                orderbook.write(
                                    f"\nTriple RSI: Bought {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                            except:
                                print(
                                    f"Error placing Triple RSI Buy Order for {tradingsymbol} succesfully orders {buy_order_id}")
                            print(
                                f"Triple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                            ticker.log.write(
                                f"\nTriple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

                            tradebook.write(
                                f"\nTriple RSI buy signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

        elif instrument_token in open_trades:
            if not last_candle.STX_13:

                try:

                    last_traded_price = get_ltp(instrument_token)
                    timestamp = get_timestamp()
                    sell_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
                                                     exchange=kite.EXCHANGE_NFO,
                                                     transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                     quantity=25,
                                                     order_type=kite.ORDER_TYPE_LIMIT,
                                                     product=kite.PRODUCT_NRML,
                                                     variety=kite.VARIETY_REGULAR,
                                                     price=last_traded_price,
                                                     )
                    open_trades.remove(instrument_token)
                    print(
                        f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                    orderbook.write(
                        f"\nTriple Supertrend: Supertrend 13 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                except:
                    print(
                        f"Error Triple Supertrend 13 placing Sell Order for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")

                print(
                    f"Triple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                ticker.log.write(
                    f"\nTriple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")
                tradebook.write(
                    f"\nTriple Supertrend 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price} ")

        elif instrument_token in open_trades:
            if last_relative_candle.STX_13:
                if last_relative_candle.STX_8:

                    try:

                        last_traded_price = get_ltp(instrument_token)
                        timestamp = get_timestamp()
                        sell_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
                                                         exchange=kite.EXCHANGE_NFO,
                                                         transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                         quantity=25,
                                                         order_type=kite.ORDER_TYPE_LIMIT,
                                                         product=kite.PRODUCT_NRML,
                                                         variety=kite.VARIETY_REGULAR,
                                                         price=last_traded_price,
                                                         )
                        open_trades.remove(instrument_token)
                        print(
                            f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                        orderbook.write(
                            f"\nRelative Supertrend: Supertrend 13 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                    except:
                        print(
                            f"Error placing Sell Order for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                    print(
                        f"Relative Double Supertrend Sell signal for {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                    ticker.log.write(
                        f"\nRelative Double Supertrend Sell signal for {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                    tradebook.write(
                        f"\nRelative Double Supertrend Sell signal for {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

        elif instrument_token in open_trades:
            if penultimate_candle.rsi13 > 87:
                if last_candle.rsi13 <= 87:

                    try:

                        last_traded_price = get_ltp(instrument_token)
                        timestamp = get_timestamp()
                        sell_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
                                                         exchange=kite.EXCHANGE_NFO,
                                                         transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                         quantity=25,
                                                         order_type=kite.ORDER_TYPE_LIMIT,
                                                         product=kite.PRODUCT_NRML,
                                                         variety=kite.VARIETY_REGULAR,
                                                         price=last_traded_price,
                                                         )
                        open_trades.remove(instrument_token)
                        print(
                            f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                        orderbook.write(
                            f"\nTriple RSI: RSI 13 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                    except:
                        print(
                            f"Error placing Sell Order for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                    print(
                        f"Triple RSI 13 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                    ticker.log.write(
                        f"\nTriple RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                    tradebook.write(
                        f"\nTriple RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")

        elif instrument_token in open_trades:
            if last_relative_candle.rsi21 < 21:
                if last_relative_candle.rsi21 >= 21:

                    try:

                        last_traded_price = get_ltp(instrument_token)
                        timestamp = get_timestamp()
                        sell_order_id = kite.place_order(tradingsymbol=tickertape[instrument_token],
                                                         exchange=kite.EXCHANGE_NFO,
                                                         transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                         quantity=25,
                                                         order_type=kite.ORDER_TYPE_LIMIT,
                                                         product=kite.PRODUCT_NRML,
                                                         variety=kite.VARIETY_REGULAR,
                                                         price=last_traded_price,
                                                         )
                        open_trades.remove(instrument_token)
                        print(
                            f"Sell Order placed for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                        orderbook.write(
                            f"\nRelative RSI: RSI 21 - Sold {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                    except:
                        print(
                            f"Error placing Sell Order for {tradingsymbol} succesfully orders. Order ID: {sell_order_id}")
                    print(
                        f"Triple Relative RSI 21 sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                    ticker.log.write(
                        f"\nTriple Relative RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
                    tradebook.write(
                        f"\nTriple Relative RSI sell signal, {tradingsymbol} at {timestamp} ltp: {last_traded_price}")
    except:
        print("Error in execution")
        pass
