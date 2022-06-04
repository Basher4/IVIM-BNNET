`ifndef _TYPES_SV_
`define _TYPES_SV_

parameter PARALLELISM = 32;

parameter QM_BITS     = 3;
parameter QN_BITS     = 13;
parameter FP_SIZE     = QM_BITS + QN_BITS;   // Can't be more than 18 - DSPs don't support that.
parameter FP_MSB      = FP_SIZE - 1;
parameter FP_DBL_SIZE = FP_SIZE * 2;
parameter FP_DBP_MSB  = FP_DBL_SIZE - 1;
parameter INPUT_DIM   = 128;

parameter PERC_PARAM_ROM_SIZE = FP_SIZE * 129 /*128 weights + bias*/
                                        * 4 /*parameters*/
                                        * 3 /*layers*/
                                        * INPUT_DIM / PARALLELISM;
parameter PERC_PARAM_ADDR_WIDTH = $clog2(PERC_PARAM_ROM_SIZE);

typedef bit signed [ 7:0] int8;
typedef bit signed [15:0] int16;
typedef bit signed [31:0] int32;
typedef int16             nndata;
typedef int32             nndata_dbl;
typedef bit [PERC_PARAM_ADDR_WIDTH-1:0] perc_param_addr;

parameter bit DT_TO_OUTPUT = 1'b0;
parameter bit DT_TO_IL_CACHE = 1'b1;

bit [QM_BITS-1:0] CONST_QM_ZERO = {QM_BITS{1'b0}};
bit [QN_BITS-1:0] CONST_QN_ZERO = {QN_BITS{1'b0}};

function bit signed [QM_BITS-1 : 0] nndata_int_part(input nndata num);
    nndata_int_part = num[FP_MSB : QN_BITS];
endfunction

function bit signed [QN_BITS-1 : 0] nndata_frac_part(input nndata num);
    nndata_frac_part = num[QN_BITS-1 : 0];
endfunction

function bit signed [FP_SIZE-1 : 0] nndata_double_to_single(input nndata_dbl num);
    parameter MSB = FP_DBL_SIZE - QM_BITS - 1;
    parameter LSB = QN_BITS;
    nndata_double_to_single = {num[31] , num[MSB:LSB]};
endfunction

// Useful functions for testing.
function real fixed2real (nndata num);
    fixed2real = real'(num)/(2.0 ** QN_BITS);
endfunction

`endif // _TYPES_SV_
