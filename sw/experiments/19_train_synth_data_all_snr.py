"""
This file trains a network both clean and noisy data.
"""

import gzip
import os
import numpy as np
import pickle
import time
import torch
import sys
import json

sys.path.append('./')
sys.path.append('./sw/')

from IVIMNET.hyperparams import hyperparams as hp_example_1
import IVIMNET.simulations as sim
import IVIMNET.deep as deep
import IVIMNET.deep_bayes as deep_bayes
import IVIMNET.fitting_algorithms as fit

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 1
FILE_PREFIX = "./sw/models/bnn_e19"
SNRS = [5, 15, 20, 30, 50]
BAYES_SAMPLES = 256

arg = hp_example_1()
arg = deep.checkarg(arg)
bvalues = arg.sim.bvalues
net_params = deep_bayes.net_params()

IVIM_signal_noisy = []
for i in range(REPS):
    for snr in SNRS:
        signal_path = f"./sw/data/signals/train_{snr}SNR.pickle.gz"
        with gzip.open(signal_path) as fd:
            IVIM_signal_noisy.append(pickle.load(fd)[0])

IVIM_signal_noisy = np.concatenate(IVIM_signal_noisy, axis=0)

file_prefix = FILE_PREFIX.format(snr) + f"_{i}"
model_path = f"{file_prefix}.pt"
info_path = f"{file_prefix}.json"


time_start = time.perf_counter()
net, epoch, final_val_loss = deep_bayes.learn_IVIM(IVIM_signal_noisy, bvalues, arg, net_params=net_params, stats_out=True, bayes_samples=BAYES_SAMPLES)
time_end = time.perf_counter()

torch.save(net, model_path)
with open(info_path, "w") as fd:
    json.dump({
        "signal_path": f"./sw/data/signals/train_{SNRS}SNR.pickle.gz",

        "model_path": model_path,
        "snr": SNRS,
        "bayes_training_samples": BAYES_SAMPLES,
        "num_bvalues": len(bvalues),
        "dorpout_p": net_params.dropout,
        "activation_fn": net_params.activation,

        "epochs": epoch,
        "final_val_loss": final_val_loss,
        "training_time": time_end - time_start
    }, fd, indent=4)
