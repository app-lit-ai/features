import time

def feature(adapter, index, vars=None, other_features=None):
    """
    Parameters
    ----------
    count : number
        The number of bars; e.g. [10] 1-second bars
    size : number
        The number of units in each bar; e.g. 10 [1]-second bars
    unit : string
        Either hour, minute, or second; e.g. 10 1-[second] bars
    """
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    data = adapter.get_bars(index, count, unit, size)
    if len(data) != count:
        return []

    data = data[:,:4]
    # price_offset = data[-1,3]
    # data -= price_offset

    if feature.sample is None:
        feature.sample = data
    else:
        feature.sample[:] = data

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_2010.csv" },
        "features": [ { "count": 10, "size": 1, "unit": "day" } ]
    }
    adapter = loader.load_adapter(json=rds)
    start = time.time()
    index = 500000
    data = feature(adapter, index, adapter.rds['features'][0])
    end = time.time()
    duration = end - start
    print(f"Built {len(data)} {rds['features'][0]['size']}-{rds['features'][0]['unit']} bars from index {index} in {duration} seconds")

if __name__ == '__main__':
    main()