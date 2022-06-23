"""
This file loads parameters of NN generated by 01.py and
    1) Fuses batch normalization parameter with preceeding weights
    2) Finds the best nuber of integer and fractional bits to represent weights and biases
"""

from fixedpoint import FixedPoint
import gzip
import itertools
import json
import numpy as np
import nibabel as nib
import pickle
import sys
import torch, torch.quantization

sys.path.append('./sw/')

NEURAL_NETWORK_PATH = "./sw/models/bnn_e08_patient.pt"
MEM_FILE_PATH = "./mem_files/for_testbench/32_lanes"
INPUT_SIGNALS_FOLDER = "./sw/data/example_data"
INPUT_SIGNALS_PATH = "./sw/data/example_data/data.nii.gz"
ACCELERATOR_NUM_LANES = 32
accelerator_perceptrons = [[] for _ in range(ACCELERATOR_NUM_LANES)]
TOTAL_BITS = 16
MEMORY_WIDTH = 128 + 1
PAD_WITH_ZEROS = True
INT_BITS = 3
PLOT = False

try:
    print(sys.argv)
    MEM_FILE_PATH = sys.argv[1]
    print("MEM_FILE_PATH", MEM_FILE_PATH)
    INT_BITS = int(sys.argv[2])
    print("INT_BITS", INT_BITS)
    TOTAL_BITS = int(sys.argv[3])
    print("TOTAL_BITS", TOTAL_BITS)
    PLOT = bool(int(sys.argv[4]))
    print("PLOT", PLOT)
except:
    print("Argument parsing done. Lol.")

# Load neural network
net: torch.nn.Module = torch.load(NEURAL_NETWORK_PATH, map_location="cpu")
net.eval()
network_parameters = dict(net.named_parameters())

# Merge weights with Batch Normalization
def merge_weights_with_bn(linear_layer, batch_norm):
    coef = (batch_norm.weight)/torch.sqrt(batch_norm.running_var+batch_norm.eps)
    w_ = coef * linear_layer.weight
    b_ = coef * (linear_layer.bias - batch_norm.running_mean) + batch_norm.bias
    print(coef.shape, w_.shape, b_.shape)
    return w_.detach(), b_.detach()

param_sum, param_count = 0, 0
params_arr = []

to_fuse = []
for param_net in range(4):
    for offset in [0, 4]:
        to_fuse.append([f"fc_layers.{param_net}.{offset}", f"fc_layers.{param_net}.{offset+2}"])
fnet = torch.ao.quantization.fuse_modules(net, to_fuse)

for param_net in range(4):
    for offset in [0, 4]:
        linear_layer: torch.nn.Linear = fnet.get_submodule(f"fc_layers.{param_net}.{offset}")
        w, b = linear_layer.weight, linear_layer.bias

        for perc_idx in range(b.shape[0]):
            val = torch.concat((b[perc_idx].unsqueeze(dim=0),w[perc_idx]))
            print(".", end="")

            accelerator_perceptrons[perc_idx % ACCELERATOR_NUM_LANES].append(val)
            # Sanity check
            params_arr.append(w.T[perc_idx].numpy())
            params_arr.append(b[perc_idx].numpy().reshape(1))

    encoder_layer: torch.nn.Linear = net.get_submodule(f"encoder.{param_net}.8")
    for i in range(ACCELERATOR_NUM_LANES):
        accelerator_perceptrons[i].append(torch.concat((encoder_layer.bias, encoder_layer.weight.squeeze())))

params_arr = np.concatenate(params_arr)

# Find the best quantization
print(f"Every perceptron ({ACCELERATOR_NUM_LANES} in total) requires memory {len(accelerator_perceptrons[0])} deep")
print(f"Parameter stats:")
print(f"\tCount = {len(params_arr)}\n\tMean  = {np.mean(params_arr)}")
print(f"\tMedian= {np.median(params_arr)}\n\tStdev = {np.std(params_arr)}\n")

### load patient data
print('Load patient data \n')
# load and init b-values
text_file = np.genfromtxt(f'{INPUT_SIGNALS_FOLDER}/bvalues.bval')
bvalues = np.array(text_file)
selsb = np.array(bvalues) == 0
# load nifti
data = nib.load(INPUT_SIGNALS_PATH)
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

# best_int_bits = 0
# best_rmse = 9999
# for int_bits in range(1, TOTAL_BITS):
#     error = 0
#     rmse = 0
#     denom = 0

#     # Error from weights and biases.
#     for ps in itertools.chain.from_iterable(accelerator_perceptrons):
#         for we in ps:
#             err = we - float(FixedPoint(float(we), True, int_bits, TOTAL_BITS - int_bits))
#             error += err * err
#         denom += ps.shape[0]

#     # Error from input signal
#     signal_noisy = input_data[0]
#     for vox in signal_noisy:
#         for bv in vox:
#             err = we - float(FixedPoint(float(we), True, int_bits, TOTAL_BITS - int_bits))
#             error += err * err
#     denom += signal_noisy.shape[0] * signal_noisy.shape[1]

#     error /= denom
#     rmse = torch.sqrt(error)

#     print(f"INT_BITS = {int_bits} , RMSE = {rmse}")

#     if rmse < best_rmse:
#         best_rmse = rmse
#         best_int_bits = int_bits
best_int_bits = 3

# Output memory files for perceptrons
for pi, pd in enumerate(accelerator_perceptrons):
    with open(f"{MEM_FILE_PATH}/perc_{pi}_params_32lanes.mem", "w") as fd:
        fd.write(f"// INT_BITS = {best_int_bits}\n")
        for si, sd in enumerate(pd):
            pdata = [FixedPoint(val, True, best_int_bits, TOTAL_BITS - best_int_bits) for val in sd]
            if PAD_WITH_ZEROS:
                while len(pdata) < MEMORY_WIDTH:
                    pdata.append(FixedPoint(0, True, best_int_bits, TOTAL_BITS - best_int_bits))

            fd.write("".join(f"{elem:0{4}x}" for elem in pdata))
            fd.write(f"    // bias = {pdata[0]:0{4}x}, w[0] = {pdata[1]:0{4}x}, w[{len(sd)-2}] = {pdata[len(sd)-1]:0{4}x}")
            fd.write('\n')


# Quantize voxel data
with open(f"{MEM_FILE_PATH}/din_32lanes.mem", "w") as fd:
    fd.write(f"// INT_BITS = {best_int_bits}, {len(input_data)} elements\n")
    
    for voxel in input_data:
        pdata = [FixedPoint(bv, True, best_int_bits, TOTAL_BITS - best_int_bits, overflow='clamp', overflow_alert='warning') for bv in voxel]
        fd.write(" ".join(f"{elem:0{4}x}" for elem in pdata))
        if PAD_WITH_ZEROS:
            fd.write(" ".join("0" for _ in range(128 - len(pdata))))
        fd.write(f"    // bv0 = {pdata[0]:0{4}x}\n")
