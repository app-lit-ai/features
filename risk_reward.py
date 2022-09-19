import numpy as np

SHAKE_TO_SECONDS = 10e8

def feature(adapter, index, vars=None, other_features=None):
    type = vars.get('type') # long or short
    risk, reward = vars.get('risk'), vars.get('reward')
    horizon = vars.get('horizon')
    return is_win(type[0], adapter.handle, index, risk, reward, horizon, slippage=0)

def is_win(label_type, tick_file, sample_index, risk, reward, horizon=None, slippage=0):
    label_dict = {
        "s": is_short_rr_v8,
        "l": is_long_rr_v8,
        "t": tick_rr_v8
    }
    get_label = label_dict[label_type.lower()]
    if label_type.lower() == "t":
        return get_label(tick_file, sample_index, risk, reward)
    else:
        return get_label(tick_file, sample_index, risk, reward, horizon, slippage)


def find_tick_stop(starting_pos, next_price, eof, target, stop_out):
    current_position = starting_pos
    while not eof(current_position):
        if next_price(current_position) >= target:
            return [1.0]
        if next_price (current_position) <= stop_out:
            return [0.0]
        current_position += 1
    return [0.0]

def tick_rr_v8(tick_file, sample_index_in, risk, reward):
    accelerator = tick_file['accelerators']
    sample_index = sample_index_in
    start_price  = tick_file['Price'][sample_index]
    stop_out     = start_price - risk
    target       = start_price + reward
    eof          = lambda x: x + 1 >= len(tick_file['Price'])
    next_price   = lambda x: tick_file['Price'][x+1]
    p_100  = accelerator['p100']
    p_10   = accelerator['p10']

    current_position = sample_index
    end_of_this_block = current_position + (10 - (current_position % 10))

    block_max, block_min = p_10[current_position//10]
    if block_max >= target or block_min <= stop_out:
        if current_position + 1 < end_of_this_block:
            if max(tick_file['Price'][current_position+1:end_of_this_block]) >= target or min(tick_file['Volume'][current_position+1:end_of_this_block]) <= stop_out:
                return find_tick_stop(current_position, next_price, eof, target, stop_out)
    if end_of_this_block >= len(tick_file['Price']):
        return find_tick_stop(current_position, next_price, eof, target, stop_out)
    current_position = end_of_this_block
    
    end_of_this_block = current_position + (100 - (current_position % 100))
    if end_of_this_block >= len(tick_file['Price']):
        return find_tick_stop(current_position, next_price, eof, target, stop_out)
    
    block_max, block_min = p_100[current_position//100]
    if block_max >= target or block_min <= stop_out:
        found = True
        while p_10[current_position//10, 0] < target and p_10[current_position//10, 1] > stop_out:
            current_position += 10
            if current_position >= end_of_this_block:
                if current_position > end_of_this_block:
                    print("!!!WARNING: current_position > end_of_this_block during p_100 inital check!!!")
                    print("current_position: " + str(current_position) + " , end_of_this_block: " + str(end_of_this_block))
                found = False
                break
        if found:
            return find_tick_stop(current_position, next_price, eof, target, stop_out)
        if current_position != end_of_this_block:
            print("!!!WARNING: current_position != end_of_this_block during p_100 inital check on exit!!!")
            print("current_position: " + str(current_position) + " , end_of_this_block: " + str(end_of_this_block))
    current_position = end_of_this_block

    while p_100[current_position//100,0] < target and p_100[current_position//100,1] > stop_out:
        if (current_position + 100)//100 >= len(p_100):
            break
        current_position += 100
    while p_10[current_position//10,0] < target and p_10[current_position//10,1] > stop_out:
        if (current_position + 10)//10 >= len(p_10):
            break
        current_position += 10
    return find_tick_stop(current_position, next_price, eof, target, stop_out)


def find_long_stop(tick_file, target, stop, current_position, end_of_horizon):
    next_price = lambda x: tick_file['Price'][x]
    eof = lambda x: x + 1 >= len(tick_file['Price'])
    get_time = lambda x: tick_file['timestamp'][x]

    while not eof(current_position):
        if get_time(current_position) >= end_of_horizon:
            return [0.0]

        if next_price(current_position) >= target:
            return [1.0]

        if next_price(current_position) <= stop:
            return [0.0]

        current_position += 1
    
    return [0.0]

def find_short_stop(tick_file, target, stop, current_position, end_of_horizon):
    next_price = lambda x: tick_file['Price'][x]
    eof = lambda x: x + 1 >= len(tick_file['Price'])
    get_time = lambda x: tick_file['timestamp'][x]

    while not eof(current_position):
        if get_time(current_position) >= end_of_horizon:
            return [0.0]

        if next_price(current_position) <= target:
            return [1.0]

        if next_price(current_position) >= stop:
            return [0.0]

        current_position += 1
    
    return [0.0]

def is_long_rr_v8(tick_file, sample_index, risk, reward, horizon, slippage=0):
    accelerator = tick_file['accelerators']
    start_time = tick_file['timestamp'][sample_index] # timestamp of most recent tick
    time_horizon = horizon * SHAKE_TO_SECONDS
    stop_time = start_time + time_horizon
    start_price = tick_file['Price'][sample_index] + slippage
    stop_out = start_price - risk + slippage
    target = start_price + reward + slippage
    accelerator_index = sample_index
    p_1000 = accelerator['p1000']
    p_100  = accelerator['p100' ]
    p_10   = accelerator['p10'  ]
    
    def get_prices(start, end):
        return tick_file['Price'][start:end]

    #check if anything in current batch could be the stop:
    end_of_this_block = accelerator_index + (10 - (accelerator_index % 10)) # where within the set the end of this block of 10 is
    if p_10[accelerator_index//10,0] >= target or p_10[accelerator_index//10,1] <= stop_out:
        # if accelerator_index = 105, make sure the target or stop_out wasn't hit in 100-105, but instead from 106-110
        if accelerator_index+ 1 < end_of_this_block:
            if max(get_prices(accelerator_index+1,end_of_this_block)) >= target or min(get_prices(accelerator_index+1,end_of_this_block)) <= stop_out:
                return find_long_stop(tick_file, target, stop_out, accelerator_index, stop_time)
    if end_of_this_block >= len(tick_file['Price']):
        return find_long_stop(tick_file, target, stop_out, accelerator_index, stop_time)
    accelerator_index = end_of_this_block

    end_of_this_block = accelerator_index + (100 - (accelerator_index % 100))
    if end_of_this_block >= len(tick_file['Price']):
        return find_long_stop(tick_file, target, stop_out, accelerator_index, stop_time)
    if p_100[accelerator_index//100,0] >= target or p_100[accelerator_index//100,1] <= stop_out:
        found = True
        while p_10[accelerator_index//10, 0] < target and p_10[accelerator_index//10, 1] > stop_out:
            accelerator_index += 10
            if accelerator_index >= end_of_this_block:
                if accelerator_index > end_of_this_block:
                    print("!!!WARNING: accelerator_index > end_of_this_block during p_100 inital check!!!")
                    print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
                found = False
                break
        if found:    
            return find_long_stop(tick_file, target, stop_out, accelerator_index, stop_time)
        if accelerator_index != end_of_this_block:
            print("!!!WARNING: accelerator_index != end_of_this_block during p_100 inital check on exit!!!")
            print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
    accelerator_index = end_of_this_block

    end_of_this_block = accelerator_index + (1000 - (accelerator_index % 1000))
    if end_of_this_block >= len(tick_file['Price']):
        return find_long_stop(tick_file, target, stop_out, accelerator_index, stop_time)
    if p_1000[accelerator_index//1000,0] >= target or p_1000[accelerator_index//1000,1] <= stop_out:
        found = True
        while p_100[accelerator_index//100, 0] < target and p_100[accelerator_index//100, 1] > stop_out:
            accelerator_index += 100
            if accelerator_index >= end_of_this_block:
                if accelerator_index > end_of_this_block:
                    print("!!!WARNING: accelerator_index > end_of_this_block during p_1000 inital check (Sub p_100)!!!")
                    print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
                found = False
                break
        if found:
            while p_10[accelerator_index//10, 0] < target and p_10[accelerator_index//10, 1] > stop_out:
                accelerator_index += 10
                if accelerator_index >= end_of_this_block:
                    if accelerator_index > end_of_this_block:
                        print("!!!WARNING: accelerator_index > end_of_this_block during p_1000 inital check (Sub p_10)!!!")
                        print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
                    found = False
                    break
            if found:
                return find_long_stop(tick_file, target, stop_out, accelerator_index, stop_time)
        if accelerator_index != end_of_this_block:
            print("!!!WARNING: accelerator_index != end_of_this_block during p_1000 inital check on exit!!!")
            print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
    accelerator_index = end_of_this_block
    
    while p_1000[accelerator_index//1000, 0] < target and p_1000[accelerator_index//1000, 1] > stop_out:
        if (accelerator_index + 1000)//1000 >= len(p_1000):
            break
        accelerator_index += 1000
    while p_100[accelerator_index//100, 0] < target and p_100[accelerator_index//100, 1] > stop_out:
        if (accelerator_index + 100)//100 >= len(p_100):
            break
        accelerator_index += 100
    while p_10[accelerator_index//10, 0] < target and p_10[accelerator_index//10, 1] > stop_out:
        if (accelerator_index + 10)//10 >= len(p_10):
            break
        accelerator_index += 10
    return find_long_stop(tick_file, target, stop_out, accelerator_index, stop_time)

def is_short_rr_v8(tick_file, sample_index, risk, reward, horizon, slippage=0):

    accelerator = tick_file['accelerators']
    start_time = tick_file['timestamp'][sample_index] #timestamp of most recent tick
    time_horizon = horizon * SHAKE_TO_SECONDS
    stop_time = start_time + time_horizon
    start_price = tick_file['Price'][sample_index] - slippage
    stop_out = start_price + risk - slippage
    target = start_price - reward - slippage
    accelerator_index = sample_index
    p_1000 = accelerator['p1000']
    p_100  = accelerator['p100' ]
    p_10   = accelerator['p10'  ]
    
    def get_prices(start, end):
        return tick_file['Price'][start:end]

    #check if anything in current batch could be the stop:
    end_of_this_block = accelerator_index + (10 - (accelerator_index % 10)) # where within the set the end of this block of 10 is
    if p_10[accelerator_index//10,1] <= target or p_10[accelerator_index//10,0] >= stop_out:
        # if accelerator_index = 105, make sure the target or stop_out wasn't hit in 100-105, but instead from 106-110
        if accelerator_index+ 1 < end_of_this_block:
            if min(get_prices(accelerator_index+1,end_of_this_block)) <= target or max(get_prices(accelerator_index+1,end_of_this_block)) >= stop_out:
                return find_short_stop(tick_file, target, stop_out, accelerator_index, stop_time)
    if end_of_this_block >= len(tick_file['Price']):
        return find_short_stop(tick_file, target, stop_out, accelerator_index, stop_time)
    accelerator_index = end_of_this_block

    end_of_this_block = accelerator_index + (100 - (accelerator_index % 100))
    if end_of_this_block >= len(tick_file['Price']):
        return find_short_stop(tick_file, target, stop_out, accelerator_index, stop_time)
    if p_100[accelerator_index//100,1] <= target or p_100[accelerator_index//100,0] >= stop_out:
        found = True
        while p_10[accelerator_index//10, 1] > target and p_10[accelerator_index//10, 0] < stop_out:
            accelerator_index += 10
            if accelerator_index >= end_of_this_block:
                if accelerator_index > end_of_this_block:
                    print("!!!WARNING: accelerator_index > end_of_this_block during p_100 inital check!!!")
                    print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
                found = False
                break
        if found:    
            return find_short_stop(tick_file, target, stop_out, accelerator_index, stop_time)
        if accelerator_index != end_of_this_block:
            print("!!!WARNING: accelerator_index != end_of_this_block during p_100 inital check on exit!!!")
            print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
    accelerator_index = end_of_this_block

    end_of_this_block = accelerator_index + (1000 - (accelerator_index % 1000))
    if end_of_this_block > len(tick_file['Price']):
        return find_short_stop(tick_file, target, stop_out, accelerator_index, stop_time)
    if p_1000[accelerator_index//1000,1] <= target or p_1000[accelerator_index//1000,0] >= stop_out:
        found = True
        while p_100[accelerator_index//100, 1] > target and p_100[accelerator_index//100, 0] < stop_out:
            accelerator_index += 100
            if accelerator_index >= end_of_this_block:
                if accelerator_index > end_of_this_block:
                    print("!!!WARNING: accelerator_index > end_of_this_block during p_1000 inital check (Sub p_100)!!!")
                    print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
                found = False
                break
        if found:
            while p_10[accelerator_index//10, 1] > target and p_10[accelerator_index//10, 0] < stop_out:
                accelerator_index += 10
                if accelerator_index >= end_of_this_block:
                    if accelerator_index > end_of_this_block:
                        print("!!!WARNING: accelerator_index > end_of_this_block during p_1000 inital check (Sub p_10)!!!")
                        print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
                    found = False
                    break
            if found:
                return find_short_stop(tick_file, target, stop_out, accelerator_index, stop_time)
        if accelerator_index != end_of_this_block:
            print("!!!WARNING: accelerator_index != end_of_this_block during p_1000 inital check on exit!!!")
            print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
    accelerator_index = end_of_this_block
    
    while p_1000[accelerator_index//1000, 1] > target and p_1000[accelerator_index//1000, 0] < stop_out:
        if (accelerator_index + 1000)//1000 >= len(p_1000):
            break
        accelerator_index += 1000
    while p_100[accelerator_index//100, 1] > target and p_100[accelerator_index//100, 0] < stop_out:
        if (accelerator_index + 100)//100 >= len(p_100):
            break
        accelerator_index += 100
    while p_10[accelerator_index//10, 1] > target and p_10[accelerator_index//10, 0] < stop_out:
        if (accelerator_index + 10)//10 >= len(p_10):
            break
        accelerator_index += 10
    return find_short_stop(tick_file, target, stop_out, accelerator_index, stop_time)


def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_2010.csv" },
        "features": [ { "type": "long", "risk": 2, "make": 3, "horizon": 1 } ]
    }
    adapter = loader.load_adapter(json=rds)
    data = feature(adapter, 50000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()