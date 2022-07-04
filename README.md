# IVIM-BNNET
Repo for my master thesis

Python modules use a fixed point library https://pypi.org/project/fixedpoint/

# What is What
## SW
- `IVIMNET` contains python modules used by PyTorch implementation
- `data` contains in-vivo data available from the IVIM-NET paper
- `models` contains trained pytorch models
- `experiments` contains python files for experiments that do not happen in jupyter notebooks. The most useful ones are
  - `00_generate_signals` generates a set of synthetic DWI data for training and inference, with added gaussian noise
  - `01_train_network_batch` train BNNs on synthetic data
  - `50_quant_synth_data_for_parallel` quantizes torch model parameters and outputs `.mem` files which are used to initialize buffers in the accelerator
  - `51_...` is the same but for different number of processing lanes

## HW
### Python
Functional model of the accelerator written in python. It's super slow, could use some matlab.
### Vivado Prj
Vivado project of the accelerator. Contains the Verilog code and tesetbenches.

## Jupyter Notebooks
- `bnn_eval_synth` generates Figures 5-9. Figure 9 was manually assembled but puzzle pieces are generated here.
- `bnn_eval_synth_all` generates Figures 10 and 11.
- `bnn_eval_invivo` has base code for generating figure 18 and 19
- `untitled` generates figure 27 after accelerator output was simulated using python model

All other notebooks are just random miscelaneous stuff.
