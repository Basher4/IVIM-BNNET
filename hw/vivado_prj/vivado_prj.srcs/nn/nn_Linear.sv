`timescale 1ns/1ps
`include "types.sv"

module nn_Linear #(IN_FEATURES = 16, OUT_FEATURES = 16) (
    input  wire      clk,
    input  wire      rst_n,

    input  nn_data_t weight_mat [OUT_FEATURES][IN_FEATURES],
    input  nn_data_t bias_vec   [OUT_FEATURES],

    input  nn_data_t din        [IN_FEATURES],
    input  logic     din_vld,
    output nn_data_t dout       [OUT_FEATURES],
    output logic     dout_vld
);

    wire [0:OUT_FEATURES-1] valid_aggregate;
    assign valid = &valid_aggregate;

    genvar i;
    generate
        for (i = 0; i < OUT_FEATURES; i++) begin: PERCEPTRONS
            nn_Perceptron #(
                .FEATURES(IN_FEATURES)
            ) prec (
                .clk(clk),
                .rst_n(rst_n),
                
                .weights(weight_mat[i]),
                .bias(bias_vec[i]),
                
                .din(din),
                .din_vld(din_vld),
                
                .dout(dout[i]),
                .dout_vld(valid_aggregate[i])
            );
        end
    endgenerate

endmodule: nn_Linear
