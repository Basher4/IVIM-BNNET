"""
This file trains a batch of network on simulated inputs with different SNRs.
During training, 256 samples are taken to hopefully represent the underlying distribution well enough.
"""

import gzip
import os
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
FILE_PREFIX = "./models/bnn_e01_SNR{}"
SNRS = [5, 15, 20, 30, 50]
BAYES_SAMPLES = 256

arg = hp_example_1()
arg = deep.checkarg(arg)
bvalues = arg.sim.bvalues
net_params = deep_bayes.net_params()

for i in range(REPS):
    for snr in SNRS:
        file_prefix = FILE_PREFIX.format(snr) + f"_{i}"
        model_path = f"{file_prefix}.pt"
        info_path = f"{file_prefix}.json"
        signal_path = f"./data/signals/train_{snr}SNR.pickle.gz"

        # Load values
        with gzip.open(signal_path) as fd:
            IVIM_signal_noisy, D, f, Dp = pickle.load(fd)

        time_start = time.perf_counter()
        net, epoch, final_val_loss = deep_bayes.learn_IVIM(IVIM_signal_noisy, bvalues, arg, net_params=net_params, stats_out=True, bayes_samples=BAYES_SAMPLES)
        time_end = time.perf_counter()

        # Save the model and corresponding metadata if it's better than what exists.
        try:
            with open(info_path, "r") as fd:
                net_meta = json.load(fd)
                if net_meta['final_val_loss'] < final_val_loss:
                    continue
        except OSError:
            pass

        torch.save(net, model_path)
        with open(info_path, "w") as fd:
            json.dump({
                "signal_path": signal_path,

                "model_path": model_path,
                "snr": snr,
                "bayes_training_samples": BAYES_SAMPLES,
                "num_bvalues": len(bvalues),
                "dorpout_p": net_params.dropout,
                "activation_fn": net_params.activation,

                "epochs": epoch,
                "final_val_loss": final_val_loss,
                "training_time": time_end - time_start
            }, fd, indent=4)