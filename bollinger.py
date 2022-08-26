import numpy as np

#TODO quadruple check for lookahead bias

def feature(adapter, index, vars=None, other_features=None):
    rate = vars['rate'] or 20
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    df = adapter.get_dataframe(index, count * 2, unit, size)
    if len(df[rate:]) < count:
        return []

    df = df.set_index('Date-Time')
    resample_unit = adapter.translate_resample_unit(unit)    
    resampled = df.resample(f"{size}{resample_unit}")
    if len(resampled) < count:
        return []

    price = resampled['Price'].mean()
    price = price[price.notna()]

    window = price.rolling(rate)
    sma = np.expand_dims(window.mean(), axis=1)[-count:]
    std = np.expand_dims(window.std(), axis=1)[-count:]
    up, down = sma + std * 2, sma - std * 2

    if feature.sample is None:
        feature.sample = np.swapaxes(np.asarray([down[rate:], up[rate:]]), 0, 1)
    else:
        feature.sample[:] = np.swapaxes(np.asarray([down[rate:], up[rate:]]), 0, 1)

    feature.sample = feature.sample - df.Price.iloc[-1]

    assert not np.isnan(feature.sample[:]).any(), "Found NaN in feature."

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