import numpy as np

def feature(adapter, index, vars=None, other_features=None):
    field = vars['field']
    nonzeros = np.count_nonzero(other_features[field])
    if nonzeros == 0:
        err = f"0 values for field {field} at index {index}"
        print(err)
        raise Exception(err)
    return np.asarray([nonzeros])
