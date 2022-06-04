`timescale 1ns / 1ps
`include "types.sv"

module PEController #(integer SAMPLES = 32) (
    input logic clk,
    input logic rst
);
    // This was very much designed to not change.
    ingeter NUM_PU = PARALLELISM;
    localparam bit DATA_TAG_ILC = 1'b0;
    localparam bit DATA_TAG_OUT = 1'b1;

    // Wiring for processing units.
    logic           global_bypass_dropout;
    logic           global_bypass_relu;
    logic           global_din_vld;
    logic           global_dout_vld;
    logic           din_from_input;

    logic           bernoulli_sample_rd;
    bit [INPUT_DIM-1:0] bernoulli_sample;
    logic           bernoulli_sample_vld;
    logic           sampler_fifo_full;
    logic           sampler_fifo_empty;

    logic           bypass_dropout  [NUM_PU];
    logic           bypass_relu     [NUM_PU];
    bit [INPUT_DIM-1:0] dropout_mask [NUM_PU];
    int32           pu_bias         [NUM_PU];
    int8            pu_weights      [NUM_PU][INPUT_DIM];

    int8            pu_din          [NUM_PU][INPUT_DIM];
    logic           pu_din_vld      [NUM_PU];
    int8            pu_dout         [NUM_PU];
    logic           pu_dout_vld     [NUM_PU];

    logic           data_tag_in;
    logic           data_tag_out;

    // Input / Output signals.
    bit   [14 : 0]  input_data_addr = 0;
    bit   [ 8 : 0]  weights_rd_addr = 0;    // Synchrnoize weights and biases
    int8            input_data      [INPUT_DIM];
    int8            output_data     [NUM_PU];
    logic           output_data_we;

    logic           ilc_wr_enable;
    bit   [11 : 0]  ilc_wr_addr;
    bit  [255 : 0]  ilc_wr_data;
    logic           ilc_rd_enable;
    bit   [ 9 : 0]  ilc_rd_addr;
    bit [1023 : 0]  ilc_rd_data;
    int8            ilc_rd_data_arr [INPUT_DIM];


    /// -------------------------------------------------------------------------
    ///      Instantiate modules
    /// -------------------------------------------------------------------------
    BernoulliSampler #(.WIDTH(INPUT_DIM)) u_BernoulliSampler (
        .clk,
        .rst,
        // Data
        .fifo_rd_en (bernoulli_sample_rd),
        .fifo_out   (bernoulli_sample),
        // Ctrl signals
        .fifo_full  (sampler_fifo_full),
        .fifo_empty (sampler_fifo_empty),
        .fifo_valid (bernoulli_sample_vld)
    );

    // All PUs work together, if one is valid all will be valid. For now.
    assign global_dout_vld = pu_dout_vld[0];

    genvar i;
    generate
        for (i = 0; i < NUM_PU; i+=1) begin
            assign pu_din[i] = din_from_input ? input_data : ilc_rd_data_arr;
            assign pu_din_vld[i] = global_din_vld;
            assign bypass_dropout[i] = global_bypass_dropout;
            assign bypass_relu[i] = global_bypass_relu;
            assign dropout_mask[i] = bernoulli_sample;
            assign output_data[i] = pu_dout[i];

            PEProcessingUnit #(.IN_WIDTH(INPUT_DIM)) u_ProcUnit (
                .clk,
                .rst,

                .bypass_dropout(bypass_dropout[i]),
                .bypass_relu(bypass_relu[i]),

                .i_data_tag(data_tag_in),
                .o_data_tag(data_tag_out),

                .dropout_mask(dropout_mask[i]),
                .param_addr(weights_rd_addr),

                .din(pu_din[i]),
                .din_vld(pu_din_vld[i]),
                .dout(pu_dout[i]),
                .dout_vld(pu_dout_vld[i])
            );
        end
    endgenerate

    assign output_data_we = (data_tag_out == DATA_TAG_OUT);
    PEIoCoordinator u_IoCoordinator (
        .clk,
        .rst,
        .o_init_done(), // TODO: Do this.

        // Weights
        .i_weights_rd_addr(weights_rd_addr),
        .o_weights(neuron_weights),
        // Biases
        .i_biases_rd_addr(weights_rd_addr),
        .o_biases(neuron_biases),
        // Input data
        .i_input_data_rd_addr(input_data_addr),
        .o_input_data(input_data),
        // Output data
        .i_output_data(output_data),
        .i_output_data_we(output_data_we)
    );

    // Intermediate layer cache.
    assign ilc_wr_enable = (data_tag_out == DATA_TAG_ILC);
    assign {>>{ilc_wr_data}} = pu_dout;     // Map IL cache data in to output of PUs.
    assign {>>{ilc_rd_data_arr}} = ilc_rd_data;

    // TODO: This should've been just a FIFO.
    bram_ilcache_1024d bram_il_cache (
        .clka   (clk),              // input wire clka
        
        .ena    (1),                // input wire 
        .wea    (ilc_wr_enable),      // input wire [0 : 0] wea
        .addra  (ilc_wr_addr), // input wire [11 : 0] addra
        .dina   (ilc_wr_data), // input wire [255 : 0] dina
        
        .clkb   (clk),              // input wire clkb
        .enb    (ilc_rd_enable),      // input wire enb
        .addrb  (ilc_rd_addr), // input wire [9 : 0] addrb
        .doutb  (ilc_rd_data)  // output wire [1023 : 0] doutb
    );

    /// -------------------------------------------------------------------------
    ///      Control flow state machine
    /// -------------------------------------------------------------------------
    bit [8:0]   counter = 0;
    logic       l1_started_writing = 0;
    bit [8:0]   weights_rd_base_addr;

    enum logic [64:0] {S_INIT,
                       S_FISRT_LAYER_START,
                       S_FIRST_LAYER_EVAL,
                       S_FIRST_LAYER_WAIT_FOR_DONE,
                       S_SECOND_LAYER_EVAL,
                       S_THIRD_LAYER_START,
                       S_THIRD_LAYER_WAIT_FOR_DONE,
                       S_NEXT_VOXEL,
                       S_DONE,
                       S_ERROR } state;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= S_INIT;
        end else begin
            case (state)
                S_INIT: begin
                    input_data_addr <= 0;
                    weights_rd_addr <= 0;
                    output_data_we <= 0;
                    global_bypass_dropout <= 0;
                    global_bypass_relu <= 0;
                    weights_rd_base_addr <= 0;
                    data_tag_in <= 0;
                    
                    state <= S_FISRT_LAYER_START;
                end

                S_FISRT_LAYER_START: begin
                    data_tag_in <= DATA_TAG_ILC;
                    global_din_vld <= 1;
                    global_bypass_dropout <= 1;
                    din_from_input <= 1;    // Take input from image BRAM.

                    counter <= 0;
                    state <= S_FIRST_LAYER_EVAL;
                end

                S_FIRST_LAYER_EVAL: begin
                    if (counter == 16) begin
                        // ilc_wr_enable <= 1;     // When valid data starts pouring in, write it.
                        global_din_vld <= 0;    // Data in next cycle won't be valid.
                        counter <= 0;
                        state <= S_FIRST_LAYER_WAIT_FOR_DONE;
                    end else begin
                        weights_rd_addr <= weights_rd_addr + 1;
                        counter <= counter + 1;
                    end

                    assert (global_dout_vld == 0) else $error("Unexpected bahaviour - PU processed all data while evaluating first layer.");
                end

                S_FIRST_LAYER_WAIT_FOR_DONE: begin
                    if (global_dout_vld) begin
                        ilc_wr_addr <= ilc_wr_addr + 1;
                        l1_started_writing <= 1;
                    end else if (l1_started_writing) begin
                        // ilc_wr_enable <= 1;
                        l1_started_writing <= 0;
                        l2_iteration <= 0;

                        // Setup for next layer evaluation.
                        global_bypass_dropout <= 0;
                        bernoulli_sample_rd <= 1;
                        din_from_input <= 0;    // Take input from IL cache.
                        global_din_vld <= 1;
                        counter <= 0;
                        weights_rd_base_addr <= weights_rd_addr;
                        state <= S_SECOND_LAYER_EVAL;
                    end
                end

                S_SECOND_LAYER_EVAL: begin
                    if (counter[8:7] == 4) begin
                        // To evaluate the last layer we need to bypass ReLU unit and run it through sigmoid on the host computer.
                        bypass_relu <= 1;
                        counter <= 0;
                        data_tag_in <= DATA_TAG_OUT;
                        state <= S_THIRD_LAYER_START;
                    end else begin
                        // Every 4 cycles we start evaluating a new sample -> need a new dropout mask.
                        bernoulli_sample_rd <= (counter[1:0] == 3);
                        
                        // Every 4 cycles come back to the base address.
                        if (counter[1:0] == 3) begin
                            weights_rd_addr <= weights_rd_base_addr;
                        end else begin
                            weights_rd_addr <= weights_rd_addr + 1;
                        end

                        if (counter[6:0] == 7'hff) begin
                            // I evaluated SAMPLES sample, in the next cycle we need to have next input from cache.
                            weights_rd_base_addr <= weights_rd_base_addr + 4;
                            ilc_rd_addr <= ilc_rd_addr + 1;
                        end
                    end
                end

                S_THIRD_LAYER_START: begin
                    // We can start evaluating the last layer straight away.
                    // S_SECOND_LAYER_EVAL takes (4 params * 32 samples/param * 4 cycles/sample)  = 512 cycles.
                    if (global_dout_vld)
                        ilc_wr_addr <= ilc_wr_addr + 1;

                    counter <= coutner + 1;
                    if (coutner == 128) begin
                        counter <= 0;
                        global_din_vld <= 0;
                        state <= S_THIRD_LAYER_WAIT_FOR_DONE;
                    end else begin
                        ilc_rd_addr <= ilc_rd_addr;
                    end
                end

                S_THIRD_LAYER_WAIT_FOR_DONE: begin
                    if (global_dout_vld) begin
                        ilc_wr_addr <= ilc_wr_addr + 1;
                    end else begin
                        // Move on to next voxel
                        input_data_addr <= input_data_addr + 1; // TODO: Change this to next input signal.
                        state <= S_FISRT_LAYER_START;
                    end
                end

                S_ERROR: state <= S_INIT;
                default: begin
                    state <= S_ERROR;
                end
            endcase
        end
    end

endmodule
