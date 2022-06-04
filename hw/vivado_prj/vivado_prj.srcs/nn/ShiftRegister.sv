`timescale 1ns/1ps
`include "types.sv"

module ShiftRegister #(integer WIDTH = 16, integer LENGTH = 8) (
    input  logic clk,
    input  logic rst,
    input  bit [WIDTH-1:0] din,
    output bit [WIDTH-1:0] dout
);
    genvar i;

    bit [WIDTH-1:0] shr [LENGTH];

    always @(posedge clk or posedge rst)
        if (rst) shr[0] <= 0; else shr[0] <= din;
    
    generate
        for (i = 1; i < LENGTH; i+=1) begin
            always @(posedge clk or posedge rst)
                if (rst) shr[i] <= 0; else shr[i] <= shr[i-1];
        end
    endgenerate

    assign dout = shr[LENGTH-1];

endmodule
