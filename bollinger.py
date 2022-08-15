import numpy as np

#TODO quadruple check for lookahead bias

def feature(adapter, index, vars=None, other_features=None):
    rate = vars['rate'] or 20
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    df = adapter.get_dataframe(index, unit, (count * size) + 1)
    if len(df[rate:]) < count:
        return []

    window = df.Price.rolling(rate)
    sma, std = window.mean(), window.std()
    up, down = sma + std * 2, sma - std * 2

    feature.sample = np.swapaxes(np.asarray([up[rate:], down[rate:]]), 0, 1)

    price_offset = df.Price.iloc[-1]
    feature.sample = feature.sample - price_offset

    return feature.sample[:]

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters_csv", "path": "/data/raw/test.csv" },
        "features": [ { "rate": 20, "count": 60, "size": 1, "unit": "sec" } ]
    }
    adapter = loader.load_adapter(json=rds, limit=20000)
    data = feature(adapter, 5000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()