import logging
import numpy as np

#TODO quadruple check for lookahead bias

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

def feature(adapter, index, vars=None, other_features=None):
    rate = vars['rate'] or 20
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    data = adapter.get_bars(index, count+rate+1, unit, size)
    if len(data) < count:
        return []

    price_offset = data[-1,3]
    ema = np.expand_dims(numpy_ewma_vectorized_v2(data[:,3], rate), axis=1)[-count:]
    ema -= price_offset
    if ema.shape[0] < count:
        return []

    if feature.sample is None:
        feature.sample = ema
    else:
        feature.sample[:] = ema

    if np.isnan(feature.sample[:]).any():
        logging.warn(f"Found NaN in ema at index {index}.")
        return []

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_2011.csv", "resolution": 1 },
        "features": [ { "rate": 10, "count": 10, "size": 1, "unit": "min" } ]
    }
    adapter = loader.load_adapter(json=rds)
    data = feature(adapter, 550000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()