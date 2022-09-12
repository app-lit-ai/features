   
def feature(adapter, index, vars=None, other_features=None):
    
    risk = vars['risk']
    reward = vars['reward']
    type = vars['type']

    count = vars['count'] or 60
    size = vars['size'] or 1
    unit = vars['unit'] or 'sec'

    data = adapter.get_bars(index, count, unit, size, future=True)
    if len(data) != count:
        return []    

    start_price = data[0, 0]
    if type == "long":
        loss_price = start_price - risk
        win_price = start_price + reward
        loss_comparator = lambda low, high: low <= loss_price
        win_comparator = lambda low, high: high >= win_price
    elif type == "short":
        loss_price = start_price + risk
        win_price = start_price - reward
        loss_comparator = lambda low, high: high >= loss_price
        win_comparator = lambda low, high: low <= win_price
    else:
        raise Exception("Invalid type input; must be either 'long' or 'short'")

    for index in range(len(data)):
        low, high = data[index,2], data[index,1]
        if loss_comparator(low, high):
            return [0.0]
        if win_comparator(low, high):
            return [1.0]

    return [0.0] # no partial wins

def interrogate():
    return [
        { 
            "name": "risk", "type": "number",
            "description": "How much can the price go down before a sale is forced."
        },
        {
            "name": "reward", "type": "number",
            "description": "At what price is a sale forced to take profit."
        },
        {
            "name": "type", "type": "string",
            "description": "One of two valid values: 'long' or 'short'"
        },
        {
            "name": "count", "type": "number",
            "description": "The number of bars to examine in the future for risk and reward thresholds."
        },
        {
            "name": "size", "type": "number",
            "description": "The size of each bar"
        },
        {
            "name": "unit", "type": "string", 
            "description": "The unit for each bar. Valid values are 'day', 'hour', 'minute', 'second'"
        }
    ]

def main():
    from lit.data import loader
    import h5py
    from random import randint

    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_ALL.csv" },
        "features": [ { "risk": 1, "reward": 1, "type": "long", "count": 10, "size": 1, "unit": "day" } ]
    }
    adapter = loader.load_adapter(json=rds)

    with h5py.File("/data/raw/TSLA.O_ALL.h5", "r") as f:
        sample_count = f['timestamp'].shape[0]

    indexes = [randint(1, sample_count) for i in range(10)]
    for index in indexes:
        data = len(feature(adapter, index, adapter.rds['features'][0]))


if __name__ == '__main__':
    main()