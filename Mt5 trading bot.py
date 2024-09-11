import MetaTrader5 as mt
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
import talib as ta

# Initialize MetaTrader5
mt.initialize()

# Login to the account
login = 7453068
server = 'VantageInternational-Demo'
password = '*******'
mt.login(login, password, server)

# Define constants
ticker = 'SP500'
interval = mt.TIMEFRAME_H1
from_date = datetime.now()
no_of_rows = 100
rates = mt.copy_rates_from(ticker, interval, from_date, no_of_rows)

# Fetch account information
account_info = mt.account_info()
num_symbols = mt.symbols_total()
symbol_info = mt.symbols_get()
mt.symbol_info(ticker)._asdict() 


# Fetch historical data
ohlc = pd.DataFrame(mt.copy_rates_range(ticker, mt.TIMEFRAME_H1, datetime(2017, 9, 18), datetime.now()))
ohlc['time'] = pd.to_datetime(ohlc['time'], unit='s')
print(ohlc)

# Define the period for ADX calculation
InpPeriodADX = 21

# Initialize buffers for ADX calculation
ExtADXBuffer = np.zeros_like(ohlc['close'])
ExtPDIBuffer = np.zeros_like(ohlc['close'])
ExtNDIBuffer = np.zeros_like(ohlc['close'])
ExtPDBuffer = np.zeros_like(ohlc['close'])
ExtNDBuffer = np.zeros_like(ohlc['close'])
ExtTmpBuffer = np.zeros_like(ohlc['close'])

def exponential_moving_average(index, period, prev_ema, buffer):
    alpha = 2 / (period + 1)
    if index == 0:
        return buffer[0]
    else:
        return alpha * buffer[index] + (1 - alpha) * prev_ema

def calculate_adx(high, low, close, period):
    rates_total = len(close)
    if rates_total < period:
        return

    start = 1
    ExtPDIBuffer[0] = 0.0
    ExtNDIBuffer[0] = 0.0
    ExtADXBuffer[0] = 0.0

    for i in range(start, rates_total):
        high_price = high[i]
        prev_high = high[i - 1]
        low_price = low[i]
        prev_low = low[i - 1]
        prev_close = close[i - 1]

        tmp_pos = high_price - prev_high
        tmp_neg = prev_low - low_price

        if tmp_pos < 0.0:
            tmp_pos = 0.0
        if tmp_neg < 0.0:
            tmp_neg = 0.0
        if tmp_pos > tmp_neg:
            tmp_neg = 0.0
        else:
            if tmp_pos < tmp_neg:
                tmp_pos = 0.0
            else:
                tmp_pos = 0.0
                tmp_neg = 0.0

        tr = max(max(abs(high_price - low_price), abs(high_price - prev_close)), abs(low_price - prev_close))
        if tr != 0.0:
            ExtPDBuffer[i] = 100.0 * tmp_pos / tr
            ExtNDBuffer[i] = 100.0 * tmp_neg / tr
        else:
            ExtPDBuffer[i] = 0.0
            ExtNDBuffer[i] = 0.0

        ExtPDIBuffer[i] = exponential_moving_average(i, period, ExtPDIBuffer[i - 1], ExtPDBuffer)
        ExtNDIBuffer[i] = exponential_moving_average(i, period, ExtNDIBuffer[i - 1], ExtNDBuffer)

        tmp = ExtPDIBuffer[i] + ExtNDIBuffer[i]
        if tmp != 0.0:
            tmp = 100.0 * abs((ExtPDIBuffer[i] - ExtNDIBuffer[i]) / tmp)
        else:
            tmp = 0.0
        ExtTmpBuffer[i] = tmp

        ExtADXBuffer[i] = exponential_moving_average(i, period, ExtADXBuffer[i - 1], ExtTmpBuffer)

# Call the calculate_adx function
calculate_adx(ohlc['high'].values, ohlc['low'].values, ohlc['close'].values, InpPeriodADX)

# Add the results to the dataframe
ohlc['ADX'] = ExtADXBuffer
ohlc['+DI'] = ExtPDIBuffer
ohlc['-DI'] = ExtNDIBuffer


# #royal scalping placeholder

# Calculate indicators
# ohlc = calculate_royal_scalping(ohlc)
ohlc['CCI'] = ta.CCI(ohlc['high'], ohlc['low'], ohlc['close'], timeperiod=1000)

pd_cci = pd.DataFrame(ohlc['CCI'])
pd_cci['time'] = ohlc['time']
print(pd_cci)


pd_adx = pd.DataFrame(ohlc['ADX'])
pd_adx['time'] = ohlc['time']
print(pd_adx)


# Define trading functions
def create_order(ticker, qty, order_type, price, sl, tp, comment):
    request = {
        "action": mt.TRADE_ACTION_DEAL,
        "symbol": ticker,
        "volume": qty,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "comment": comment,
        "type_time": mt.ORDER_TIME_GTC,
        "type_filling": mt.ORDER_FILLING_IOC,
    }
    order = mt.order_send(request)
    return order

def close_order(ticker, qty, order_type, price, position, comment):
    request = {
        "action": mt.TRADE_ACTION_DEAL,
        "symbol": ticker,
        "volume": qty,
        "type": order_type,
        "position": position,
        "price": price,
        "comment": comment,
        "type_time": mt.ORDER_TIME_GTC,
        "type_filling": mt.ORDER_FILLING_IOC,
    }
    order = mt.order_send(request)
    return order

# Trading logic
def trading_strategy():
    current_adx = ohlc['ADX'].iloc[-1]
    current_cci = ohlc['CCI'].iloc[-1]
    current_royal_scalping = ohlc['Royal_Scalping'].iloc[-1]
    previous_cci = ohlc['CCI'].iloc[-2]
    previous_royal_scalping = ohlc['Royal_Scalping'].iloc[-2]
    previous_adx = ohlc['ADX'].iloc[-2]

    #defining position variable
    positions = mt.positions_get(symbol=ticker)

     # Pair of positions logic
    if current_adx > 20 and current_adx > previous_adx:
        if current_cci > 0 and current_cci > previous_cci and (current_royal_scalping > 80 or (previous_royal_scalping < 20 and current_royal_scalping > 20)):
            create_order(ticker, 0.1, mt.ORDER_TYPE_BUY, mt.symbol_info_tick(ticker).ask, None, None, "Buy order - 1/2 pair of positions")
            create_order(ticker, 0.1, mt.ORDER_TYPE_BUY, mt.symbol_info_tick(ticker).ask, None, None, "Buy order - 2/2 pair of positions")
        elif current_cci < 0 and current_cci < previous_cci and (current_royal_scalping < 20 or (previous_royal_scalping > 80 and current_royal_scalping < 80)):
            create_order(ticker, 0.1, mt.ORDER_TYPE_SELL, mt.symbol_info_tick(ticker).bid, None, None, "Sell order - 1/2 pair of positions")
            create_order(ticker, 0.1, mt.ORDER_TYPE_SELL, mt.symbol_info_tick(ticker).bid, None, None, "Sell order - 2/2 pair of positions")
     
     #Single positions logic 
    if not positions:
        if current_adx > 20 and current_adx > previous_adx:
            if previous_cci < 40 and current_cci > 40 and current_royal_scalping > 80:
                create_order(ticker, 0.1, mt.ORDER_TYPE_BUY, mt.symbol_info_tick(ticker).ask, None, None, "Buy order - single position")
            elif previous_cci > -40 and current_cci < -40 and current_royal_scalping < 20:
                create_order(ticker, 0.1, mt.ORDER_TYPE_SELL, mt.symbol_info_tick(ticker).bid, None, None, "Sell order - single position")    

    # Implement stop loss logic for all positions
    if current_cci < 0 and previous_cci > 0:
        positions = mt.positions_get(symbol=ticker)
        for position in positions:
            if position.type == mt.ORDER_TYPE_BUY:
                close_order(ticker, position.volume, mt.ORDER_TYPE_SELL, mt.symbol_info_tick(ticker).bid, position.ticket, "Stop loss for buy")

    if current_cci > 0 and previous_cci < 0:
        positions = mt.positions_get(symbol=ticker)
        for position in positions:
            if position.type == mt.ORDER_TYPE_SELL:
                close_order(ticker, position.volume, mt.ORDER_TYPE_BUY, mt.symbol_info_tick(ticker).ask, position.ticket, "Stop loss for sell")

    # Implement take profit logics :
    positions = mt.positions_get(symbol=ticker)
    buy_positions = [p for p in positions if p.type == mt.ORDER_TYPE_BUY]
    sell_positions = [p for p in positions if p.type == mt.ORDER_TYPE_SELL]
    
 # For 1 position in the pair of buy positions
    for position in buy_positions:
     if "1/2 pair of positions" in position.comment:
        if current_cci < 70 and previous_cci > 70:
            close_order(ticker, position.volume, mt.ORDER_TYPE_SELL, mt.symbol_info_tick(ticker).bid, position.ticket, "Take profit for buy - 1/2 pair of positions")
     elif "2/2 pair of positions" in position.comment:
        if current_royal_scalping < 80 and previous_royal_scalping > 80:
            close_order(ticker, position.volume, mt.ORDER_TYPE_SELL, mt.symbol_info_tick(ticker).bid, position.ticket, "Take profit for buy - 2/2 pair of positions")

 # For 1 position in the pair of sell positions
    for position in sell_positions:
     if "1/2 pair of positions" in position.comment:
        if current_cci > -70 and previous_cci < -70:
            close_order(ticker, position.volume, mt.ORDER_TYPE_BUY, mt.symbol_info_tick(ticker).ask, position.ticket, "Take profit for sell - 1/2 pair of positions")
     elif "2/2 pair of positions" in position.comment:
        if current_royal_scalping > 20 and previous_royal_scalping < 20:
            close_order(ticker, position.volume, mt.ORDER_TYPE_BUY, mt.symbol_info_tick(ticker).ask, position.ticket, "Take profit for sell - 2/2 pair of positions")

 # For all positions in the buy pair
    if len(buy_positions) > 0:
     if (current_cci < 70 and current_royal_scalping < 80 and previous_royal_scalping > 80) or (current_royal_scalping < 80 and previous_royal_scalping > 80 and current_cci >= 70):
        for position in buy_positions:
            if "single" not in position.comment:
                close_order(ticker, position.volume, mt.ORDER_TYPE_SELL, mt.symbol_info_tick(ticker).bid, position.ticket, "Take profit for buy - all pairs positions")

 # For all positions in the sell pair  
    if len(sell_positions) > 0:
     if (current_cci > -70 and current_royal_scalping > 20 and previous_royal_scalping < 20) or (current_royal_scalping > 20 and previous_royal_scalping < 20 and current_cci <= -70):
        for position in sell_positions:
            if "single" not in position.comment:
                close_order(ticker, position.volume, mt.ORDER_TYPE_BUY, mt.symbol_info_tick(ticker).ask, position.ticket, "Take profit for sell - all pairs positions")
        
 # For single positions
    for position in positions:
        if "single" in position.comment:
            if position.type == mt.ORDER_TYPE_BUY and current_cci < 70 and previous_cci > 70:
                close_order(ticker, position.volume, mt.ORDER_TYPE_SELL, mt.symbol_info_tick(ticker).bid, position.ticket, "Take profit for buy - single position")
            elif position.type == mt.ORDER_TYPE_SELL and current_cci > -70 and previous_cci < -70:
                close_order(ticker, position.volume, mt.ORDER_TYPE_BUY, mt.symbol_info_tick(ticker).ask, position.ticket, "Take profit for sell - single position")
    



# Run the strategy
while True:
    trading_strategy()
    time.sleep(3600)  # Run every hour




