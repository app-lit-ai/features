import numpy as np

def feature(adapter, index, vars=None, other_features=None):
    count = vars['count'] or 64
    df = adapter.get_dataframe(index, "tick", count + 1)
    if len(df) < count:
        return []

    feature.sample = df[['Price', 'Volume']].astype(np.float32).values

    price_offset = feature.sample[-1][0]
    feature.sample[:,0] = feature.sample[:,0] - price_offset
    return feature.sample[:]
    
feature.sample = np.array((10, 2))

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters_csv", "path": "/data/raw/test.csv" },
        "features": [ { "count": 512 } ]
    }
    adapter = loader.load_adapter(json=rds, limit=20000)
    data = feature(adapter, 5000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()