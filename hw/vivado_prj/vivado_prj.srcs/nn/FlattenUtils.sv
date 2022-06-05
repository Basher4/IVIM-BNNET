`timescale 1ns / 1ps
`include "types.sv"

module Unflatten #(integer ELEM_SIZE, integer INPUT_WIDTH) (
    input  bit [INPUT_WIDTH-1 : 0] in,
    output bit [ELEM_SIZE-1   : 0] out [INPUT_WIDTH / ELEM_SIZE]
);
    genvar i;
    generate
        for (i = 0; i < INPUT_WIDTH / ELEM_SIZE; i += 1)
            assign out[i] = in[ELEM_SIZE*(i+1)-1 : ELEM_SIZE*i];
    endgenerate
endmodule

module Flatten #(integer ELEM_SIZE, integer ELEM_COUNT) (
    input  bit [ELEM_SIZE-1            : 0] in [ELEM_COUNT],
    output bit [ELEM_SIZE*ELEM_COUNT-1 : 0] out
);
    genvar i;
    generate
        for (i = 0; i < ELEM_COUNT; i += 1)
            assign out[ELEM_SIZE*(i+1)-1 : ELEM_SIZE*i] = in[i];
    endgenerate
endmodule
