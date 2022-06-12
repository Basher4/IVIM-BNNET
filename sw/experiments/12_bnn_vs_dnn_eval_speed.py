from time import perf_counter
from tqdm import tqdm
import gzip
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pickle
import sys
import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data as utils

sys.path.append('./')
sys.path.append('./sw/')

DEVICE = "cpu"
NEURAL_NETWORK_PATH = "./sw/models/bnn_e08_patient.pt"
INPUT_SIGNALS_FOLDER = "./sw/data/example_data"
### load patient data
print('Load patient data \n')
# load and init b-values
text_file = np.genfromtxt(f'{INPUT_SIGNALS_FOLDER}/bvalues.bval')
bvalues = np.array(text_file)
selsb = np.array(bvalues) == 0
# load nifti
data = nib.load(f'{INPUT_SIGNALS_FOLDER}/data.nii.gz')
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

input_data = datatot[res]

bnn = torch.load(NEURAL_NETWORK_PATH, map_location=DEVICE)
inferloader = utils.DataLoader(torch.from_numpy(input_data.astype(np.float32)),
                                   batch_size=2048,
                                   shuffle=False,
                                   drop_last=False)

time = []
for i in tqdm(range(10)):
    s = perf_counter()
    with torch.no_grad():
        for i, X_batch in tqdm(enumerate(inferloader, 0), leave=False, total=len(inferloader)):
            X_batch = X_batch.to(DEVICE)
            # here the signal is predicted. Note that we now are interested in the parameters and no longer in the predicted signal decay.
            Xt, Dtt, Fpt, Dpt, S0t = bnn(X_batch)
    e = perf_counter()
    time.append(e-s)
print(f"To evaluate BNN on a CPU takes {np.mean(time)}+-{np.std(time)}s")
print(f"Evaluated {len(input_data)} voxels -> {np.mean(time)*1000000/len(input_data)}*10^-6 s/voxel +- {np.std(time)*1000000/len(input_data)}")
print(f"Shape of data", datas.shape)
del bnn

# dnn = torch.load(DNN_PATH, map_location="cuda")
# time = 0
# for i in range(10):
#     s = perf_counter()
#     dnn(X)
#     e = perf_counter()
#     time += e - s
# time /= 10
# print(f"To evaluate DNN on a GPU takes {time}s")
# del dnn
