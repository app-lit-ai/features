#TODO quadruple check for lookahead bias

def feature(adapter, index, vars=None, other_features=None):
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    data = adapter.get_bars(index, count, unit, size)
    if len(data) != count:
        return []

    price_offset = data[-1,3]
    data -= price_offset

    if feature.sample is None:
        feature.sample = data
    else:
        feature.sample[:] = data

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader

    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_ALL.csv", "resolution": 1 },
        "features": [ { "count": 50, "size": 1, "unit": "day" } ]
    }
    adapter = loader.load_adapter(json=rds)

    index = 446443900
    data = len(feature(adapter, index, adapter.rds['features'][0]))

if __name__ == '__main__':
    main()