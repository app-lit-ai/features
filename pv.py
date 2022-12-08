"""
Parameters
----------
count : number
    The number of ticks.
"""
import numpy as np

def feature(adapter, index, vars=None, other_features=None):
    count = vars['count'] or 64
    df = adapter.get_dataframe(index, count)
    if len(df) < count:
        return []

    if feature.sample is None:
        feature.sample = df[['mdEntryPx', 'mdEntrySize']].astype(np.float32).values
    else:
        feature.sample[:] = df[['mdEntryPx', 'mdEntrySize']].astype(np.float32).values

    #price_offset = feature.sample[-1][0]
#    feature.sample[:,0] = feature.sample[:,0]# - price_offset
    return feature.sample[:,0]
    
feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/test.csv" },
        "features": [ { "count": 512 } ]
    }
    adapter = loader.load_adapter(json=rds)
    data = feature(adapter, 5000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()