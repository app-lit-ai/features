import numpy as np

def feature(adapter, index, vars=None, other_features=None):
    window = 10
    lookback_index = index - (window - 1)
    if lookback_index < 0:
        return []

    df = adapter.get_dataframe(lookback_index, index + 1)

    feature.sample = df[['mdEntryPx', 'mdEntrySize']].astype(np.float32).values

    price_offset = feature.sample[-1][0]
    feature.sample[:,0] = feature.sample[:,0] - price_offset
    return feature.sample[:]
    
feature.sample = np.array((10, 2))