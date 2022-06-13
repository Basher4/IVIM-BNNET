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

from IVIMNET.hyperparams import hyperparams as hp_example_1
import IVIMNET.deep as deep
import IVIMNET.deep_bayes as deep_bayes
import experiments.utils as exp_utils

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
EPOCHS = 1000
BAYES_SAMPLES = 256

INPUT_DATA_DIR = "./sw/data/invivo_data"
INPUT_DATA_1_PATH = f"{INPUT_DATA_DIR}/ds1.nii"
INPUT_BVAL_1_PATH = f"{INPUT_DATA_DIR}/ds1.bval"
INPUT_DATA_2_PATH = f"{INPUT_DATA_DIR}/ds2.nii"
INPUT_BVAL_2_PATH = f"{INPUT_DATA_DIR}/ds2.bval"
INPUT_PATHS = [
    (INPUT_DATA_1_PATH, INPUT_BVAL_1_PATH),
    (INPUT_DATA_2_PATH, INPUT_BVAL_2_PATH)
]

OUTPUT_PATH_TEMPLATE = "./sw/models/bnn_e13_ds{ds}_{rep}"

arg = hp_example_1()
arg.fit.do_fid = False
net_params = deep_bayes.net_params()


def train_network(i):
    data_path, bv_path = INPUT_PATHS[i]
    bvalues, traindata = exp_utils.load_invivo_data(data_path, bv_path)

    for it in range(REPS):
        # Train net
        time_start = time.perf_counter()
        net, epochs, best_val_loss = deep_bayes.learn_IVIM(traindata, bvalues, arg,
                                                           net_params=net_params, epochs=EPOCHS,
                                                           stats_out=True, bayes_samples=BAYES_SAMPLES)
        time_end = time.perf_counter() - time_start
        # Save outputs
        model_path = OUTPUT_PATH_TEMPLATE.format(ds=i+1, rep=it)
        torch.save(net, f"{model_path}.pt")
        with open(f"{model_path}.json", "w") as fd:
            json.dump({
                "signal_path": data_path,

                "model_path": model_path,
                "snr": -1,
                "bayes_training_samples": BAYES_SAMPLES,
                "num_bvalues": len(bvalues),
                "dorpout_p": net_params.dropout,
                "activation_fn": net_params.activation,

                "epochs": epochs,
                "final_val_loss": best_val_loss,
                "training_time": time_end
            }, fd, indent=4)


if __name__ == "__main__":
    train_network(0)
    train_network(1)
