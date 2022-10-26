import logging
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

LAST_DATETIME, LAST_SAMPLE = {}, {}
def feature(adapter, index, vars=None, other_features=None):
    global LAST_DATETIME, LAST_SAMPLE
    unit = vars['unit'] or 'sec'
    dt = adapter.get_timestamp(index)
    datetime = adapter.format_datetime(dt, unit)
    if unit in LAST_DATETIME and datetime == LAST_DATETIME[unit]:
        return LAST_SAMPLE[unit]

    rate = vars['rate'] or 20
    count = vars['count'] or 60
    size = vars['size'] or 1

    # get data
    data = adapter.get_bars(index, count+rate+1, unit, size)
    if len(data) < count:
        return []
    v = data[:, 5]
    h = data[:, 1]
    l = data[:, 2]

    # compute
    vwap = np.cumsum(v*(h+l)/2) / np.cumsum(v)
    # vwap -= vwap[-1]
    vwap_window = sliding_window_view(vwap, window_shape=rate)
    vwap_ma = np.mean(vwap_window, axis=1)

    # shape
    vwap = vwap[-count:]
    if vwap.shape[0] < count:
        return []

    vwap_ma = vwap_ma[-count:]
    if vwap_ma.shape[0] < count:
        return []

    # combine
    if feature.sample is None:
        feature.sample = np.hstack([vwap, vwap_ma])
    else:
        feature.sample[:] = np.hstack([vwap, vwap_ma])

    LAST_DATETIME[unit], LAST_SAMPLE[unit] = datetime, feature.sample

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_2010.csv", "resolution": 1 },
        "features": [ { "rate": 10, "count": 10, "size": 1, "unit": "min" } ]
    }
    adapter = loader.load_adapter(json=rds)
    data = feature(adapter, 550000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()