`timescale 1ns/1ps
`include "types.sv"

module nn_ReLU (
    input  logic    clk,
    input  logic    rst,
    input  logic    bypass,
    
    input  nndata   din,
    input  logic    din_vld,
    output nndata   dout,
    output logic    dout_vld,

    input  logic    i_pp_data_tag,
    output logic    o_pp_data_tag
);

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            dout <= 0;
        end else begin
            if (bypass)
                dout <= din;
            else
                dout <= nndata_int_part(din) < 0 ? 0 : din;
        end
    end
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            dout_vld <= 0;
            o_pp_data_tag <= 0;
        end else begin
            dout_vld <= din_vld;
            o_pp_data_tag <= i_pp_data_tag;
        end
    end

endmodule: nn_ReLU
