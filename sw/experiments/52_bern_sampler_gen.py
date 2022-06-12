import numpy as np

WIDTH = 128
N_SIPO = WIDTH

rnums = np.random.randint(0, np.iinfo(np.uint64).max, size=(N_SIPO, 3, 2), dtype=np.uint64)

with open(f"./mem_files/bern_sample_init_{N_SIPO}x3.txt", "w") as fd:
    fd.write("{\n")
    for r in rnums:
        fd.write("{ ")
        fd.write(", ".join([f"128'h{e[0]:0{16}x}{e[1]:0{16}x}" for e in r]))
        fd.write(" },\n")
    fd.write("}\n")
