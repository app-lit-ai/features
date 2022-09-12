import argparse
import time
import numpy as np

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

    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, type=str)
    args = parser.parse_args()

    rds = {
        "adapter": { "name": "reuters", "path": args.path },
        "features": [ { "count": 10, "size": 1, "unit": "day" } ]
    }
    adapter = loader.load_adapter(json=rds)

    index = 800000
    start = time.time()
    data = len(feature(adapter, index, adapter.rds['features'][0])) # first get
    print(f"{data} in {time.time() - start} seconds")
    start = time.time()
    r = range(index, index + 10000, 1000)
    data = [len(feature(adapter, index, adapter.rds['features'][0])) for index in r] # walk the data
    print(f"{data} in {time.time() - start} seconds")

    start = time.time()
    data = len(feature(adapter, index, adapter.rds['features'][0])) # get it again
    print(f"{data} in {time.time() - start} seconds")


if __name__ == '__main__':
    main()