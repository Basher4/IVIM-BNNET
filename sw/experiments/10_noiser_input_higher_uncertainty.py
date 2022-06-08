from collections import defaultdict
import gzip
import os
import pickle
import time
from matplotlib import markers, pyplot as plt
import matplotlib
import torch
import sys
import json

from tqdm import tqdm

sys.path.append('./sw/')

from IVIMNET.hyperparams import hyperparams as hp_example_1
import IVIMNET.simulations as sim
import IVIMNET.deep as deep
import IVIMNET.deep_bayes as deep_bayes
import IVIMNET.fitting_algorithms as fit

BNN_PATH = f"./sw/models/bnn_e01_SNR{{}}_{{}}.pt"
SIGNAL_PATH = f"./sw/data/signals/infer_{{}}SNR_{{}}.pickle.gz"
PLOT_PATH = f"./sw/plots/e10_bnn_cov_vs_snr.png"
SNR = [50, 30, 20, 15, 5]
i = 0

cov_global = defaultdict(list)

device = "cpu"

pbar = tqdm(total=len(SNR)**2)
for train_snr in SNR:
    net = torch.load(BNN_PATH.format(train_snr, i), map_location=device)
    for eval_snr in SNR:
        with gzip.open(SIGNAL_PATH.format(eval_snr, i)) as fd:
            [dwi_image_long, Dt_truth, Fp_truth, Dp_truth] = pickle.load(fd)
            ground_truth = {
                "x": torch.from_numpy(dwi_image_long).float().to(device),
                "dt": torch.from_numpy(Dt_truth).reshape((100*100, 1)),
                "fp": torch.from_numpy(Fp_truth).reshape((100*100, 1)),
                "dp": torch.from_numpy(Dp_truth).reshape((100*100, 1))
            }

        x, dt, fp, dp, s0 = net(ground_truth["x"])

        x_mu = torch.mean(x, dim=0)
        x_sigma = torch.std(x, dim=0) ** 2
        x_cov = x_mu / x_sigma

        cov_global[train_snr].append(x_cov)
        
        del x
        del dt
        del fp
        del dp
        del s0
        del x_mu
        del x_sigma
        del x_cov
        del ground_truth["x"]
        pbar.update(1)
    del net
pbar.close()

with open("./sw/data/e10_dict.pickle", "wb"):
    pickle.dump(cov_global, fd)

for train_snr in SNR:
    plt.plot(cov_global[train_snr], label=f"Traning SNR {train_snr}")
plt.legend(loc=0)
plt.title("Coefficient of Variation for IVIM-BNNET")
plt.xticks(SNR)
plt.tight_layout()
# plt.savefig()
plt.show()
