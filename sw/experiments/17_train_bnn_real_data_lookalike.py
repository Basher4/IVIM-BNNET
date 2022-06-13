"""
Train BNN on synthetic data with the same b-values as the original dataset.
"""

import gzip
import json
import nibabel as nib
import numpy as np
import os
import pickle
import sys
import time
import torch

sys.path.append('./')
sys.path.append('./sw/')

from experiments import utils
from IVIMNET.hyperparams import hyperparams as hp_example_1
import IVIMNET.simulations as sim
import IVIMNET.deep as deep
import IVIMNET.deep_bayes as deep_bayes
import IVIMNET.fitting_algorithms as fit

DATA_PATH = "./sw/data/example_data/data.nii.gz"
BVAL_PATH = "./sw/data/example_data/bvalues.bval"
model_path = "./sw/models/bnn_e17.pt"
info_path = "./sw/models/bnn_e17.json"
BAYES_SAMPLES = 128

arg = hp_example_1()
arg = deep.checkarg(arg)
net_params = deep_bayes.net_params()

def sim_data(snr, bvals):
    path = f"./sw/data/signals/example_data_synth_snr{snr}.pickle.gz"
    if os.path.exists(path):
        print("Loading cached simulation data with SNR", snr)
        with gzip.open(path, "rb") as fd:
            return pickle.load(fd)

    print("Simulating data for SNR", snr)
    ts = time.perf_counter()
    train_signals = sim.sim_signal(snr, bvals, sims=arg.sim.sims, Dmin=arg.sim.range[0][0],
                          Dmax=arg.sim.range[1][0], fmin=arg.sim.range[0][1],
                          fmax=arg.sim.range[1][1], Dsmin=arg.sim.range[0][2],
                          Dsmax=arg.sim.range[1][2], rician=arg.sim.rician)
    with gzip.open(path, "wb") as fd:
        pickle.dump(train_signals, fd)
    te = time.perf_counter()
    print("Finished in", te - ts, "seconds")

    return train_signals

bvalues, datatot = utils.load_invivo_data(DATA_PATH, BVAL_PATH)

# Simulate data to train
train_signals_5 = sim_data(5, bvalues)
train_signals_50 = sim_data(50, bvalues)

# Train network
X_train = np.concatenate((train_signals_5[0], train_signals_50[0]), axis=0)
time_start = time.perf_counter()
net, epoch, final_val_loss = deep_bayes.learn_IVIM(X_train, bvalues, arg, net_params=net_params, stats_out=True, bayes_samples=BAYES_SAMPLES)
time_end = time.perf_counter()

torch.save(net, model_path)
with open(info_path, "w") as fd:
    json.dump({
        "signal_path": DATA_PATH,

        "model_path": model_path,
        "snr": -1,
        "bayes_training_samples": BAYES_SAMPLES,
        "num_bvalues": len(bvalues),
        "dorpout_p": net_params.dropout,
        "activation_fn": net_params.activation,

        "epochs": epoch,
        "final_val_loss": final_val_loss,
        "training_time": time_end - time_start
    }, fd, indent=4)
