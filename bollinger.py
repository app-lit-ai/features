import logging
import numpy as np
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

#TODO quadruple check for lookahead bias

def feature(adapter, index, vars=None, other_features=None):
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
    rate = vars['rate'] or 20
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    data = adapter.get_bars(index, count, unit, size)
    if len(data) != count:
        return []
    # price_offset = data[-1,3]

    window = sliding_window_view(data[:,3], window_shape=rate)
    sma = np.mean(window, axis=1)
    std = np.std(window, axis=1, ddof=1)
    up, down = sma + std * 2, sma - std * 2

    if feature.sample is None:
        feature.sample = np.swapaxes(np.asarray([down, up]), 0, 1)
    else:
        feature.sample[:] = np.swapaxes(np.asarray([down, up]), 0, 1)

    # feature.sample = feature.sample - price_offset

    if np.isnan(feature.sample[:]).any():
        logging.warn(f"Found NaN in bollinger at index {index}.")
        return []

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/test.csv" },
        "features": [ { "rate": 5, "count": 50, "size": 1, "unit": "sec" } ]
    }
    adapter = loader.load_adapter(json=rds)
    data = feature(adapter, 20000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()