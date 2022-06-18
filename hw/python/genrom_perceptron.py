from fixedpoint import FixedPoint
import numpy as np

from config import INT_BITS, FRAC_BITS
import utils

TESTBENCH_ROM_PATH = "./hw/vivado_prj/vivado_prj.srcs/testbenches/nn/perceptron"
PERC_PARAMS_PATH = f"{TESTBENCH_ROM_PATH}/perc_weights_bias.mem"
INPUT_ROM_PATH = f"{TESTBENCH_ROM_PATH}/perc_data_in.mem"
RESULT_ROM_PATH = f"{TESTBENCH_ROM_PATH}/perc_data_out.mem"

N_FEATURES = 128
ITERS = 4

rng = np.random.default_rng(1234)

def n2f(n): return FixedPoint(n, True, INT_BITS, FRAC_BITS, overflow="wrap", overflow_alert="warning")
def fparr(count): return np.array([n2f(x-0.5) for x in rng.random(count)])

def gen_roms():
    weights = fparr(N_FEATURES * ITERS).reshape((ITERS, N_FEATURES))
    data_in = fparr(N_FEATURES * ITERS).reshape((ITERS, N_FEATURES))
    bias = fparr(ITERS)
    results: list[FixedPoint] = np.array([w@d + b for w,d,b in zip(weights, data_in, bias)])

    for result in results:
        print(hex(result), float(result))
        print(result.qformat)
        result.trim(True, True)
        print("After trim:", hex(result), float(result))
        print(result.qformat)

        result.resize(INT_BITS, FRAC_BITS, overflow="clamp", alert="warning")
        print(hex(result), float(result))
        print(result.qformat)
        print()

    perc_params = np.insert(weights, 0, bias, axis=1)
    utils.write_romfile(perc_params, PERC_PARAMS_PATH)

    data_in = data_in.flatten()
    data_in = np.expand_dims(data_in, axis=1)
    utils.write_romfile(data_in, INPUT_ROM_PATH)

    utils.write_romfile(results, RESULT_ROM_PATH)

if __name__ == "__main__":
    gen_roms()
