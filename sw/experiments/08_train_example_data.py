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
import IVIMNET.simulations as sim
import IVIMNET.deep as deep
import IVIMNET.deep_bayes as deep_bayes
import IVIMNET.fitting_algorithms as fit

arg = hp_example_1()
arg = deep.checkarg(arg)
arg.fit.do_fit = False
net_params = deep_bayes.net_params()

testdata = False

EPOCHS = 1000
BAYES_SAMPLES = 256

### folder patient data
folder = './sw/data/example_data'
model_path = './sw/models/bnn_e08_patient'

### load patient data
print('Load patient data \n')
# load and init b-values
text_file = np.genfromtxt('{folder}/bvalues.bval'.format(folder=folder))
bvalues = np.array(text_file)
selsb = np.array(bvalues) == 0
# load nifti
data = nib.load('{folder}/data.nii.gz'.format(folder=folder))
datas = data.get_fdata() 
# reshape image for fitting
sx, sy, sz, n_b_values = datas.shape 
X_dw = np.reshape(datas, (sx * sy * sz, n_b_values))

### select only relevant values, delete background and noise, and normalise data
S0 = np.nanmean(X_dw[:, selsb], axis=1)
S0[S0 != S0] = 0
S0 = np.squeeze(S0)
valid_id = (S0 > (0.5 * np.median(S0[S0 > 0]))) 
datatot = X_dw[valid_id, :]
# normalise data
S0 = np.nanmean(datatot[:, selsb], axis=1).astype('<f')
datatot = datatot / S0[:, None]
print('Patient data loaded\n')

print('NN fitting\n')
res = [i for i, val in enumerate(datatot != datatot) if not val.any()] # Remove NaN data

# train network
time_start = time.perf_counter()
net, epochs, best_val_loss = deep_bayes.learn_IVIM(datatot[res], bvalues, arg, net_params=net_params, epochs=EPOCHS, stats_out=True, bayes_samples=BAYES_SAMPLES)
time_end = time.perf_counter() - time_start
print('\ntime elapsed for Net: {}\n'.format(time_end))

# Save the network
torch.save(net, f"{model_path}.pt")
with open(f"{model_path}.json", "w") as fd:
    json.dump({
        "signal_path": f"{folder}/data.nii.gz",

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
