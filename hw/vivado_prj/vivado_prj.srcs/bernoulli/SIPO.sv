`timescale 1ns/1ps

module SIPO #(IN_WIDTH = 32, OUT_WIDTH = 128) (
    input logic clk,
    input logic rst,
    
    input  bit   [ IN_WIDTH - 1:0] in,
    output bit   [OUT_WIDTH - 1:0] out,
    output logic                   out_vld
);

    localparam integer OUT_BITS = $clog2(OUT_WIDTH / IN_WIDTH);
    bit [OUT_BITS:0] counter;
    
    // Output valid flag.
    assign out_vld = (counter == (OUT_WIDTH / IN_WIDTH) - 1);
    
    // Count up until OUT_WIDTH.
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter <= 0;
        end else begin
            counter <= out_vld ? 0 : counter + 1;
        end
    end
    
    // Shift in input values on every clock cycle.
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            out <= 0;
        end else begin
            out <= { out[OUT_WIDTH - IN_WIDTH - 1:0], in };
        end
    end

endmodule
