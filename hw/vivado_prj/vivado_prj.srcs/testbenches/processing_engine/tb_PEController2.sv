`timescale 1ns / 1ps
`include "types.sv"

module tb_PEControllerV2;

    logic clk = 1;
    logic rst = 1;
    always #5 clk = ~clk;

endmodule
