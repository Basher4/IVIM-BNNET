`timescale 1ns/1ps
`include "types.sv"

module nn_DropoutLayer #(WIDTH = 32) (
    input  logic  clk,
    input  logic  rst,
    input  logic  bypass,

    input  logic [WIDTH-1:0]   mask,
    input  nndata din [WIDTH],
    input  logic  din_vld,
    output nndata dout [WIDTH],
    output logic  dout_vld,

    // Pipeline registers.
    input  logic  i_pp_bypass_relu,
    output logic  o_pp_bypass_relu,
    input  nndata i_pp_bias,
    output nndata o_pp_bias,
    input  logic  i_pp_data_tag,
    output logic  o_pp_data_tag
);

    genvar i;
    generate
        for (i = 0; i < WIDTH; i++) begin
            always @(posedge clk) begin
                if (bypass)
                    dout[i] <= din[i];
                else
                    dout[i] <= mask[i] ? din[i] : 0; 
            end
        end
    endgenerate
    
    always @(posedge clk or posedge rst) begin
        if (rst)
            dout_vld <= 0;
        else
            dout_vld <= din_vld;
    end

    // Take care of pipeline registers.
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            o_pp_bypass_relu <= 0;
            o_pp_bias <= 0;
            o_pp_data_tag <= 0;
        end else begin
            o_pp_bypass_relu <= i_pp_bypass_relu;
            o_pp_bias <= i_pp_bias;
            o_pp_data_tag <= i_pp_data_tag;
        end
    end

endmodule