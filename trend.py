import logging
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

LAST_DATETIME, LAST_SAMPLE = None, None
def feature(adapter, index, vars=None, other_features=None):
    global LAST_DATETIME, LAST_SAMPLE
    dt = adapter.get_timestamp(index)
    datetime = dt.strftime('%Y-%m-%d %H:%M')
    if datetime == LAST_DATETIME:
        return LAST_SAMPLE[:]

    count, size, unit = 50, 1, "day"
    data_day = adapter.get_bars(index, count+(count-1), unit, size)
    if len(data_day) == 0 or data_day.shape[0] < count+(count-1):
        LAST_DATETIME, LAST_SAMPLE = datetime, []
        return []

    count, size, unit = 24, 1, "hour"
    data_hour = adapter.get_bars(index, count+(count-1), unit, size)
    if len(data_hour) == 0 or data_hour.shape[0] < count+(count-1):
        LAST_DATETIME, LAST_SAMPLE = datetime, []
        return []

    count, size, unit = 60, 1, "min"
    data_min = adapter.get_bars(index, count+(count-1), unit, size)
    if len(data_min) == 0 or data_min.shape[0] < count+(count-1):
        LAST_DATETIME, LAST_SAMPLE = datetime, []
        return []

    window = sliding_window_view(data_day[:,3], window_shape=50, axis=0)
    sma_50day = np.mean(window, axis=1)

    window = sliding_window_view(data_day[-39:,3], window_shape=20, axis=0)
    sma_20day = np.mean(window, axis=1)
    
    window = sliding_window_view(data_day[-19:,3], window_shape=10, axis=0)
    sma_10day = np.mean(window, axis=1)

    window = sliding_window_view(data_day[-9:,3], window_shape=5, axis=0)
    sma_5day = np.mean(window, axis=1)

    window = sliding_window_view(data_hour[-47:,3], window_shape=24, axis=0)
    sma_24hour = np.mean(window, axis=1)

    window = sliding_window_view(data_min[-119:,3], window_shape=60, axis=0)
    sma_60min = np.mean(window, axis=1)

    fit = lambda x: np.polyfit(range(len(x)), x, deg=1)[0]
    feature.sample = np.asarray([
        fit(sma_60min), fit(sma_24hour), fit(sma_5day), fit(sma_10day), fit(sma_20day), fit(sma_50day)
    ]).flatten()

    LAST_DATETIME, LAST_SAMPLE = datetime, feature.sample[:]

    if np.isnan(feature.sample[:]).any():
        logging.warn(f"Found NaN in trend at index {index}.")
        LAST_SAMPLE = []
        return []

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_2011.csv", "resolution": 1 },
        "features": [ { } ]
    }
    adapter = loader.load_adapter(json=rds)
    index = 1100000
    data = feature(adapter, index, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()