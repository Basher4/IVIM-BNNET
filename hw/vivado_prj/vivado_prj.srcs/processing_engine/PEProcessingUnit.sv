`timescale 1ns / 1ps
`include "types.sv"

module PEProcessingUnit #(IN_WIDTH = 128, PARAM_FILE = "Invalid String") (
    input  logic  clk,
    input  logic  rst,

    input  logic  bypass_dropout,
    input  logic  bypass_relu,

    input  logic  i_data_tag,
    output logic  o_data_tag,

    input  bit [IN_WIDTH-1 : 0] dropout_mask,
    input  perc_param_addr      param_addr,

    input  nndata din [IN_WIDTH],
    input  logic  din_vld,
    output nndata dout,
    output logic  dout_vld
);
    genvar i;

    // Data flow wires.
    nndata dropout_dout [IN_WIDTH];
    logic  dropout_dout_vld;
    nndata perceptron_dout;
    logic  perceptron_dout_vld;
    nndata relu_dout;
    logic  relu_dout_vld;

    // Dropout pipeline registers
    // param_addr is not here. Latency of dropout layer is 1 cycle,
    // but it also takes 1 cycle to get output of BRAM. These two effects cancel out.
    nndata pp_drop_bias;
    logic  pp_drop_relu_bypass;
    bit    pp_drop_data_tag;
    // Perceptron pipeline registers
    logic  pp_perc_relu_bypass;
    logic  pp_perc_data_tag;

    // --------------------------------------------------------
    //          Dropout mask
    // --------------------------------------------------------
    nn_DropoutLayer #(.WIDTH(IN_WIDTH)) u_DropoutLayer (
        .clk,
        .rst,
        .bypass(bypass_dropout),
        .mask(dropout_mask),
        .din(din),
        .din_vld(din_vld),
        .dout(dropout_dout),
        .dout_vld(dropout_dout_vld),

        .i_pp_bypass_relu(bypass_relu),
        .o_pp_bypass_relu(pp_drop_relu_bypass),
        .i_pp_data_tag(i_data_tag),
        .o_pp_data_tag(pp_drop_data_tag)
    );

    // --------------------------------------------------------
    //          Perceptron
    // --------------------------------------------------------
    nn_Perceptron #(.FEATURES(IN_WIDTH), .PARAM_FILE(PARAM_FILE)) u_Perceptron (
        .clk,
        .rst,

        // This parameters determines the weights and biases for the perceptron.
        // It skips the first stage in pipeline because latency from submitting
        // and address to getting the output on wires is 1 clock cycle, which is
        // exactly the latency of `nn_DropoutLayer`.
        .param_addr(param_addr),

        .din(dropout_dout),
        .din_vld(dropout_dout_vld),
        .dout(perceptron_dout),
        .dout_vld(perceptron_dout_vld),

        .i_pp_bypass_relu(pp_drop_relu_bypass),
        .o_pp_bypass_relu(pp_perc_relu_bypass),
        .i_pp_data_tag(pp_drop_data_tag),
        .o_pp_data_tag(pp_perc_data_tag)
    );

    // Relu
    nn_ReLU u_Relu (
        .clk,
        .rst,
        .bypass(pp_perc_relu_bypass),

        .din(perceptron_dout),
        .din_vld(perceptron_dout_vld),
        .dout(relu_dout),
        .dout_vld(relu_dout_vld),

        .i_pp_data_tag(pp_perc_data_tag),
        .o_pp_data_tag(o_data_tag)
    );

    // Output
    assign dout = relu_dout;
    assign dout_vld = relu_dout_vld;

endmodule
