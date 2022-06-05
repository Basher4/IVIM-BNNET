`timescale 1ns / 1ps
`include "types.sv"

module PEIoCoordinator (
    input   logic        clk,
    input   logic        rst,
    output  logic        o_init_done,
    output  logic        o_done,

    // Input data
    input   logic        i_load_next_input, 
    output  nndata       o_input_data [INPUT_DIM],
    output  logic        o_input_data_vld,
    // Output data
    input   nndata       i_output_data,
    input   logic        i_output_data_we
);

    localparam integer VOXELS_TO_EVALUATE = 4;
    genvar i;

    bit [14 : 0] i_input_data_rd_addr = 0;

    /* ******************************************************** */
    /*                    INPUT DATA MEMORY                     */
    /* ******************************************************** */
    
    // Input data that holds 32k voxels. That should be enough to hold at least 1
    // Z-slice of data. I can do my evaluation on that. Worst case I initialize 1 block for every slice.

    bit [   8 : 0] input_rd_addr;
    bit [2047 : 0] input_data_flattened;
    
    bram_input_data_512d u_BramInData (
        .clka(clk),    // input wire clka
        .ena(1),      // input wire ena
        .addra(input_rd_addr + 1),  // input wire [8 : 0] addra
        .douta(input_data_flattened)  // output wire [2047 : 0] douta
    );
    
    always @(posedge clk or posedge rst) begin
        if (rst)
            input_rd_addr <= ~0;
        else begin
            if (i_load_next_input) begin
                input_rd_addr <= input_rd_addr + 1;
                {>>{o_input_data}} <= input_data_flattened;
            end
        end
    end

    /* ******************************************************** */
    /*                  OUTPUT SAMPLES MEMORY                   */
    /* ******************************************************** */
    // For evey voxel we compute 4 int8 numbers:  Dt, Fp, Dp, f0
    // Example model has 144*144*21 = 248832 voxels * 32b/voxel = ~8Mb -> 388 BRAM blocks.
    // We can affort that. If not, this is a good candidate to modify into URAM memory.

    bit [10 : 0] output_wr_addr = 0;
    
    bram_output_data_512d u_BramOutData (
        .clka(clk),    // input wire clka
        .ena(1),      // input wire ena
        .wea(i_output_data_we),      // input wire [0 : 0] wea
        .addra(output_wr_addr),  // input wire [10 : 0] addra
        .dina(i_output_data),    // input wire [15 : 0] dina
        .clkb(clk),    // input wire clkb
        .enb(1),      // input wire enb
        .addrb(),  // input wire [8 : 0] addrb
        .doutb()  // output wire [63 : 0] doutb
    );

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            output_wr_addr <= 0;
        end else begin
            output_wr_addr <= i_output_data_we ? output_wr_addr + 1 : output_wr_addr;
        end
    end


    /* ******************************************************** */
    /*                     STATE MANAGEMENT                     */
    /* ******************************************************** */
    // Redundant field but in the future this might need to stall in the beginning.
    // E.g. if we want to load data from RAM.
    assign o_init_done = 1;

    // When we evaluate `VOXELS_TO_EVALUATE` then indicate that the whole network was processed.
    always @(posedge clk or posedge rst) begin
        if (rst)
            o_done <= 0;
        else begin
            if (i_load_next_input)
                o_done <= input_rd_addr == (VOXELS_TO_EVALUATE - 1);
            else
                o_done <= 0;
        end
    end

endmodule
