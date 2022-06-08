"""
This file loads NN trained in 01.py and evaluates inputs with different number of samples.
It then plots the mean and stdev on a chart. I'm interested in 2^0 .. 2^8 samples.
Is the number of samples I take (2^5) enough?
"""

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

sys.path.append('./')
sys.path.append('./sw/')

from IVIMNET.hyperparams import hyperparams as hp_example_1
import IVIMNET.simulations as sim
import IVIMNET.deep as deep
import IVIMNET.deep_bayes as deep_bayes
import IVIMNET.fitting_algorithms as fit

SNR = int(sys.argv[1]) if len(sys.argv) > 1 else 5
SIGNAL_PATH = f"./sw/data/signals/infer_{SNR}SNR.pickle.gz"
IVIMBNNET_PATH = f"./sw/models/bnn_e01_SNR{SNR}_{{}}.pt"
IVIMNET_PATH = f"./sw/models/ivimnet_e07_SNR{SNR}_{{}}.pt"
OUTPUT_GRAPHS_PATH = f"./sw/plots/e02_samples_required_SNR{SNR}.png"
BAYES_SAMPLES = 256

arg = hp_example_1()
arg = deep.checkarg(arg)
bvalues = arg.sim.bvalues
net_params = deep_bayes.net_params()

# Load inference signals.
with gzip.open(SIGNAL_PATH) as fd:
    [dwi_image_long, Dt_truth, Fp_truth, Dp_truth] = pickle.load(fd)
    ground_truth = {
        "x": torch.from_numpy(dwi_image_long).float().to("cuda"),
        "dt": torch.from_numpy(Dt_truth).reshape((100*100, 1)),
        "fp": torch.from_numpy(Fp_truth).reshape((100*100, 1)),
        "dp": torch.from_numpy(Dp_truth).reshape((100*100, 1))
    }

# Load neural net
def eval_net(path):
    ivim_bnnet = torch.load(path.format(0), map_location="cuda")
    signals, Dt, Fp, Dp, s0 = ivim_bnnet(ground_truth["x"])
    dd = {
        "x": signals.detach().cpu().unsqueeze(dim=0),
        "dt": Dt.detach().cpu().unsqueeze(dim=0),
        "fp": Fp.detach().cpu().unsqueeze(dim=0),
        "dp": Dp.detach().cpu().unsqueeze(dim=0)
    }
    for i in range(1, 5):
        ivim_bnnet = torch.load(path.format(i), map_location="cuda")
        signals, Dt, Fp, Dp, s0 = ivim_bnnet(ground_truth["x"])
        dd = {
            "x": torch.cat([dd['x'], signals.detach().cpu().unsqueeze(dim=0)], dim=0),
            "dt": torch.cat([dd['dt'], Dt.detach().cpu().unsqueeze(dim=0)], dim=0),
            "fp": torch.cat([dd['fp'], Fp.detach().cpu().unsqueeze(dim=0)], dim=0),
            "dp": torch.cat([dd['dp'], Dp.detach().cpu().unsqueeze(dim=0)], dim=0)
        }
        del ivim_bnnet

    dd = {
        "x":  torch.mean(dd['x'], dim=0),
        "dt": torch.mean(dd['dt'], dim=0),
        "fp": torch.mean(dd['fp'], dim=0),
        "dp": torch.mean(dd['dp'], dim=0)
    }
    return dd

bnnet_samples = eval_net(IVIMBNNET_PATH)
ivim_output = eval_net(IVIMNET_PATH)

def eval_stats(arg_cs: str, ax):
    arg = arg_cs.lower()
    gt, bnnet_dat, ivim_dat = ground_truth[arg].cpu(), bnnet_samples[arg], ivim_output[arg]

    xlabels = []
    bnn_nrmse = []
    dnn_nrmse = []
    vs_nrmse = []
    bnn_cov = []
    dnn_cov = []
    q = torch.tensor([0.95]).cuda()

    for exponent in range(1, 9):
        hi_idx = 2 ** exponent - 1
        lo_idx = 2 ** (exponent - 1) - 1
        samples = bnnet_dat[lo_idx:hi_idx]
        assert(len(samples) == 2 ** (exponent - 1))

        xlabels.append(2 ** (exponent - 1))

        mean = torch.mean(samples, dim=0)
        std = torch.std(samples, dim=0)

        rmse = torch.sqrt((mean - gt) * (mean - gt))
        mu_rmse = torch.mean(rmse)
        sigma_rmse = torch.std(rmse) ** 2
        mu_nrmse = mu_rmse / torch.mean(samples)

        cov = float(sigma_rmse) / float(mu_rmse)
        bnn_cov.append(cov)
        

        rmse = torch.sqrt((ivim_dat - gt) * (ivim_dat - gt))
        ivim_mu_rmse = torch.mean(rmse)
        ivim_sigma_rmse = torch.std(rmse) ** 2
        ivim_mu_nrmse = ivim_mu_rmse / torch.mean(samples)

        cov = float(ivim_sigma_rmse) / float(ivim_mu_rmse)
        dnn_cov.append(cov)

        rmse = torch.sqrt((ivim_dat - mean) * (ivim_dat - mean))
        ivb_mu_rmse = torch.mean(rmse)
        ivb_sigma_rmse = torch.std(rmse) ** 2
        ivb_mu_nrmse = ivb_mu_rmse / torch.mean(samples)

        bnn_nrmse.append(float(mu_nrmse))
        dnn_nrmse.append(float(ivim_mu_nrmse))
        vs_nrmse.append(float(ivb_mu_nrmse))

        print(f"#Samples = {2**(exponent-1):>3} --BNN-> NRMSE = {float(mu_nrmse)} , CoV = {float(sigma_rmse) / float(mu_rmse)}")
        print(f"               -IVIM-> NRMSE = {float(ivim_mu_nrmse)} , CoV = {float(ivim_sigma_rmse) / float(ivim_mu_rmse)}")
        print(f"               ---VS-> NRMSE = {float(ivb_mu_nrmse)} , CoV = {float(ivb_sigma_rmse) / float(ivb_mu_rmse)}")

    ax.set_title(f"Error for parameter {arg_cs}")
    ax.set_xlabel("Number of samples")
    ax.set_xscale("log")
    ax.set_ylabel("NRMSE")
    ax.set_xticks(xlabels)
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    for xc in xlabels:
        ax.axvline(x=xc, c="#0c0c0c", alpha=0.1)
    l1, = ax.plot(xlabels, bnn_nrmse, color="#1f77b4", label="IVIM-BNNET")
    l2, = ax.plot(xlabels, dnn_nrmse, color="#ff740e", label="IVIM-NET")

    ax2 = ax.twinx()
    ax2.set_ylabel("Coefficient of Variation")
    l3, = ax2.plot(xlabels, bnn_cov, color="#0f67a4", label="Coef of Variation", linestyle='dashed', marker='s')
    l4, = ax2.plot(xlabels, dnn_cov, color="#ef6400", label="Coef of Variation", linestyle='dashed', marker='s')
    ax.legend(handles=[l1, l3, l2, l4], loc="right", bbox_to_anchor=(1, 0.4))



fig, axs = plt.subplots(4, 1, constrained_layout=True)
fig.set_size_inches(4, 12)
fig.suptitle(f"SNR {SNR}")
print('========= PARAMETER "x"')
eval_stats("X", axs[0])
print()

print('========= PARAMETER "Dt"')
eval_stats("Dt", axs[1])
print()

print('========= PARAMETER "Fp"')
eval_stats("Fp", axs[2])
print()

print('========= PARAMETER "Dp"')
eval_stats("Dp", axs[3])
print()

plt.savefig(OUTPUT_GRAPHS_PATH, dpi=100)
plt.show()
