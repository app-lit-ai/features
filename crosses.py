import logging
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

#TODO quadruple check for lookahead bias

def get_crosses(diffs):
    last_is_pos = diffs[0] >= 0
    retval = 0
    cross_index = -1
    for i, diff in enumerate(diffs[1:]):
        is_pos = diff >= 0
        if is_pos != last_is_pos:
            if is_pos:
                retval = 1
            else:
                retval = -1
            cross_index = i
        last_is_pos = is_pos
    return retval, (len(diffs[1:]) - cross_index)

LAST_DATE, LAST_SAMPLE = None, None
def feature(adapter, index, vars=None, other_features=None):

    global LAST_DATE, LAST_SAMPLE
    dt = adapter.get_timestamp(index)
    date = f"{dt.year}-{dt.month}-{dt.day}"
    if date == LAST_DATE:
        return LAST_SAMPLE

    count, size, unit = 50, 1, "day"
    data_day = adapter.get_bars(index, count+(count-1), unit, size)
    if data_day.shape[0] < count+(count-1):
        return []

    window = sliding_window_view(data_day[:,3], window_shape=50, axis=0)
    sma_50day = np.mean(window, axis=1)

    window = sliding_window_view(data_day[-39:,3], window_shape=20, axis=0)
    sma_20day = np.mean(window, axis=1)
    
    window = sliding_window_view(data_day[-19:,3], window_shape=10, axis=0)
    sma_10day = np.mean(window, axis=1)

    window = sliding_window_view(data_day[-9:,3], window_shape=5, axis=0)
    sma_5day = np.mean(window, axis=1)

    feature.sample = np.asarray([
        get_crosses((sma_5day - sma_10day[-5:])),
        get_crosses((sma_5day - sma_20day[-5:])), get_crosses((sma_10day - sma_20day[-10:])),
        get_crosses((sma_5day - sma_50day[-5:])), get_crosses((sma_10day - sma_50day[-10:])), get_crosses((sma_20day - sma_50day[-20:]))
    ]).flatten()

    if np.isnan(feature.sample[:]).any():
        logging.warn(f"Found NaN in crosses at index {index}.")
        return []

    LAST_DATE, LAST_SAMPLE = date, feature.sample

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_2011.csv", "resolution": 1 },
        "features": [ { } ]
    }
    adapter = loader.load_adapter(json=rds)
    index = 1670003
    data = feature(adapter, index, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()