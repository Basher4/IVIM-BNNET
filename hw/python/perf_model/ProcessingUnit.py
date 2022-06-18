import numpy as np

from Perceptron import Perceptron
from BernoulliSampler import BernoulliSampler
from perf_model.config import *

class ProcessingUnit:
    def __init__(self, perc_params, samples, nweights):
        self.perceptrons = [Perceptron(pp, nweights) for pp in perc_params]
        self.bs = BernoulliSampler(len(perc_params))
        self.samples = samples
        self.progress = 0

    def _apply_dropout(self, input):
        mask = self.bs.get_mask()
        return np.array([(m if mask.bits[i] == 1 else CONST_FP_ZERO) for i,m in enumerate(input)])

    def _calc_param(self, input: np.ndarray, idx):
        # print("Param", end='')
        # Layer 1
        l1out = [p.calculate(input, idx) for p in self.perceptrons]
        l1out = np.array([(r if r > 0 else CONST_FP_ZERO) for r in l1out])

        # Start sampling
        samples_l2 = []
        for _ in range(self.samples):
            # print(".", end="")
            # Layer 2
            res = self._apply_dropout(l1out)
            samples_l2.append([p.calculate(res, idx+1) for p in self.perceptrons])

        samples_l3 = []
        for smpl in samples_l2:
            # print("+", end="")
            # Encoder
            res = self._apply_dropout(smpl)
            samples_l3.append(self.perceptrons[0].calculate(res, idx+2))
        # print()
        return samples_l3

    def calculate(self, input: np.ndarray):
        # print("Voxel start", self.progress + 1, "/100'000")
        return [self._calc_param(input, idx) for idx in [0, 3, 6, 9]]
