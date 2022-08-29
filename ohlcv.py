import numpy as np

#TODO quadruple check for lookahead bias

def feature(adapter, index, vars=None, other_features=None):
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    df = adapter.get_dataframe(index, count*2, unit, size)
    if len(df) == 0:
        return []

    price_offset = df.Price.iloc[-1]
    df = df.set_index('Date-Time')
    resample_unit = f"{size}{adapter.translate_resample_unit(unit)}"
    resampled = df.resample(resample_unit)
    nans = resampled.Price.ohlc().isna().open.values
    ohlc = resampled['Price'].ohlc()[~nans].values[-count:]
    if len(ohlc) < count:
        return []

    ohlc -= price_offset
    vol = np.expand_dims(resampled['Volume'].sum()[~nans].values[-count:], axis=1)
    max_vol = np.expand_dims(resampled['Volume'].max()[~nans].values[-count:], axis=1)
    vwap = np.expand_dims(resampled['Market VWAP'].mean()[~nans][-count:], axis=1)
    vwap -= vwap[-1]

    if feature.sample is None:
        feature.sample = np.hstack([ohlc, vol, max_vol, vwap])
    else:
        feature.sample[:] = np.hstack([ohlc, vol, max_vol, vwap])

    return feature.sample[:]
feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/test.csv" },
        "features": [ { "count": 60, "size": 1, "unit": "sec" } ]
    }
    adapter = loader.load_adapter(json=rds)
    data = feature(adapter, 5000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()