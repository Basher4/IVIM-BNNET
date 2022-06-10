`timescale 1ns/1ps
`include "bs_init.sv"

module BernoulliSampler #(WIDTH = 128, DIV = 4) (
    input logic clk,
    input logic rst,
    
    input logic fifo_rd_en,
    output bit [WIDTH-1:0] fifo_out,
    output logic fifo_full,
    output logic fifo_empty,
    output logic fifo_valid
);

    localparam integer SIPO_BITS = WIDTH / DIV;   // Generate a sample every clock cycle.
                                            // Must do that to match consumption rate once pipeline gets filled up.
                                            // Otherwise we need to wait a few cycles between voxels to refill the sampler.                                            

    initial begin
        assert (WIDTH <= 128) else $error("WIDTH must be less than internal fifo width.");
    end
    
    bit [SIPO_BITS-1:0] sipo_in;
    bit [WIDTH-1:0]     sipo_out;
    logic               sipo_out_vld;
    
    genvar i;
    generate
        for (i = 0; i < SIPO_BITS; i++) begin
            // LFSR to sample random bernoulli variables. Each has p=0.5.
            bit [2:0] lfsr_out;
            LFSR #(.RESET_VALUE(bs_init[i][0])) lfsr1 (.clk, .rst, .out(lfsr_out[0]));
            LFSR #(.RESET_VALUE(bs_init[i][1])) lfsr2 (.clk, .rst, .out(lfsr_out[1]));
            LFSR #(.RESET_VALUE(bs_init[i][2])) lfsr3 (.clk, .rst, .out(lfsr_out[2]));

            assign sipo_in[i] = &lfsr_out; // Make p=0.125
        end
    endgenerate
    
    generate
        if (SIPO_BITS < WIDTH)
            SIPO #(.IN_WIDTH(SIPO_BITS),
                   .OUT_WIDTH(WIDTH))
                sipo (
                   .clk,
                   .rst,
                   .in(sipo_in),
                   .out(sipo_out),
                   .out_vld(sipo_out_vld)
            );
        else begin
            assign sipo_out = sipo_in;
            assign sipo_out_vld = 1;
        end
    endgenerate
    
    fifo_128w_512d samples_fifo (
        .clk(clk),                  // input wire clk
        .srst(rst),                 // input wire srst
        
        .din(sipo_out),             // input wire [127 : 0] din
        .wr_en(sipo_out_vld),       // input wire wr_en
        .rd_en(fifo_rd_en),         // input wire rd_en
        .dout(fifo_out),            // output wire [127 : 0] dout
        .full(fifo_full),           // output wire full
        .empty(fifo_empty),         // output wire empty
        .valid(fifo_valid),         // output wire valid
        
        // TODO: I should probably do something with these signals.
        .wr_rst_busy(),  // output wire wr_rst_busy
        .rd_rst_busy()   // output wire rd_rst_busy
    );

endmodule
