import numpy as np

#TODO quadruple check for lookahead bias

def feature(adapter, index, vars=None, other_features=None):
    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    df = adapter.get_dataframe(index, unit, (count * size) + 1)
    offset = df.Price.iloc[-1]
    df = df.set_index('Date-Time')
    resample_unit = adapter.translate_resample_unit(unit)
    df = df.resample(f"{size}{resample_unit}")['Price'].ohlc()
    if len(df) < count:
        return []

    if not feature.sample:
        feature.sample = df.values[-count:]
    else:
        feature.sample[:] = df.values[-count:]
    feature.sample -= offset

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds_path = "/opt/lit/refined_data/TSLA.O_2010.json"
    adapter = loader.load_adapter(rds_path, limit=20000)
    data = feature(adapter, 5000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()