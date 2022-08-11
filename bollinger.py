import numpy as np

def get_sma(prices, rate):
    return prices.rolling(rate).mean()

def get_bollinger_bands(prices, rate):
    sma = get_sma(prices, rate)
    std = prices.rolling(rate).std()
    bollinger_up = sma + std * 2 # top band
    bollinger_down = sma - std * 2 # bottom band
    return bollinger_up, bollinger_down

def feature(adapter, index, vars=None, other_features=None):
    window = vars['window'] or 100
    lookback_index = index - (window - 1)
    if lookback_index < 0:
        return []

    df = adapter.get_dataframe(lookback_index, index + 1)

    rate = vars['rate'] or 20
    up, down = get_bollinger_bands(df.Price, rate)
    feature.sample = np.swapaxes(np.asarray([up[rate:], down[rate:]]) - df.Price.iloc[-1], 0, 1)

    price_offset = df.Price.iloc[-1]
    feature.sample = feature.sample - price_offset
    return feature.sample[:]