from collections import defaultdict
import gzip
import json
import nibabel as nib
import numpy as np
import os
import pickle
import sys
import time
import torch
from tqdm import tqdm

sys.path.append('./')
sys.path.append('./sw/')

from experiments.utils import load_infer_signals
from IVIMNET.hyperparams import hyperparams as hp_example_1
import IVIMNET.simulations as sim
import IVIMNET.deep as deep
import IVIMNET.deep_bayes as deep_bayes
import IVIMNET.fitting_algorithms as fit

DEVICE = "cuda"
NET_PATH = "./sw/models/ivim_e05_SNR{snr}_{it}.pt"
bvals = torch.tensor([0, 5, 10, 20, 30, 40, 60, 150, 300, 500, 700])

times = np.zeros((5, 5, 100))

for si, snr in tqdm(enumerate([5, 15, 20, 30, 50])):
    data = load_infer_signals(snr)[0]
    data = torch.from_numpy(data.astype(np.float32)).to(DEVICE)
    for it in tqdm(range(5), leave=False):
        net = torch.load(NET_PATH.format(snr = snr, it = it), map_location=DEVICE)
        for x in tqdm(range(100), leave=False):
            ts = time.perf_counter()
            _ = net(data)
            te = time.perf_counter()
            times[si][it][x] = te - ts
        del net

# times = times*10e6/data.shape[0]
# print(f"Mean inference time = {np.mean(times)}e-6 s/vox")
# print(f"Median inference time = {np.median(times)}e-6 s/vox")
# print(f"Evaluated {data.shape[0]} voxels")
# print(f"Stdev", np.std(times))
