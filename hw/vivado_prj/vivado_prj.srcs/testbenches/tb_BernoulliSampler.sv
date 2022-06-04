`timescale 1ns / 1ps

module tb_BernoulliSampler;

    logic clk;
    logic rst_n;
    
    logic fifo_rd_en;
    wire [127:0] fifo_out;
    wire fifo_full;
    wire fifo_empty;
    wire fifo_valid;

    BernoulliSampler uut (
        .clk,
        .rst_n,
        
        .fifo_rd_en,
        .fifo_out,
        .fifo_full,
        .fifo_empty,
        .fifo_valid
    );
    
    always #5 clk <= ~clk;
    
    initial begin
        clk = 1;
        rst_n = 0;
        fifo_rd_en = 0;

        // Wait 5 cycles for reset.        
        #50;
        rst_n = 1;
        // Fifo is empty in the beginning.
        assert (fifo_empty == 1) else $error("Fifo is not empty in the beginning");
        
        // Check if fifo is still empty after 3 cycles.
        #30;
        assert (fifo_empty == 1) else $error("Fifo is not empty after 3 cycles");
        
        // After 4 cycles from beginning fifo should contain 1 element.
        #10;
        // The empy flag should be deasserted at the end of the cycle - check on negedge.
        #5;
        assert (fifo_empty == 0) else $error("Fifo is empty after 4 cycles - should contain 1 element");        
        #5;
    end
    
    always @(posedge clk) begin
        if (!fifo_empty) begin
            fifo_rd_en <= ~fifo_rd_en;
        end
    end

endmodule
