`timescale 1ns / 1ps

module tb_BernoulliSampler;

    logic clk = 1;
    logic rst = 1;
    
    logic fifo_rd_en = 0;
    wire [127:0] fifo_out;
    wire fifo_full;
    wire fifo_empty;
    wire fifo_valid;

    BernoulliSampler uut (
        .clk,
        .rst,
        
        .fifo_rd_en,
        .fifo_out,
        .fifo_full,
        .fifo_empty,
        .fifo_valid
    );
    
    always #5 clk <= ~clk;
    
    initial begin
        #10;
        rst = 0;

        // Fifo is empty in the beginning.
        assert (fifo_empty == 1) else $error("Fifo is not empty in the beginning");
        
        // Check if fifo is still empty after 3 cycles.
        #30;
        assert (fifo_empty == 1) else $error("Fifo is not empty after 3 cycles");
        
        // On 4th cycles a value is written into the fifo and should be now visible.
        #15;
        // The empy flag should be deasserted at the end of the cycle - check on negedge.
        #5 assert (fifo_empty == 0) else $error("Fifo is empty after 4 cycles - should contain 1 element");

        // Wait to get more values in the fifo (also to separate experiments in waveform).
        #100;

        // Read value and check that it is latched after read.
        fifo_rd_en = 1;
        assert (fifo_out != 0) else $error("Fifo should not be empty now");
        #10;
        
        fifo_rd_en = 0;
        #20;
        assert (fifo_out != 0) else $error("Fifo out is empty if not read");
        
        #100;
        
        // Check if I can get new data out of full fifo every cycle
        fifo_rd_en = 1;
        #140;

        $finish;        
    end

endmodule
