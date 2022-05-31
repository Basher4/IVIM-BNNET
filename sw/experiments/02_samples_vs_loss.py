"""
This file loads NN trained in 01.py and evaluates inputs with different number of samples.
It then plots the mean and stdev on a chart. I'm interested in 2^0 .. 2^8 samples.
Is the number of samples I take (2^5) enough?
"""

import gzip
import os
import pickle
import time
import torch
import sys
import json

sys.path.append('./')

from IVIMNET.hyperparams import hyperparams as hp_example_1
import IVIMNET.simulations as sim
import IVIMNET.deep as deep
import IVIMNET.deep_bayes as deep_bayes
import IVIMNET.fitting_algorithms as fit

SNR = 15
SIGNAL_PATH = f"./data/signals/infer_{SNR}SNR.pickle.gz"
MODEL_PATH = "./models/bnn_e01_SNR{SNR}.pt"
BAYES_SAMPLES = 256

arg = hp_example_1()
arg = deep.checkarg(arg)
bvalues = arg.sim.bvalues
net_params = deep_bayes.net_params()

# Load inference signals.
with gzip.open(SIGNAL_PATH) as fd:
    [dwi_image_long, Dt_truth, Fp_truth, Dp_truth] = pickle.load(fd)

# Load neural net
net = torch.load(MODEL_PATH, map_location="cuda")

