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
import pickle
import sys
import torch

sys.path.append('./sw/')

NEURAL_NETWORK_PATH = "./sw/models/bnn_e01_SNR5_0.pt"
MEM_FILE_PATH = "./mem_files/for_testbench/fully_parallel"
INPUT_SIGNALS_PATH = "./sw/data/signals/infer_5SNR.pickle.gz"
ACCELERATOR_NUM_LANES = 11
accelerator_perceptrons = [[] for _ in range(ACCELERATOR_NUM_LANES)]
TOTAL_BITS = 16
MEMORY_WIDTH = 128 + 1
PAD_WITH_ZEROS = False

# Load neural network
net: torch.nn.Module = torch.load(NEURAL_NETWORK_PATH, map_location="cpu")
network_parameters = dict(net.named_parameters())

# Merge weights with Batch Normalization
def merge_weights_with_bn(lin_w, lin_b, bn_w, bn_b):
    w = lin_w * bn_w
    b = bn_w * lin_b + bn_b
    return w.detach(), b.detach()

param_sum, param_count = 0, 0
params_arr = []

for param_net in range(4):
    for offset in [0, 4]:
        linear_layer: torch.nn.Linear = net.get_submodule(f"fc_layers.{param_net}.{offset}")
        batch_norm: torch.nn.BatchNorm1d = net.get_submodule(f"fc_layers.{param_net}.{offset+2}")

        lin_w, lin_b = linear_layer.weight, linear_layer.bias
        bn_w, bn_b = batch_norm.weight, batch_norm.bias
        for perc_idx in range(lin_w.shape[0]):
            # w, b = merge_weights_with_bn(lin_w[perc_idx], lin_b[perc_idx], bn_w[perc_idx], bn_b[perc_idx])
            w, b = lin_w[perc_idx].detach(), lin_b[perc_idx].detach()
            accelerator_perceptrons[perc_idx % ACCELERATOR_NUM_LANES].append(torch.concat((b.unsqueeze(dim=0),w)))
            params_arr.append(w.numpy())
            params_arr.append(b.numpy().reshape(1))

    encoder_layer: torch.nn.Linear = net.get_submodule(f"encoder.{param_net}.8")
    for i in range(ACCELERATOR_NUM_LANES):
        accelerator_perceptrons[i].append(torch.concat((encoder_layer.bias, encoder_layer.weight.squeeze())))

params_arr = np.concatenate(params_arr)

# Find the best quantization
print(f"Every perceptron ({ACCELERATOR_NUM_LANES} in total) requires memory {len(accelerator_perceptrons[0])} deep")
print(f"Parameter stats:\n\tCount = {len(params_arr)}\n\tMean  = {np.mean(params_arr)}\n\tMedian= {np.median(params_arr)}\n\tStdev = {np.std(params_arr)}\n")

with gzip.open(INPUT_SIGNALS_PATH) as fd:
    input_data = pickle.load(fd)

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

#     # Error from ground truth outputs
#     for gtp in input_data[1:]:
#         for row in gtp:
#             for val in row:
#                 err = we - float(FixedPoint(float(val), True, int_bits, TOTAL_BITS - int_bits))
#                 error += err * err
#         denom += gtp.shape[0] * gtp.shape[1]

#     error /= denom
#     rmse = torch.sqrt(error)

#     print(f"INT_BITS = {int_bits} , RMSE = {rmse}")

#     if rmse < best_rmse:
#         best_rmse = rmse
#         best_int_bits = int_bits
#     else:
#         break
best_int_bits = 3

# Output memory files for 32 perceptrons
for pi, pd in enumerate(accelerator_perceptrons):
    with open(f"{MEM_FILE_PATH}/perc_{pi}_params.mem", "w") as fd:
        fd.write(f"// INT_BITS = {best_int_bits}\n")
        for si, sd in enumerate(pd):
            pdata = [FixedPoint(val, True, best_int_bits, TOTAL_BITS - best_int_bits) for val in sd]

            if PAD_WITH_ZEROS:
                while len(pdata) < MEMORY_WIDTH:
                    pdata.append(FixedPoint(0, True, best_int_bits, TOTAL_BITS - best_int_bits))

            fd.write(" ".join(f"{elem:0{4}x}" for elem in reversed(pdata)))
            fd.write(f"    // bias = {pdata[0]:0{4}x}, w[0] = {pdata[1]:0{4}x}, w[{len(sd)-2}] = {pdata[-1]:0{4}x}")
            fd.write('\n')
