import os
from fixedpoint import FixedPoint
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import sys
import pickle

sys.path.append('./hw/python')
sys.path.append('./hw/python/perf_model')

from perf_model.config import *
from perf_model.ProcessingUnit import ProcessingUnit

MEM_FOLDER = "./mem_files/for_testbench/fully_parallel_16_3"
DIN_PATH = f"{MEM_FOLDER}/din.mem"
PERC_PATH = f"{MEM_FOLDER}/perc_{{}}_params.mem"

RANGE_FRAC = int(sys.argv[1]) if len(sys.argv) >= 2 else 1
RANGE_TOTAL = int(sys.argv[2]) if len(sys.argv) >= 2 else 1

def sigmoid(x):
    return 1.0/(1.0+np.exp(-x))

def load_memfile(path, signed, m, n):
    with open(path, "r") as fd:
        lines = fd.readlines()
    
    res = []
    for line in tqdm(lines):
        row = []
        for num_candidate in line.split():
            if num_candidate == '//' or num_candidate.startswith('//'):
                break
            
            row.append(FixedPoint(f"0x{num_candidate}", signed, m, n, overflow=OVERFLOW))
        if len(row) > 0:
            res.append(row)

    return np.array(res)

din = load_memfile(DIN_PATH, True, NUM_INT_BITS, NUM_FRAC_BITS)[:, :11]
# din = load_memfile(DIN_PATH, True, NUM_INT_BITS, NUM_FRAC_BITS)[:, :11].reshape((100,100,11))
# fig,ax = plt.subplots(1, 11)
# for i in range(11):
#     ax[i].imshow(din[:,:,i])
# plt.show()

# din_mean = []
# for col in range(0, 100, 10):
#     din_mean.append([])
#     for row in range(0, 100, 10):
        
#         dat = np.mean(np.mean(din[col:row, col+10:row+10, :], axis=0), axis=0)
#         print(dat.shape)

#         din_mean[-1].append(dat)
# din = np.array(din_mean)

perc_params = [load_memfile(PERC_PATH.format(i), False, NUM_WIDTH*129, 0).reshape(-1) for i in range(11)]

print("Computing data")
pu = ProcessingUnit(perc_params, 32, 11)
data = []
li = len(din) * (RANGE_FRAC-1) // RANGE_TOTAL
hi = len(din) * RANGE_FRAC // RANGE_TOTAL

print(len(din), "Evaluating elements from", li, "to", hi)
for dd in tqdm(din[li:hi]):
    res = pu.calculate(dd)
    vox = []

    for par in res:
        arr = []
        for s in par:
            arr.append(s)
        vox.append(arr)
    data.append(vox)

data = np.array(data)
print(data.shape)

with open("synth_eval_fixed.pickle", "wb") as fd:
    pickle.dump(data, fd)

fig,ax = plt.subplots(1, 4)
for i in range(4):
    for x in range(data.shape[0]):
        data[x,i] = float(data[x,i])
    ax[i].imshow(data[:,i].astype(float).reshape(100,100))
plt.savefig("plot.png")
