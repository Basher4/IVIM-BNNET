from fixedpoint import FixedPoint


NUM_WIDTH = 16
NUM_INT_BITS = 3
NUM_FRAC_BITS = NUM_WIDTH - NUM_INT_BITS

OVERFLOW = "clamp"       # other option is clamp

CONST_FP_ZERO = FixedPoint(0, True, m=NUM_INT_BITS, n=NUM_FRAC_BITS, overflow=OVERFLOW)
