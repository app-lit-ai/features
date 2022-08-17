from typing import Callable
import numpy as np
import pandas as pd

#TODO quadruple check for lookahead bias

def calc_rsi(over: pd.Series, fn_roll: Callable, window_size) -> pd.Series:
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

    df = adapter.get_dataframe(index, count, unit, size)
    df = df.set_index('Date-Time')
    resample_unit = adapter.translate_resample_unit(unit)    
    resampled = df.resample(f"{size}{resample_unit}")

    price = resampled['Price'].mean()
    sma = np.expand_dims(price.rolling(rate).mean(), axis=1)[-count:]
    sma -= sma[-1]
    
    vwap = np.expand_dims(resampled['Market VWAP'].mean().rolling(rate).mean(), axis=1)[-count:]
    vwap -= vwap[-1]

    rsi_ema = np.expand_dims(calc_rsi(price, lambda s: s.ewm(span=rate).mean(), rate), axis=1)[-count:]
    rsi = rsi_ema - rsi_ema.max()
    # rsi_sma = calc_rsi(price, lambda s: s.rolling(rate).mean(), rate)
    # rsi_rma = calc_rsi(price, lambda s: s.ewm(alpha=1 / rate).mean(), rate) 

    feature.sample = np.hstack([sma, vwap, rsi])

    return feature.sample[:]

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters_csv", "path": "/data/raw/test.csv" },
        "features": [ { "rate": 5, "count": 60, "size": 1, "unit": "sec" } ]
    }
    adapter = loader.load_adapter(json=rds, limit=20000)
    data = feature(adapter, 5000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()