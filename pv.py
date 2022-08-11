import numpy as np

def feature(adapter, index, vars=None, other_features=None):
    window = 10
    lookback_index = index - (window - 1)
    if lookback_index < 0:
        return []

    df = adapter.get_dataframe(lookback_index, index + 1)

    feature.sample = df[['Price', 'Volume']].astype(np.float32).values

    price_offset = feature.sample[-1][0]
    feature.sample[:,0] = feature.sample[:,0] - price_offset
    return feature.sample[:]
    
feature.sample = np.array((10, 2))

def main():
    from lit.data import loader
    rds_path = "/opt/lit/refined_data/TSLA.O_2010.json"
    adapter = loader.load_adapter(rds_path, limit=20000)
    data = feature(adapter, 5000)
    print(data)

if __name__ == '__main__':
    main()