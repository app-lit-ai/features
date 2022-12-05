"""
Parameters
----------
type : string
    Long or short.
risk : number
    The amount of risk, as a percent, before a trade is stopped out.
reward : number
    The amount of reward, as a percent, before a trade is closed as a win.
horizon : number
    The amount of time, in seconds, until the trade times out and is forced close as a loss.
"""
import numpy as np

SHAKE_TO_SECONDS = 10e8

def feature(adapter, index, vars=None, other_features=None):
    type = vars.get('type')
    risk, reward = vars.get('risk'), vars.get('reward')
    horizon = vars.get('horizon')

    price = adapter.get_price(index)
    risk *= price
    reward *= price

    return is_win(type[0], adapter, index, risk, reward, horizon, slippage=0)

def is_win(label_type, adapter, sample_index, risk, reward, horizon=None, slippage=0):
    label_dict = {
        "s": is_short_rr_v8,
        "l": is_long_rr_v8
    }
    get_label = label_dict[label_type.lower()]
    if label_type.lower() == "t":
        return get_label(adapter, sample_index, risk, reward)
    else:
        return get_label(adapter, sample_index, risk, reward, horizon, slippage)


def find_tick_stop(starting_pos, next_price, eof, target, stop_out):
    current_position = starting_pos
    while not eof(current_position):
        if next_price(current_position) >= target:
            return [1.0]
        if next_price (current_position) <= stop_out:
            return [0.0]
        current_position += 1
    return [0.0]

def find_long_stop(adapter, target, stop, current_position, end_of_horizon):
    next_price = lambda x: adapter.get_price(x)
    eof = lambda x: x + 1 >= len(adapter)
    get_time = lambda x: adapter.get_timestamp(x).value

    while not eof(current_position):
        if get_time(current_position) >= end_of_horizon:
            return [0.0]

        if next_price(current_position) >= target:
            return [1.0]

        if next_price(current_position) <= stop:
            return [0.0]

        current_position += 1
    
    return [0.0]

def find_short_stop(adapter, target, stop, current_position, end_of_horizon):
    next_price = lambda x: adapter.get_price(x)
    eof = lambda x: x + 1 >= len(adapter)
    get_time = lambda x: adapter.get_timestamp(x).value

    while not eof(current_position):
        if get_time(current_position) >= end_of_horizon:
            return [0.0]

        if next_price(current_position) <= target:
            return [1.0]

        if next_price(current_position) >= stop:
            return [0.0]

        current_position += 1
    
    return [0.0]

def is_long_rr_v8(adapter, sample_index, risk, reward, horizon, slippage=0):
    start_time = adapter.get_timestamp(sample_index).value # timestamp of most recent tick
    time_horizon = horizon * SHAKE_TO_SECONDS
    stop_time = start_time + time_horizon
    start_price = adapter.get_price(sample_index) + slippage
    stop_out = start_price - risk + slippage
    target = start_price + reward + slippage
    accelerator_index = sample_index
    p_1000 = adapter.get_accelerators('p1000')
    p_100  = adapter.get_accelerators('p100')
    p_10   = adapter.get_accelerators('p10')
    
    def get_prices(start, end):
        return adapter.get_dataframe(start, end - start).Price

    #check if anything in current batch could be the stop:
    end_of_this_block = accelerator_index + (10 - (accelerator_index % 10)) # where within the set the end of this block of 10 is
    if p_10[accelerator_index//10,0] >= target or p_10[accelerator_index//10,1] <= stop_out:
        # if accelerator_index = 105, make sure the target or stop_out wasn't hit in 100-105, but instead from 106-110
        if accelerator_index+ 1 < end_of_this_block:
            if max(get_prices(accelerator_index+1,end_of_this_block)) >= target or min(get_prices(accelerator_index+1,end_of_this_block)) <= stop_out:
                return find_long_stop(adapter, target, stop_out, accelerator_index, stop_time)
    if end_of_this_block >= len(adapter):
        return find_long_stop(adapter, target, stop_out, accelerator_index, stop_time)
    accelerator_index = end_of_this_block

    end_of_this_block = accelerator_index + (100 - (accelerator_index % 100))
    if end_of_this_block >= len(adapter):
        return find_long_stop(adapter, target, stop_out, accelerator_index, stop_time)
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
            return find_long_stop(adapter, target, stop_out, accelerator_index, stop_time)
        if accelerator_index != end_of_this_block:
            print("!!!WARNING: accelerator_index != end_of_this_block during p_100 inital check on exit!!!")
            print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
    accelerator_index = end_of_this_block

    end_of_this_block = accelerator_index + (1000 - (accelerator_index % 1000))
    if end_of_this_block >= adapter:
        return find_long_stop(adapter, target, stop_out, accelerator_index, stop_time)
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
                return find_long_stop(adapter, target, stop_out, accelerator_index, stop_time)
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
    return find_long_stop(adapter, target, stop_out, accelerator_index, stop_time)

def is_short_rr_v8(adapter, sample_index, risk, reward, horizon, slippage=0):
    start_time = adapter.get_timestamp(sample_index).value # timestamp of most recent tick
    time_horizon = horizon * SHAKE_TO_SECONDS
    stop_time = start_time + time_horizon
    start_price = adapter.get_price(sample_index) - slippage
    stop_out = start_price + risk - slippage
    target = start_price - reward - slippage
    accelerator_index = sample_index
    p_1000 = adapter.get_accelerators('p1000')
    p_100  = adapter.get_accelerators('p100')
    p_10   = adapter.get_accelerators('p10')
    
    def get_prices(start, end):
        return adapter.get_dataframe(start, end - start).Price

    #check if anything in current batch could be the stop:
    end_of_this_block = accelerator_index + (10 - (accelerator_index % 10)) # where within the set the end of this block of 10 is
    if p_10[accelerator_index//10,1] <= target or p_10[accelerator_index//10,0] >= stop_out:
        # if accelerator_index = 105, make sure the target or stop_out wasn't hit in 100-105, but instead from 106-110
        if accelerator_index+ 1 < end_of_this_block:
            if min(get_prices(accelerator_index+1,end_of_this_block)) <= target or max(get_prices(accelerator_index+1,end_of_this_block)) >= stop_out:
                return find_short_stop(adapter, target, stop_out, accelerator_index, stop_time)
    if end_of_this_block >= len(adapter):
        return find_short_stop(adapter, target, stop_out, accelerator_index, stop_time)
    accelerator_index = end_of_this_block

    end_of_this_block = accelerator_index + (100 - (accelerator_index % 100))
    if end_of_this_block >= len(adapter):
        return find_short_stop(adapter, target, stop_out, accelerator_index, stop_time)
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
            return find_short_stop(adapter, target, stop_out, accelerator_index, stop_time)
        if accelerator_index != end_of_this_block:
            print("!!!WARNING: accelerator_index != end_of_this_block during p_100 inital check on exit!!!")
            print("accelerator_index: " + str(accelerator_index) + " , end_of_this_block: " + str(end_of_this_block))
    accelerator_index = end_of_this_block

    end_of_this_block = accelerator_index + (1000 - (accelerator_index % 1000))
    if end_of_this_block > len(adapter):
        return find_short_stop(adapter, target, stop_out, accelerator_index, stop_time)
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
                return find_short_stop(adapter, target, stop_out, accelerator_index, stop_time)
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
    return find_short_stop(adapter, target, stop_out, accelerator_index, stop_time)


def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_2010.csv" },
        "features": [ { "type": "long", "risk": 0.005, "reward": 0.005, "horizon": 900 } ]
    }
    adapter = loader.load_adapter(json=rds)
    data = feature(adapter, 50000, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()