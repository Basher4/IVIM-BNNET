from fixedpoint import FixedPoint
import numpy as np
from config import INT_BITS, FRAC_BITS

TESTBENCH_ROM_PATH = "./roms/tb/linear"
LINEAR_WEIGHTS_ROM_PATH = f"{TESTBENCH_ROM_PATH}/weights.mem"
LINEAR_BIAS_ROM_PATH = f"{TESTBENCH_ROM_PATH}/bias.mem"
LINEAR_INPUT_ROM_PATH = f"{TESTBENCH_ROM_PATH}/data_in.mem"
LINEAR_RESULT_ROM_PATH = f"{TESTBENCH_ROM_PATH}/data_out.mem"

IN_FEATURES = 16
OUT_FEATURES = 3

rng = np.random.default_rng(1234)

def n2f(n): return FixedPoint(n, True, INT_BITS, FRAC_BITS, overflow="wrap", overflow_alert="warning")
def fparr(count): return np.array([n2f(x) for x in rng.random(count)])

def generate_linear_weights():
    data = fparr(IN_FEATURES * OUT_FEATURES).reshape(IN_FEATURES, OUT_FEATURES)
    
    rom = ""
    for idx, row in enumerate(data.T):
        rom += f"// Neuron {idx}\n"
        rom += "\n".join([f"{c:0{4}x}" for c in row])
        rom += "\n\n"
    
    with open(LINEAR_WEIGHTS_ROM_PATH, "w") as fd:
        fd.write(rom)

    return data

def lin2file(data, path):
    with open(path, "w") as fd:
        for c in data:
            c.resize(INT_BITS, FRAC_BITS)

        fd.write("\n".join(f"{c:0{4}x}" for c in data))
        fd.write("\n")

if __name__ == "__main__":
    weights = generate_linear_weights()
    bias = fparr(OUT_FEATURES)
    input = fparr(IN_FEATURES)
    result = weights.T @ input + bias

    # Dump to files
    lin2file(bias, LINEAR_BIAS_ROM_PATH)
    lin2file(input, LINEAR_INPUT_ROM_PATH)
    lin2file(result, LINEAR_RESULT_ROM_PATH)

    for r in weights:
        for c in r:
            print(float(c), end = " ")
        print()
    print()

    for r in input:
        print(float(r), end=" ")
    print()
    print()

    for r in bias:
        print(float(r), end=" ")
    print()
    print()

    for r in result:
        print(float(r), end=" ")
    print()
    print()