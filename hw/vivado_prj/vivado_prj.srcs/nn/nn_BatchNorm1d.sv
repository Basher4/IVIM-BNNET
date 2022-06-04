`timescale 1ns/1ps

module nn_BatchNorm1d #(FEATURES = 6) (
    input  wire               clk,
    input  bit  signed [15:0] data_in  [FEATURES],
    output bit  signed [15:0] data_out [FEATURES]
);

    // TODO: Actually implement the module.
    assign data_out = data_in;

endmodule