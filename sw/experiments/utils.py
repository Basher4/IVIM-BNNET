import gzip
import pickle
import nibabel as nib
import numpy as np

def load_invivo_data(data_path, bv_path):
    # Load input data
    data = nib.load(data_path)
    datas = data.get_fdata()
    sx, sy, sz, n_b_values = datas.shape 
    X_dw = np.reshape(datas, (sx * sy * sz, n_b_values))
    # Load bvalues
    bvalues = np.genfromtxt(bv_path)
    selsb = bvalues == 0

    # Delete background and noise
    S0 = np.nanmean(X_dw[:, selsb], axis=1)
    S0[S0 != S0] = 0
    S0 = np.squeeze(S0)
    valid_id = (S0 > (0.5 * np.median(S0[S0 > 0]))) 
    datatot = X_dw[valid_id, :]
    # Normalise data
    S0 = np.nanmean(datatot[:, selsb], axis=1).astype('<f')
    datatot = datatot / S0[:, None]
    res = [i for i, val in enumerate(datatot != datatot) if not val.any()] # Remove NaN data

    return bvalues, datatot[res]

def load_infer_signals(snr) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    with gzip.open(f"./sw//data/signals/infer_{snr}SNR.pickle.gz", "rb") as fd:
        obj = pickle.load(fd)
    return obj
