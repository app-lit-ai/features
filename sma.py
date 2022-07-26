"""
Parameters
----------
rate : number
    When calculating across a window, the number of bars to include in that window; e.g. [10]-day moving average for 30 days 
count : number
    The number of bars; e.g. [10] 1-second bars
size : number
    The number of units in each bar; e.g. 10 [1]-second bars
unit : string
    Either hour, minute, or second; e.g. 10 1-[second] bars
"""
import logging
from typing import Callable
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

#TODO quadruple check for lookahead bias

def calc_rsi(over: np.ndarray, fn_roll: Callable, window_size) -> pd.Series:
    over = pd.Series(over)
    delta = over.diff()
    delta = delta[1:] 
    up, down = delta.clip(lower=0), delta.clip(upper=0).abs()
    roll_up, roll_down = fn_roll(up), fn_roll(down)
    rs = roll_up / roll_down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi[:] = np.select([roll_down == 0, roll_up == 0, True], [100, 0, rsi])
    rsi.name = 'rsi'
    valid_rsi = rsi[window_size - 1:]
    assert ((0 <= valid_rsi) & (valid_rsi <= 100)).all()
    return rsi

def feature(adapter, index, vars=None, other_features=None):
    rate = vars['rate'] or 20
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    data = adapter.get_bars(index, count+rate+1, unit, size)
    if len(data) < count:
        return []

    # price_offset = data[-1,3]
    window = sliding_window_view(data[:,3], window_shape=rate)
    sma = np.mean(window, axis=1)
    #sma -= price_offset
    sma = np.expand_dims(sma, axis=1)[-count:]
    if sma.shape[0] < count:
        return []

    rsi_ema = np.expand_dims(calc_rsi(data[:,3], lambda s: s.ewm(span=rate).mean(), rate), axis=1)[-count:]
    rsi = rsi_ema / 100
    if rsi.shape[0] < count:
        return []

    # rsi_sma = calc_rsi(price, lambda s: s.rolling(rate).mean(), rate)
    # rsi_rma = calc_rsi(price, lambda s: s.ewm(alpha=1 / rate).mean(), rate) 

    if feature.sample is None:
        feature.sample = np.hstack([sma, rsi])
    else:
        feature.sample[:] = np.hstack([sma, rsi])

    if np.isnan(feature.sample[:]).any():
        logging.warn(f"Found NaN in sma at index {index}.")
        return []

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_2011.csv", "resolution": 1 },
        "features": [ { "rate": 60, "count": 60, "size": 1, "unit": "sec" } ]
    }
    adapter = loader.load_adapter(json=rds)
    index = 1650000
    data = feature(adapter, index, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()