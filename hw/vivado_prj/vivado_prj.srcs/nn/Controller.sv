`timescale 1ns / 1ps
`include "types.sv"

module Controller (
    input wire clk,
    input wire rst_n    
);
    localparam integer PARALLELISM = 32;
    localparam integer LAYERS_BEFORE_SAMPLING = 32;
    localparam integer SAMPLES = 32;
    genvar i, j;

    // Dropout mask control
    logic dropout_mask_read     = 0;
    logic dropout_mask_enable   = 0;
    wire  dropout_mask_valid;
    wire  sampler_fifo_full;
    wire  sampler_fifo_empty;
    wire [PARALLELISM-1 : 0] dropout_mask;
    
    // Wiring up neural network engine stages.
    int8_w  data_in_dropout [INPUT_DIM];
    int8_w  data_in_linear  [INPUT_DIM];
    int8_w  data_in_relu    [INPUT_DIM];
    logic   data_in_dropout_vld = 0;
    wire    data_in_linear_vld;
    wire    data_in_relu_vld;

    int8_w  data_out        [PARALLELISM];
    wire    data_out_vld;

    bit     relu_bypass = 0;

    // Weights BRAM control.
    int8_w    pu_weights [PARALLELISM][INPUT_DIM];
    bit [6:0] pu_weight_rom_addr = 0;   // All perceptrons move at the same pace, they can share weight address.

    // Bias BRAM control.
    wire [BIAS_WIDTH*8-1 : 0] pu_biases_glue;
    int32_w                   pu_biases          [PARALLELISM][INPUT_DIM];    
    bit  [8 : 0]              pu_biases_rom_addr = 0;
    
    // Intermediate layer caching BRAM.
    logic            il_cache_we      = 0;
    logic            il_cache_re      = 0;
    bit   [   9 : 0] il_cache_wr_addr = 0;
    bit   [  11 : 0] il_cache_rd_addr = 0;
    bit   [ 255 : 0] il_cache_wr_data;
    bit   [1023 : 0] il_cache_rd_data;

    // Input data BRAM.
    logic            sample_bram_re   = 0;
    logic            sample_bram_we   = 0;
    bit   [  14 : 0] sample_bram_addr = 0;
    wire  [1023 : 0] sample_bram_dout_flat;
    int8_w           sample_bram_dout [INPUT_DIM];
    
    /* ******************************************************** */
    /*                      WEIGHT MEMORY                       */
    /* ******************************************************** */
    
    // In total this block uses 14.5*PARALLELISM 36Kb BRAM blocks.
    // When PARALLELISM = 32 -> consumes 464 BRAM blocks.
    generate
        for (i = 0; i < PARALLELISM; i += 1) begin
            integer _FLATTEN_MSB = 128 * 8 - 1;
            wire [_FLATTEN_MSB : 0] bram_dout;
            
            // Un-flatten BRAM output into a 2D array of weights.
            for (j = 0; j < INPUT_DIM; j += 1) begin
                integer MSB = (j + 1) * DATA_WIDTH - 1;
                integer LSB = j * DATA_WIDTH;
                assign pu_weights[i][j] = bram_dout[MSB:LSB];
            end 
            
            // ROM to store weights for a single perceptron.
            bram_128x8w_512d bram_perceptron_weights (
                .clka   (clk),
                .ena    (1),                    // always enabled
                .wea    (0),                    // never write, essentially a ROM
                .addra  (pu_weight_rom_addr),   // input wire [6 : 0] addra
                .dina   (),                     // never write
                .douta  (bram_dout)             // glue
            );
        end
    endgenerate
    
    /* ******************************************************** */
    /*                       BIAS MEMORY                        */
    /* ******************************************************** */
    
    bram_128x32w_512d bram_biases (
        .clka   (clk),
        .ena    (1),
        .wea    (0),
        .addra  (pu_biases_rom_addr),
        .dina   (),    // Don't write biases, that's written during synthesis / simulation.
        .douta  (pu_biases_glue)  // A thick wire on whick we do a transformation into an array below.
    );
    
    // Glue for rewiring flattened vector into an array.
    generate
        for (j = 0; j < INPUT_DIM; j += 1) begin
            integer MSB = (j + 1) * BIAS_WIDTH - 1;
            integer LSB = j * BIAS_WIDTH;
            assign pu_biases[j] = pu_biases_glue[MSB:LSB];
        end
    endgenerate
    
    /* ******************************************************** */
    /*                INTERMEDIATE LAYER CACHING                */
    /* ******************************************************** */
    
    // BRAM with write port A - width  32*8 =  256
    //        and read port B - width 128*8 = 1024
    // Can cache 1024 intermediate layers (128*8bits).
    // Good candidate to transform into URAM if needed.
    bram_ilcache_1024d bram_il_cache (
        .clka   (clk),              // input wire clka
        
        .ena    (1),                // input wire 
        .wea    (il_cache_we),      // input wire [0 : 0] wea
        .addra  (il_cache_wr_addr), // input wire [11 : 0] addra
        .dina   (il_cache_wr_data), // input wire [255 : 0] dina
        
        .clkb   (clk),              // input wire clkb
        .enb    (il_cache_re),      // input wire enb
        .addrb  (il_cache_rd_addr), // input wire [9 : 0] addrb
        .doutb  (il_cache_rd_data)  // output wire [1023 : 0] doutb
    );

    // Flatten output 
    generate
        for (j = 0; j < INPUT_DIM; j += 1) begin
            integer MSB = (j + 1) * BIAS_WIDTH - 1;
            integer LSB = j * BIAS_WIDTH;
            assign il_cache_wr_data[MSB:LSB] = data_out[j];
        end
    endgenerate
    
    /* ******************************************************** */
    /*                    INPUT DATA MEMORY                     */
    /* ******************************************************** */
    
    // Input data that holds 32k voxels. That should be enough to hold at least 1
    // Z-slice of data. I can do my evaluation on that. Worst case I initialize 1 block for every slice.

    bram_32k_voxels bram_input_data (
        .clka(clk),    // input wire clka
        .ena(sample_bram_re),      // input wire ena
        .wea(sample_bram_we),      // input wire [0 : 0] wea
        .addra(sample_bram_addr),  // input wire [14 : 0] addra
        .dina(),                  // input wire [1023 : 0] dina
        .douta(sample_bram_dout_flat)  // output wire [1023 : 0] douta
    );

    // Glue for rewiring flattened vector into an array.
    generate
        for (j = 0; j < INPUT_DIM; j += 1) begin
            integer MSB = (j + 1) * DATA_WIDTH - 1;
            integer LSB = j * DATA_WIDTH;
            assign sample_bram_dout[j] = sample_bram_dout_flat[MSB:LSB];
        end
    endgenerate

    /* ******************************************************** */
    /*                  OUTPUT SAMPLES MEMORY                   */
    /* ******************************************************** */
    // For evey voxel we compute 4 int8 numbers:  Dt, Fp, Dp, f0
    // Example model has 144*144*21 = 248832 voxels * 32b/voxel = ~8Mb -> 388 BRAM blocks.
    // We can affort that. If not, this is a good candidate to modify into URAM memory.


    /* ******************************************************** */
    /*                     PIPELINE STAGES                      */
    /* ******************************************************** */
    
    BernoulliSampler #(
        .WIDTH(PARALLELISM)
    ) bern_sampler (
        .clk,
        .rst_n,
        // Data
        .fifo_rd_en (dropout_mask_read),
        .fifo_out   (dropout_mask),
        // Ctrl signals
        .fifo_full  (sampler_fifo_full),
        .fifo_empty (sampler_fifo_empty),
        .fifo_valid (dropout_mask_valid)
    );
    
    nn_DropoutLayer #(
        .WIDTH(PARALLELISM)
    ) dropout_unit (
        .clk,
        .rst_n,
        .mask_enable(dropout_mask_enable),
        .din        (data_in_dropout),
        .din_vld    (data_in_dropout_vld),
        .mask       (dropout_mask),
        .dout       (data_in_linear),
        .dout_vld   (data_in_linear_vld)
    );
    
    nn_Linear #(
        .IN_DIM(INPUT_DIM),
        .OUT_DIM(PARALLELISM)
    ) linear_layer (
        .clk,
        .rst_n,
        
        .weights    (pu_weights),
        .bias       (pu_biases),
        
        .din        (data_in_linear),
        .din_vld    (data_in_linear_vld),
        .dout       (data_in_relu),
        .dout_vld   (data_in_relu_vld)
    );
    
    nn_ReLU #(
        .FEATURES(PARALLELISM)
    ) activation_fn (
        .clk,
        .rst_n,
        .bypass     (relu_bypass),
        .din        (data_in_relu),
        .din_vld    (data_in_relu_vld),
        .dout       (data_out),
        .dout_vld   (data_out_vld)
    );

    /* ******************************************************** */
    /*                CONTROL FLOW STATE MACHINE                */
    /* ******************************************************** */
    // I am assuming that all BRAM blocks are loaded with correct data.
    // After I write address into BRAM the next clock cycle I will perform the action.
    
    bit [$clog2(LAYERS_BEFORE_SAMPLING*4):0] first_layer_delay = 0;
    bit [$clor2(SAMPLES):0] samples_generated = 0;

    enum logic {S_INIT,
                S_FISRT_LAYER_START,
                S_FIRST_LAYER_EVAL,
                S_FIRST_LAYER_WAIT_FOR_DONE,
                S_FIRST_LAYER_WAIT_FOR_DONE_ADD,
                S_SECOND_LAYER_START,
                S_SECOND_LAYER_GENERATE_SAMPLES,
                S_THIRD_LAYER_FOLD_SAMPLES_START,
                S_NEXT_VOXEL,
                S_DONE,
                S_ERROR } state;
    
    /*  1. Initialize - set addresses to 0 and asserts to false. Always transition to next state.
        2. Load input data and weights for first voxel.
                Dropout Enable = False
                Select Bias Address & assert valid
                Select Weight Address & assert valid
                Select Data Address & assert valid
        
        2.
    */

    // 1. Evaluate the first fully connected layer for the first N voxels.
    //    That gives me N*4 values in the IL cache and requires N*16 cycles.
    // 2. 

    // State transition table.
    always @(posedge clk or negedge rst_n) begin
        if (rst_n == 0) begin
            state <= S_INIT;
        end else begin
            case (state)
                S_INIT: begin
                    dropout_mask_read   <= 0;
                    dropout_mask_enable <= 0;
                    data_in_dropout_vld <= 0;
                    pu_weight_rom_addr  <= 0;
                    pu_biases_rom_addr  <= 0;
                    il_cache_we         <= 0;
                    il_cache_re         <= 0;
                    il_cache_wr_addr    <= 0;
                    il_cache_rd_addr    <= 0;
                    sample_bram_re      <= 0;
                    sample_bram_we      <= 0;
                    sample_bram_addr    <= 0;

                    state <= S_FISRT_LAYER_START;
                end

                S_FISRT_LAYER_START: begin
                    sample_bram_re <= 1;    // Address of input data is set in previous state. Now load it from BRAM.

                    // Weights and biases are already set - BRAM blocks are always outputting a value.

                    data_in_dropout_vld <= 1;   // Data coming into dropout unit is valid.
                    dropout_mask_enable <= 0;   // Bypass dropout.

                    state <= S_FIRST_LAYER_EVAL;
                end

                S_FIRST_LAYER_EVAL: begin
                    // Data keeps flowing through the graph, make sure that on the next cycle
                    // correct data is read for weights and biases. Data stays the same.
                    pu_weight_rom_addr <= pu_weight_rom_addr + 1;
                    pu_biases_rom_addr <= pu_biases_rom_addr + 1;

                    // After 4 cycles we evaluated a layer. Stop feeding it new data
                    // and move on to the next state.
                    if (first_layer_delay[3]) begin
                        first_layer_delay <= 0;
                        sample_bram_re <= 0;
                        data_in_dropout_vld <= 0;   // Data coming into the processing elements is no longer valid.

                        state <= S_FIRST_LAYER_WAIT_FOR_DONE;
                    end else begin
                        first_layer_delay <= {first_layer_delay[2:0], 1};
                    end

                    assert (data_out_vld == 0) else $error("data_out_vld is HIGH before the first data had chance to be evaluated.");
                end

                S_FIRST_LAYER_WAIT_FOR_DONE: begin
                    // Wait until we processed the whole layer.
                    if (data_out_vld) begin
                        il_cache_wr_data <= data_out;
                        il_cache_we <= 1;
                        state <= S_FIRST_LAYER_WAIT_FOR_DONE_ADD;
                    end
                end

                S_FIRST_LAYER_WAIT_FOR_DONE_ADD: begin
                    if (data_out_vld) begin
                        il_cache_wr_addr <= il_cache_wr_addr + 1;
                        il_cache_wr_data <= data_out;
                    end else begin
                        state <= S_SECOND_LAYER_START;
                        il_cache_we <= 0;
                    end
                end

                S_SECOND_LAYER_START: begin
                    // We need to have at least a sample in sampler fifo for this to be working.
                    if (!sampler_fifo_empty) begin
                        // Data comes from the intermediate layer cache.
                        il_cache_re <= 1;
                        data_in_dropout_vld <= 0;
                        
                        // Bernoulli sampler must be on.
                        dropout_mask_read <= 1;
                        dropout_mask_enable <= 1;

                        // This time we want to generate 64 samples from the same input, so no need to change the address for itnermediate layer cache.
                        state <= S_SECOND_LAYER_GENERATE_SAMPLES;
                    end
                end

                S_SECOND_LAYER_GENERATE_SAMPLES: begin
                    if (samples_generated < SAMPLES) begin
                        if (!sampler_fifo_empty) begin
                            data_in_dropout_vld <= 1;
                            samples_generated <= samples_generated + 1;
                        end else begin
                            // If fifo is empty then data coming into dropout unit is not valid.
                            // We must set this flag to propagate the information.
                            data_in_dropout_vld <= 0;
                        end
                    end else begin
                        state <= S_THIRD_LAYER_FOLD_SAMPLES_START;
                        samples_generated <= 0;
                    end
                end

                default: state <= S_ERROR;
            endcase
        end
    end
    
endmodule
