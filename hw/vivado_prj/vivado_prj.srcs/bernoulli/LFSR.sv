`timescale 1ns/1ps

module LFSR #(RESET_VALUE = 0) (
    input logic clk,
    input logic rst,
    
    output bit out
);

    initial begin
        assert (RESET_VALUE != 0) else $error("Things don't work when seed is 0. Use random initial value!");
    end

    // Internal LFSR.
    bit lfsr_in;
    bit [127:0] lfsr;

    // Output
    assign out = lfsr[127];

    // LFSR working    
    assign lfsr_in = lfsr[120] ^ lfsr[125] ^ lfsr[126] ^ lfsr[127];
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            lfsr <= RESET_VALUE;
        end else begin
            lfsr <= { lfsr[126:0], lfsr_in };
        end
    end

endmodule
