from typing import List
from fixedpoint import FixedPoint
import numpy as np
from perf_model.config import *

class Perceptron:
    def __init__(self, perc_params: List[FixedPoint], nweights):
        self._pp = []
        for pp in perc_params:
            bias = FixedPoint(hex(pp.bits[0 : NUM_WIDTH-1]), True, m=NUM_INT_BITS, n=NUM_FRAC_BITS, overflow=OVERFLOW)
            weights = []
            for i in range(nweights):
                lo = (i+1)*NUM_WIDTH
                hi = (i+2)*NUM_WIDTH-1
                weights.append(FixedPoint(hex(pp.bits[lo:hi]), True, m=NUM_INT_BITS, n=NUM_FRAC_BITS, overflow=OVERFLOW))
            self._pp.append((bias, np.array(weights)))

    def calculate(self, input:np.ndarray, pidx):
        bias, weights = self._pp[pidx]
        dotprod: FixedPoint = (input @ weights) + bias.resize(NUM_INT_BITS, NUM_FRAC_BITS)
        dotprod.resize(NUM_INT_BITS, NUM_FRAC_BITS, alert="ignore", overflow=OVERFLOW)
        return dotprod
