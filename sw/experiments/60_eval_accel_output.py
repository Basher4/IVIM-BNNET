from dataclasses import dataclass
from fixedpoint import FixedPoint
import gzip
import itertools
import json
import numpy as np
import pickle
import sys
import torch

sys.path.append('./sw/')

NEURAL_NETWORK_PATH = "./sw/models/bnn_e01_SNR5_0.pt"
MEM_FILE_PATH = "./mem_files/for_testbench/fully_parallel"
INPUT_SIGNALS_PATH = "./sw/data/signals/infer_5SNR.pickle.gz"
ACCELERATOR_NUM_LANES = 11
accelerator_perceptrons = [[] for _ in range(ACCELERATOR_NUM_LANES)]
INT_BITS = 3
TOTAL_BITS = 16
MEMORY_WIDTH = 128 + 1
PAD_WITH_ZEROS = True
bvalues = torch.tensor([0, 5, 10, 20, 30, 40, 60, 150, 300, 500, 700])
net = torch.load(NEURAL_NETWORK_PATH, map_location="cpu")


@dataclass
class MinMax:
    min: float
    max: float

    def delta(self):
        return self.max - self.min


def sigm(param, bound: MinMax):
    return bound.min + torch.sigmoid(param) * bound.delta()

def compute_outputs(param1, param2, param3, param4):
    f = MinMax(0.0, 0.7)
    Dp = MinMax(0.005, 0.2)
    D = MinMax(0.0, 0.005)
    f0 = MinMax(0.0, 2.0)

    params = torch.stack([sigm(param1, f), sigm(param2, Dp), sigm(param3, D), sigm(param4, f0)], dim=0).unsqueeze(2)

    return params[0] * torch.exp(-bvalues * params[1]) + params[3] * torch.exp(-bvalues * params[2])


with gzip.open(INPUT_SIGNALS_PATH) as fd:
    input_data = pickle.load(fd)[0][:4]


def bit2tensor(*lst):
    return torch.tensor([float(FixedPoint(hex(x), True, INT_BITS, TOTAL_BITS - INT_BITS)) for x in lst])


fully_parallel_out = [
    [bit2tensor(0xfeab, 0xfeab, 0xfe8e, 0xfeab, 0xfeab, 0xfeab, 0xfea8, 0xfeab, 0xfeab, 0xfeab, 0xfeab, 0xfe5e, 0xfe75, 0xfeab, 0xfe70, 0xfe77, 0xfeab, 0xfeab, 0xfeab, 0xfe04, 0xfeab, 0xfe71, 0xfe71, 0xfea2, 0xfe87, 0xfe3f, 0xfe03, 0xfeab, 0xfe71, 0xfe70, 0xfeab, 0xfeab),
     bit2tensor(0xffff, 0xfffb, 0x0001, 0xffff, 0x0000, 0xffff, 0xffff, 0xfffe, 0xffff, 0xffff, 0x0001, 0xffff, 0x0000, 0xffff, 0x0000, 0xffff, 0xffff, 0xffff, 0xfffe, 0xffff, 0xffff, 0xffff, 0x0001, 0xffff, 0x0004, 0x0002, 0xffff, 0xffff, 0xffff, 0x0004, 0xfffe, 0x0006),
     bit2tensor(0x0079, 0x006a, 0x0078, 0x008e, 0x008a, 0x0078, 0x0080, 0x0078, 0x007e, 0x007a, 0x007b, 0x008b, 0x0078, 0x0078, 0x0079, 0x0078, 0x006a, 0x0078, 0x0078, 0x007a, 0x0078, 0x006a, 0x0078, 0x0076, 0x0078, 0x006f, 0x0078, 0x0079, 0x0078, 0x0078, 0x006b, 0x0078),
     bit2tensor(0xf527, 0xf527, 0xf527, 0xf4c8, 0xf4e5, 0xf503, 0xf528, 0xf596, 0xf523, 0xf527, 0xf5b6, 0xf5a1, 0xf527, 0xf54b, 0xf527, 0xf546, 0xf527, 0xf54b, 0xf4ff, 0xf527, 0xf527, 0xf4db, 0xf596, 0xf527, 0xf527, 0xf4e1, 0xf4f2, 0xf527, 0xf527, 0xf527, 0xf527, 0xf527),],
    [bit2tensor(0xfe75, 0xfeab, 0xfe8e, 0xfeab, 0xfe59, 0xfe91, 0xfeab, 0xfeab, 0xfeab, 0xfe75, 0xfe71, 0xfeab, 0xfe71, 0xfe75, 0xfeab, 0xfeab, 0xfeab, 0xfeab, 0xfe3f, 0xfeab, 0xfeab, 0xfe77, 0xfe77, 0xfeab, 0xfe87, 0xfeab, 0xfeab, 0xfe77, 0xfeab, 0xfe70, 0xfe59, 0xfeab),
     bit2tensor(0xffff, 0x0001, 0x0002, 0x0002, 0x0006, 0x0004, 0xffff, 0xffff, 0xffff, 0x0001, 0x0001, 0xffff, 0xfffe, 0xffff, 0xffff, 0xffff, 0xffff, 0x0003, 0xffff, 0xffff, 0x0001, 0xffff, 0x0000, 0x0004, 0xffff, 0xfffd, 0xfffe, 0x0000, 0xffff, 0xfffb, 0xffff, 0xffff),
     bit2tensor(0x008a, 0x0078, 0x0078, 0x0078, 0x007c, 0x0078, 0x0078, 0x006a, 0x007a, 0x0070, 0x007b, 0x0078, 0x0079, 0x007c, 0x0078, 0x0079, 0x0078, 0x0078, 0x0078, 0x007c, 0x006a, 0x0078, 0x008a, 0x0078, 0x0078, 0x006f, 0x0078, 0x006a, 0x0078, 0x0078, 0x007a, 0x007d),
     bit2tensor(0xf551, 0xf527, 0xf575, 0xf527, 0xf527, 0xf503, 0xf527, 0xf527, 0xf527, 0xf54e, 0xf527, 0xf4d5, 0xf527, 0xf4df, 0xf527, 0xf527, 0xf49a, 0xf4db, 0xf527, 0xf527, 0xf596, 0xf527, 0xf527, 0xf527, 0xf53a, 0xf527, 0xf5cb, 0xf546, 0xf546, 0xf527, 0xf4e5, 0xf527),],
    [bit2tensor(0xfeab, 0xfe12, 0xfe1b, 0xfdb6, 0xfe69, 0xfe91, 0xfeab, 0xfeab, 0xfebc, 0xfeab, 0xfeab, 0xfeab, 0xfe71, 0xfeab, 0xfeab, 0xfe77, 0xfeab, 0xfeab, 0xfe89, 0xfeab, 0xfeab, 0xfe71, 0xfe77, 0xfeab, 0xfeab, 0xfe6b, 0xfeab, 0xfe71, 0xfeab, 0xfeab, 0xfeab, 0xfeab),
     bit2tensor(0x0001, 0x0005, 0xffff, 0xffff, 0xffff, 0xffff, 0x0000, 0xffff, 0xffff, 0xffff, 0x0005, 0x0006, 0xffff, 0xffff, 0x0000, 0x0005, 0x0000, 0x0004, 0xffff, 0x000a, 0xffff, 0xffff, 0x0001, 0xfffe, 0xfffe, 0xfffd, 0x000b, 0x0005, 0xffff, 0xffff, 0xffff, 0xffff),
     bit2tensor(0x0078, 0x0078, 0x0078, 0x008b, 0x006b, 0x0071, 0x007a, 0x0078, 0x0078, 0x0078, 0x0078, 0x007a, 0x0078, 0x0078, 0x0078, 0x0078, 0x006d, 0x006d, 0x0078, 0x0078, 0x007b, 0x0078, 0x007c, 0x0078, 0x0078, 0x0078, 0x0078, 0x0079, 0x006a, 0x006d, 0x008a, 0x0069),
     bit2tensor(0xf527, 0xf4e1, 0xf4f8, 0xf47c, 0xf527, 0xf554, 0xf527, 0xf527, 0xf527, 0xf527, 0xf4fb, 0xf5a1, 0xf4db, 0xf527, 0xf527, 0xf546, 0xf527, 0xf527, 0xf527, 0xf527, 0xf4db, 0xf546, 0xf546, 0xf52d, 0xf527, 0xf527, 0xf527, 0xf527, 0xf546, 0xf4dc, 0xf527, 0xf4d5),],
    [bit2tensor(0xfeab, 0xfe75, 0xfeab, 0xfeab, 0xfeab, 0xfe91, 0xfe7d, 0xfe71, 0xfeab, 0xfeab, 0xfe75, 0xfe30, 0xfeab, 0xfeab, 0xfeab, 0xfeab, 0xfe77, 0xfeab, 0xfeab, 0xfe04, 0xfe12, 0xfe71, 0xfeab, 0xfeab, 0xfeab, 0xfe1b, 0xfe5e, 0xfe71, 0xfeab, 0xfeab, 0xfeab, 0xfe70),
     bit2tensor(0xffff, 0xfffe, 0x0001, 0xffff, 0xfffa, 0xfffe, 0xffff, 0xffff, 0xffff, 0xffff, 0xffff, 0x0000, 0x0003, 0x0000, 0xffff, 0xffff, 0xffff, 0xffff, 0xffff, 0x0002, 0xfffb, 0x0000, 0xffff, 0xffff, 0x0002, 0xfffe, 0xffff, 0x0000, 0x0001, 0x0008, 0xfffa, 0x0009),
     bit2tensor(0x008a, 0x0078, 0x0078, 0x008b, 0x0078, 0x0071, 0x0078, 0x0078, 0x007e, 0x0078, 0x0078, 0x0078, 0x006a, 0x007b, 0x0078, 0x0078, 0x0079, 0x0078, 0x0078, 0x0078, 0x006a, 0x008a, 0x0078, 0x007c, 0x0078, 0x0078, 0x0078, 0x0078, 0x0079, 0x007b, 0x0078, 0x0078),
     bit2tensor(0xf527, 0xf5b6, 0xf527, 0xf555, 0xf527, 0xf527, 0xf527, 0xf527, 0xf527, 0xf527, 0xf4db, 0xf504, 0xf4e1, 0xf527, 0xf545, 0xf527, 0xf527, 0xf546, 0xf527, 0xf4de, 0xf527, 0xf54f, 0xf527, 0xf527, 0xf527, 0xf4ff, 0xf527, 0xf527, 0xf501, 0xf527, 0xf527, 0xf489),
    ],
]

nn_outs = net(torch.from_numpy(input_data.astype(np.float32)))[0]
nn_mean = torch.mean(nn_outs, dim=0)
nn_stdev= torch.std(nn_outs, dim=0)

for i, voxel in enumerate(fully_parallel_out):
    outs = compute_outputs(*voxel)
    mean = torch.mean(outs, dim=0)
    std = torch.std(outs, dim=0)

    print("Voxel", i)
    for bv in range(outs.shape[1]):
        print(f"\tBValue {bvalues[bv]:>3}: NET={float(nn_mean[i][bv]):.6}??{float(nn_stdev[i][bv]):.6} ACC={float(mean[bv]):.6}??{float(std[bv]):.6}")
    print()
