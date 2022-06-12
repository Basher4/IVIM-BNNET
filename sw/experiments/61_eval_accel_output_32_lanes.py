from dataclasses import dataclass
from fixedpoint import FixedPoint
import gzip
import itertools
import json
import nibabel as nib
import numpy as np
import pickle
import sys
import torch

sys.path.append('./sw/')

NEURAL_NETWORK_PATH = "./sw/models/bnn_e08_patient.pt"
MEM_FILE_PATH = "./mem_files/for_testbench/32_lanes"
INPUT_SIGNALS_FOLDER = "./sw/data/example_data"
INPUT_SIGNALS_PATH = "./sw/data/example_data/data.nii.gz"
ACCELERATOR_NUM_LANES = 11
accelerator_perceptrons = [[] for _ in range(ACCELERATOR_NUM_LANES)]
INT_BITS = 3
TOTAL_BITS = 16
MEMORY_WIDTH = 128 + 1
PAD_WITH_ZEROS = True

bvalues = torch.from_numpy(np.fromfile('./sw/data/example_data/bvalues.bval'))
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


### load patient data
print('Load patient data')
# load and init b-values
text_file = np.genfromtxt(f'{INPUT_SIGNALS_FOLDER}/bvalues.bval')
bvalues = np.array(text_file)
selsb = np.array(bvalues) == 0
# load nifti
data = nib.load(INPUT_SIGNALS_PATH)
datas = data.get_fdata() 
# reshape image for fitting
sx, sy, sz, n_b_values = datas.shape 
X_dw = np.reshape(datas, (sx * sy * sz, n_b_values))

### select only relevant values, delete background and noise, and normalise data
S0 = np.nanmean(X_dw[:, selsb], axis=1)
S0[S0 != S0] = 0
S0 = np.squeeze(S0)
valid_id = (S0 > (0.5 * np.median(S0[S0 > 0]))) 
datatot = X_dw[valid_id, :]
# normalise data
S0 = np.nanmean(datatot[:, selsb], axis=1).astype('<f')
datatot = datatot / S0[:, None]
res = [i for i, val in enumerate(datatot != datatot) if not val.any()] # Remove NaN data

input_data = datatot[res]

print(input_data.shape)


def bit2tensor(*lst):
    return torch.tensor([float(FixedPoint(hex(x), True, INT_BITS, TOTAL_BITS - INT_BITS)) for x in lst])


fully_parallel_out = [[
    bit2tensor(0xf81d,0xf849,0xf820,0xf801,0xf869,0xf857,0xf848,0xf82b,0xf84c,0xf7ef,0xf84a,0xf864,0xf835,0xf81c,0xf85e,0xf836,0xf83b,0xf810,0xf81e,0xf7ca,0xf839,0xf81e,0xf80a,0xf822,0xf82f,0xf838,0xf7ec,0xf856,0xf80f,0xf82d,0xf86c,0xf81a,),
    bit2tensor(0x006a,0x006f,0x006f,0x006e,0x0069,0x006f,0x006f,0x006f,0x006c,0x0071,0x006f,0x006f,0x0069,0x0066,0x0072,0x0070,0x0065,0x006f,0x0070,0x0070,0x0073,0x0070,0x0075,0x0070,0x006a,0x0070,0x006f,0x006f,0x006f,0x006f,0x006f,0x006e,),
    bit2tensor(0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe3,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,),
    bit2tensor(0xff44,0xff45,0xff45,0xff45,0xff45,0xff43,0xff45,0xff45,0xff45,0xff45,0xff44,0xff44,0xff44,0xff44,0xff43,0xff44,0xff45,0xff44,0xff44,0xff44,0xff44,0xff45,0xff45,0xff45,0xff44,0xff45,0xff44,0xff45,0xff43,0xff42,0xff44,0xff44,),
    ],[
    bit2tensor(0xf82b,0xf817,0xf825,0xf7fc,0xf878,0xf823,0xf855,0xf831,0xf817,0xf80c,0xf82a,0xf821,0xf816,0xf811,0xf80a,0xf821,0xf834,0xf830,0xf855,0xf82a,0xf833,0xf848,0xf7fa,0xf81b,0xf849,0xf840,0xf837,0xf83b,0xf841,0xf84d,0xf834,0xf85b,),
    bit2tensor(0x0071,0x006f,0x006f,0x006f,0x006f,0x0070,0x0071,0x0070,0x0070,0x0070,0x006f,0x0060,0x0071,0x006f,0x006f,0x0070,0x0070,0x006d,0x0069,0x0070,0x006e,0x0070,0x0071,0x0070,0x006f,0x0070,0x0070,0x0070,0x006f,0x0077,0x006e,0x006e,),
    bit2tensor(0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe3,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe3,0xffe4,0xffe4,0xffe4,0xffe4,),
    bit2tensor(0xff48,0xff46,0xff44,0xff44,0xff44,0xff46,0xff45,0xff44,0xff45,0xff44,0xff45,0xff44,0xff45,0xff44,0xff42,0xff44,0xff42,0xff48,0xff45,0xff44,0xff44,0xff45,0xff45,0xff44,0xff44,0xff45,0xff45,0xff49,0xff45,0xff42,0xff44,0xff43,),
    ],[
    bit2tensor(0xf84a,0xf807,0xf829,0xf7fe,0xf832,0xf812,0xf825,0xf7ea,0xf82c,0xf826,0xf83f,0xf84e,0xf809,0xf830,0xf843,0xf875,0xf808,0xf81b,0xf80b,0xf85b,0xf7f2,0xf815,0xf819,0xf82a,0xf823,0xf851,0xf819,0xf82a,0xf7e6,0xf80b,0xf7f8,0xf849,),
    bit2tensor(0x0070,0x0070,0x0070,0x0073,0x0071,0x0064,0x006f,0x0070,0x0061,0x006f,0x0070,0x006e,0x006e,0x0069,0x006f,0x0070,0x006f,0x0070,0x0070,0x006f,0x0070,0x006f,0x006e,0x006f,0x006f,0x0071,0x0071,0x0070,0x006c,0x006f,0x006e,0x0070,),
    bit2tensor(0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe3,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe3,0xffe4,0xffe4,),
    bit2tensor(0xff44,0xff45,0xff44,0xff47,0xff44,0xff44,0xff45,0xff44,0xff44,0xff42,0xff46,0xff44,0xff44,0xff44,0xff45,0xff44,0xff44,0xff44,0xff44,0xff44,0xff44,0xff44,0xff45,0xff46,0xff44,0xff45,0xff47,0xff44,0xff44,0xff44,0xff45,0xff44,),
    ],[
    bit2tensor(0xf819,0xf7f3,0xf86b,0xf7e1,0xf82f,0xf84f,0xf821,0xf85b,0xf844,0xf82b,0xf7e8,0xf832,0xf818,0xf822,0xf843,0xf823,0xf845,0xf818,0xf816,0xf869,0xf843,0xf811,0xf817,0xf813,0xf85c,0xf81e,0xf805,0xf83d,0xf817,0xf84b,0xf7e2,0xf85b,),
    bit2tensor(0x006f,0x006f,0x006b,0x006e,0x006f,0x006f,0x0068,0x0070,0x006f,0x0071,0x0063,0x0070,0x0070,0x0072,0x006f,0x0070,0x0057,0x0070,0x006a,0x006e,0x006f,0x0070,0x006f,0x0070,0x0070,0x006b,0x006e,0x0070,0x007c,0x0070,0x006f,0x0070,),
    bit2tensor(0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe3,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe4,0xffe3,0xffe4,0xffe4,0xffe4,0xffe4,),
    bit2tensor(0xff45,0xff45,0xff44,0xff48,0xff44,0xff47,0xff45,0xff44,0xff46,0xff45,0xff43,0xff45,0xff44,0xff44,0xff42,0xff45,0xff42,0xff47,0xff46,0xff44,0xff45,0xff44,0xff44,0xff44,0xff44,0xff44,0xff42,0xff45,0xff45,0xff45,0xff45,0xff45,),
    ]
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
        print(f"\tBValue {bvalues[bv]:>3}: NET={float(nn_mean[i][bv]):.6}±{float(nn_stdev[i][bv]):.6} ACC={float(mean[bv]):.6}±{float(std[bv]):.6}")
    print()
