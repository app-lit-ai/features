import logging
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

#TODO quadruple check for lookahead bias

def feature(adapter, index, vars=None, other_features=None):
    rate = vars['rate'] or 20
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    # get data
    data = adapter.get_bars(index, count+rate+1, unit, size)
    if len(data) < count:
        return []
    v = data[:, 5]
    h = data[:, 1]
    l = data[:, 2]

    # compute
    vwap_ben = np.cumsum(v*(h+l)/2) / np.cumsum(v)
    vwap_ben -= vwap_ben[-1]
    vwap_ben_window = sliding_window_view(vwap_ben, window_shape=rate)
    vwap_ben_ma = np.mean(vwap_ben_window, axis=1)

    # shape
    vwap_ben = vwap_ben[-count:]
    if vwap_ben.shape[0] < count:
        return []

    vwap_ben_ma = vwap_ben_ma[-count:]
    if vwap_ben_ma.shape[0] < count:
        return []

    # combine
    if feature.sample is None:
        feature.sample = np.hstack([vwap_ben, vwap_ben_ma])
    else:
        feature.sample[:] = np.hstack([vwap_ben, vwap_ben_ma])

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