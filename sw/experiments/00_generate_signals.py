"""
Generate signals used for training and inference.
"""

import gzip
import pickle
import sys
from tqdm import tqdm

sys.path.append('./')

from IVIMNET.hyperparams import hyperparams as hp_example_1
import IVIMNET.simulations as sim
import IVIMNET.deep as deep

SNRS = [5, 15, 20, 30, 50]
arg = hp_example_1()
arg = deep.checkarg(arg)

for snr in tqdm(SNRS):
    train_signals = sim.sim_signal(snr, arg.sim.bvalues, sims=arg.sim.sims, Dmin=arg.sim.range[0][0],
                                   Dmax=arg.sim.range[1][0], fmin=arg.sim.range[0][1],
                                   fmax=arg.sim.range[1][1], Dsmin=arg.sim.range[0][2],
                                   Dsmax=arg.sim.range[1][2], rician=arg.sim.rician)

    with gzip.open(f"./data/signals/train_{snr}SNR.pickle.gz", "wb") as fd:
        pickle.dump(train_signals, fd)

    infer_signals = sim.sim_signal_predict(arg, snr)
    with gzip.open(f"./data/signals/infer_{snr}SNR.pickle.gz", "wb") as fd:
        pickle.dump(infer_signals, fd)

