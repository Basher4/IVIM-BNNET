from collections import defaultdict
import numpy as np
import json

BNN_PATH = f"./sw/models/bnn_e01_snr{{}}_{{}}.json"
DNN_ELU_PATH = f"./sw/models/ivim_e05_SNR{{}}_{{}}.json"
DNN_RELU_PATH = f"./sw/models/ivimnet_e07_SNR{{}}_{{}}.json"

SNR = [5, 15, 20, 30, 50]

bnn_loss = defaultdict(list)
de_loss = defaultdict(list)
dr_loss = defaultdict(list)

for i in range(5):
    for snr in SNR:
        with open(BNN_PATH.format(snr, i), "r") as fd:
            bnn = json.load(fd)
        with open(DNN_ELU_PATH.format(snr, i), "r") as fd:
            de = json.load(fd)
        with open(DNN_RELU_PATH.format(snr, i), "r") as fd:
            dr = json.load(fd)

        bnn_loss[snr].append(bnn["final_val_loss"])
        de_loss[snr].append(de["final_val_loss"])
        dr_loss[snr].append(dr["final_val_loss"])

for snr in SNR:
    print("For SNR", snr)
    print("BNN ", np.mean(bnn_loss[snr]), np.std(bnn_loss[snr]))
    print("ELU ", np.mean(de_loss[snr]), np.std(de_loss[snr]))
    print("ReLU", np.mean(dr_loss[snr]), np.std(dr_loss[snr]))
