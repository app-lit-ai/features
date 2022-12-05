import logging
import numpy as np
from scipy.signal import savgol_filter
from sklearn.linear_model import LinearRegression
from math import sqrt

def pythag(pt1, pt2):
    a_sq = (pt2[0] - pt1[0]) ** 2
    b_sq = (pt2[1] - pt1[1]) ** 2
    return sqrt(a_sq + b_sq)

def local_min_max(pts):
    local_min = []
    local_max = []
    prev_pts = [(0, pts[0]), (1, pts[1])]
    for i in range(1, len(pts) - 1):
        append_to = ''
        if pts[i-1] > pts[i] < pts[i+1]:
            append_to = 'min'
        elif pts[i-1] < pts[i] > pts[i+1]:
            append_to = 'max'
        if append_to:
            if local_min or local_max:
                prev_distance = pythag(prev_pts[0], prev_pts[1]) * 0.5
                curr_distance = pythag(prev_pts[1], (i, pts[i]))
                if curr_distance >= prev_distance:
                    prev_pts[0] = prev_pts[1]
                    prev_pts[1] = (i, pts[i])
                    if append_to == 'min':
                        local_min.append((i, pts[i]))
                    else:
                        local_max.append((i, pts[i]))
            else:
                prev_pts[0] = prev_pts[1]
                prev_pts[1] = (i, pts[i])
                if append_to == 'min':
                    local_min.append((i, pts[i]))
                else:
                    local_max.append((i, pts[i]))
    return local_min, local_max

def regression_ceof(pts):
    X = np.array([pt[0] for pt in pts]).reshape(-1, 1)
    y = np.array([pt[1] for pt in pts])
    model = LinearRegression()
    model.fit(X, y)
    return model.coef_[0], model.intercept_

def get_support_resistance(data):
    month_diff = data.shape[0] // len(data) # Integer divide the number of prices we have by 30
    if month_diff == 0: # We want a value greater than 0
        month_diff = 1
    smooth = int(2 * month_diff + 3) # Simple algo to determine smoothness
    pts = savgol_filter(data, smooth, 3) # Get the smoothened price data
    local_min, local_max = local_min_max(pts)

    local_min_slope, local_min_int = regression_ceof(local_min)
    local_max_slope, local_max_int = regression_ceof(local_max)

    support = (local_min_slope * np.arange(len(data))) + local_min_int
    resistance = (local_max_slope * np.arange(len(data))) + local_max_int

    return support[-1], resistance[-1]

LAST_DATE, LAST_SAMPLE = None, None
def feature(adapter, index, vars=None, other_features=None):
    global LAST_DATE, LAST_SAMPLE
    dt = adapter.get_timestamp(index)
    date = f"{dt.year}-{dt.month}-{dt.day}"
    if date == LAST_DATE:
        return LAST_SAMPLE
    
    # price_offset = adapter.get_price(index)

    count, size, unit = 100, 1, "day"
    data_day = adapter.get_bars(index, count, unit, size)
    if len(data_day) == 0 or len(data_day) < count:
        LAST_DATE, LAST_SAMPLE = date, []
        return []
    prices = data_day[:, 3]

    try:
        feature.sample = np.asarray([ 
            get_support_resistance(prices), 
            get_support_resistance(prices[-50:]),
            get_support_resistance(prices[-20:])
        ]).flatten()# - price_offset
    except ValueError:
        # either support or resistance is empty
        LAST_DATE, LAST_SAMPLE = date, []
        return []

    LAST_DATE, LAST_SAMPLE = date, feature.sample

    return feature.sample[:]

feature.sample = None

def main():
    from lit.data import loader
    rds = {
        "adapter": { "name": "reuters", "path": "/data/raw/TSLA.O_ALL.csv", "resolution": 1 },
        "features": [ { } ]
    }
    adapter = loader.load_adapter(json=rds)
    index = 15054622
    data = feature(adapter, index, adapter.rds['features'][0])
    print(data)

if __name__ == '__main__':
    main()