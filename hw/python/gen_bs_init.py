from fixedpoint import FixedPoint
import numpy as np

fd = open('./mem_files/bern_sample_init_32x3.mem', 'w')

vals = np.random.randint(0, (2**64), (32, 3, 2), dtype=np.uint64)
fd.write("{\n")
for grp in vals:
    fd.write("{ ")
    fd.write(', '.join(f"128'h{lfsr[0]:0{16}x}{lfsr[1]:0{16}x}" for lfsr in grp))
    fd.write(" },\n")
fd.write("}\n")

fd.close()
