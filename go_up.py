def feature(adapter, index, vars=None, other_features=None):
    lookahead = vars['lookahead'] or 1024
    df = adapter.get_dataframe(index, index + lookahead)
    price_now = df.loc[index, 'mdEntryPx']
    mean_future_price = df[['mdEntryPx']].mean()[0]
    if mean_future_price > price_now:
        return [1.0]
    else:
        return [0.0]