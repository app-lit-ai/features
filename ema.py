import logging
import numpy as np

#TODO quadruple check for lookahead bias

def interrogate():
    return [
        { "name": "rate", "type": "number" },
        { "name": "count", "type": "number" },
        { "name": "size", "type": "number" },
        { "name": "unit", "type": "string" }
    ]

def numpy_ewma_vectorized_v2(data, window):

    alpha = 2 /(window + 1.0)
    alpha_rev = 1-alpha
    n = data.shape[0]

    pows = alpha_rev**(np.arange(n+1))

    scale_arr = 1/pows[:-1]
    offset = data[0]*pows[1:]
    pw0 = alpha*alpha_rev**(n-1)

    mult = data*pw0*scale_arr
    cumsums = mult.cumsum()
    out = offset + cumsums*scale_arr[::-1]
    return out

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

    data = adapter.get_bars(index, count+rate+1, unit, size)
    if len(data) < count:
        return []

    # price_offset = data[-1,3]
    ema = np.expand_dims(numpy_ewma_vectorized_v2(data[:,3], rate), axis=1)[-count:]
    # ema -= price_offset
    if ema.shape[0] < count:
        return []

    if feature.sample is None:
        feature.sample = ema
    else:
        feature.sample[:] = ema

    if np.isnan(feature.sample[:]).any():
        logging.warn(f"Found NaN in ema at index {index}.")
        return []

    LAST_DATETIME[unit], LAST_SAMPLE[unit] = datetime, feature.sample

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_ALL.csv", "resolution": 1 },
        "features": [ { "rate": 60, "count": 60, "size": 1, "unit": "sec" } ]
    }
    adapter = loader.load_adapter(json=rds)
    data = feature(adapter, 100000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()