#TODO quadruple check for lookahead bias

LAST_DATETIME, LAST_SAMPLE = {}, {}
def feature(adapter, index, vars=None, other_features=None):
    global LAST_DATETIME, LAST_SAMPLE
    unit = vars['unit'] or 'sec'
    dt = adapter.get_timestamp(index)
    datetime = adapter.format_datetime(dt, unit)
    if unit in LAST_DATETIME and datetime == LAST_DATETIME[unit]:
        return LAST_SAMPLE[unit]

    count = vars['count'] or 60
    size = vars['size'] or 1

    data = adapter.get_bars(index, count, unit, size).copy()
    data = data[:,:-1] # drop the reuters vwap to avoid accidentally using it later
    if len(data) != count:
        return []

    # price_offset = data[-1,3]
    # data[:, :4] -= price_offset # price_open, price_high, price_low, price_close

    if feature.sample is None:
        feature.sample = data
    else:
        feature.sample[:] = data

    LAST_DATETIME[unit], LAST_SAMPLE[unit] = datetime, feature.sample

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