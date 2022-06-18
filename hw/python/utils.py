from fixedpoint import FixedPoint
import itertools
import numpy as np

from config import INT_BITS, FRAC_BITS

def write_romfile(data: np.array, path):
    DATA_WIDTH = (INT_BITS + FRAC_BITS + 3) // 4
    last_msb = 0
    with open(path, "w") as fd:
        for tpl in itertools.product(*map(range, data.shape)):
            c: FixedPoint = data[tpl]
            c.resize(INT_BITS, FRAC_BITS, overflow="clamp")
            if tpl[0] != last_msb:
                fd.write("\n")
                last_msb = tpl[0]
            fd.write(f"{c:0{DATA_WIDTH}x}")
        fd.write("\n")