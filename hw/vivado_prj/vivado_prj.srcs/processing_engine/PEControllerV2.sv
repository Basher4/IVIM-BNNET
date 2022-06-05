`timescale 1ns / 1ps
`include "types.sv"

module PEControllerV2 #(string PERC_PARAM_FILES [PARALLELISM]) (
    input logic clk,
    input logic rst
);
    genvar i;

    localparam integer SAMPLES = 32;

    logic         ctrl_i_data_from_input;

    logic         ioc_i_load_next_input;
    logic         ioc_i_write_output;
    nndata        ioc_i_output_data [PARALLELISM-1 : 0];
    nndata        ioc_o_input_data [INPUT_DIM-1 : 0];
    logic         ioc_o_init_done;
    logic         ioc_o_done;
    
    logic         ilc_i_we;
    bit [  7 : 0] ilc_i_wr_addr;
    bit [511 : 0] ilc_i_dina_flat;
    bit [  7 : 0] ilc_i_rd_addr;
    bit [2047: 0] ilc_o_doutb_flat;
    // Convenience features to transpose flattened wires into arrays.
    nndata        ilc_i_data [PARALLELISM-1 : 0];
    nndata        ilc_o_data [INPUT_DIM-1 : 0];
    assign {>>{ilc_i_dina_flat}} = ilc_i_data;
    assign {>>{ilc_o_data}} = ilc_o_doutb_flat;
    
    logic         bs_i_read_next_sample;
    bit [127 : 0] bs_o_dropout_mask;
    logic         bs_o_dropout_mask_vld;
    logic         bs_o_ctrl_is_full;
    logic         bs_o_ctrl_is_empty;
    
    logic         pl_i_bypass_dropout;
    logic         pl_i_bypass_relu;
    perc_param_addr pl_i_param_idx;
    logic         pl_i_data_tag;
    logic         pl_o_data_tag;
    nndata        pl_i_data [INPUT_DIM-1 : 0];
    logic         pl_i_data_vld;
    nndata        pl_o_data [PARALLELISM-1 : 0];
    logic         pl_o_data_vld_partial [PARALLELISM-1 : 0];
    logic         pl_o_data_vld_all;
    assign pl_o_data_vld_all = pl_o_data_vld_partial[0];
    // nb. Since all lanes are tied together, I can just look at 1st element instead of AND-ing all of them. 
    
    /// -------------------------------------------------------------------------
    ///      Control logic & (Un)flattening of values.
    /// -------------------------------------------------------------------------
    assign pl_i_data = ctrl_i_data_from_input ? ioc_o_input_data : ilc_o_data;
    
    /// -------------------------------------------------------------------------
    ///      Instantiate modules
    /// -------------------------------------------------------------------------
    // IO Coordinator.
    assign ioc_i_write_output = (pl_o_data_tag == DT_TO_OUTPUT) && pl_o_data_vld_all;
    PEIoCoordinator u_IOCoordinator (
        .clk,
        .rst,
        .o_init_done(ioc_o_init_done),
        .o_done(ioc_o_done),
    
        .i_load_next_input(ioc_i_load_next_input),
        .o_input_data(ioc_o_input_data),
        // All lanes compute the same data, connecting just idx 0 is fine.
        .i_output_data(ioc_i_output_data[0]),
        .i_output_data_we(ioc_i_write_output)
    );
    
    // Intermediate layer cache. Make it behave like a FIFO on writes.
    // FIFO did not allow me to have the necessary ratio for wire width :/
    assign ilc_i_we = (pl_o_data_tag == DT_TO_IL_CACHE) && pl_o_data_vld_all;
    assign ilc_i_data = pl_o_data;
    always @(posedge clk or posedge rst) begin
        if (rst)
            ilc_i_wr_addr <= 0;
        else
            ilc_i_wr_addr <= ilc_i_we ? ilc_i_wr_addr + 1 : ilc_i_wr_addr;
    end

    bram_ilcache_64d u_IntermediateLayerCache (
        .clka(clk),    // input wire clka
        .wea(ilc_i_we),      // input wire [0 : 0] wea
        .addra(ilc_i_wr_addr),  // input wire [7 : 0] addra
        .dina(ilc_i_dina_flat),    // input wire [511 : 0] dina
        .clkb(clk),    // input wire clkb
        .addrb(ilc_i_rd_addr),  // input wire [5 : 0] addrb
        .doutb(ilc_o_doutb_flat)  // output wire [2047 : 0] doutb
    );
    
    // Bernoulli sampler.
    BernoulliSampler #(.WIDTH(128)) u_BernoulliSampler (
        .clk,
        .rst,
        .fifo_rd_en(bs_i_read_next_sample),
        .fifo_out(bs_o_dropout_mask),
        .fifo_full(bs_o_ctrl_is_full),
        .fifo_empty(bs_o_ctrl_is_empty),
        .fifo_valid(bs_o_dropout_mask_vld)
    );
    
    // Processing lanes.
    generate
        for (i = 0; i < 32; i += 1) begin
            PEProcessingUnit #(.IN_WIDTH(128), .PARAM_FILE(PERC_PARAM_FILES[i])) u_ProcessingLane (
                .clk,
                .rst,
            
                .bypass_dropout(pl_i_bypass_dropout),
                .bypass_relu(pl_i_bypass_relu),
            
                .i_data_tag(pl_i_data_tag),
                .o_data_tag(pl_o_data_tag),
            
                .dropout_mask(bs_o_dropout_mask),
                .param_addr(pl_i_param_idx),
            
                .din(pl_i_data),
                .din_vld(pl_i_data_vld),
                .dout(pl_o_data[i]),
                .dout_vld(pl_o_data_vld_partial[i])
            );
        end
    endgenerate
    
    /// -------------------------------------------------------------------------
    ///      Controlling state machine.
    /// -------------------------------------------------------------------------
    bit [7:0] sample_iteration;
    bit [4:0] eval_iteration;
    perc_param_addr param_idx_checkpoint;

    enum logic [63:0] { S_INIT = 64'h0,
                        S_NET_EVAL_START = 64'h10,
                        S_FIRST_LAYER_EVAL = 64'h20,
                        S_FIRST_LAYER_AWAIT_DONE = 64'h30,
                        S_FIRST_LAYER_WAIT_FOR_DONE = 64'h40,
                        S_SECOND_LAYER_EVAL = 64'h50,
                        S_THIRD_LAYER_START = 64'h60,
                        S_THIRD_LAYER_WAIT_FOR_DONE = 64'h70,
                        S_NEXT_VOXEL = 64'h80,
                        S_DONE = 64'h90,
                        S_ERROR = ~64'h0 } state;
                       
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= S_INIT;
        end else begin case (state)
            // 
            S_INIT: begin
                // Put all signals to their default state.
                // IO Coordinator
                ioc_i_load_next_input <= 0;
                // Intermediate Layer Cache.
                ilc_i_wr_addr <= 0;
                ilc_i_rd_addr <= 0;
                // Bernoulli Sampler.
                bs_i_read_next_sample <= 0;
                // Processing lanes.
                pl_i_bypass_dropout <= 0;
                pl_i_bypass_relu <= 0;
                pl_i_param_idx <= 0;
                // TODO: Internal variables.
                sample_iteration <= 0;
                eval_iteration <= 0;
                param_idx_checkpoint <= 0;

                // Start loading the input in the next cycle.
                ioc_i_load_next_input <= ioc_o_init_done;
                // Start evaluating the model.
                state <= ioc_o_init_done ? S_NET_EVAL_START : S_INIT;
            end

            // Prepare processing lane to start computing data in the next state.
            // Input data is laoded from the IO Coordinator in this cycle.
            S_NET_EVAL_START: begin
                // Load new input only once.
                ioc_i_load_next_input <= 0;
                // Setup lanes to accept first input of layer 1.
                pl_i_bypass_dropout <= 1;
                pl_i_bypass_relu <= 0;
                // pl_i_param_idx <= 0;  --->  param_idx is set in the previous state.
                pl_i_data_tag <= DT_TO_IL_CACHE;
                pl_i_data_vld <= 1;
                ctrl_i_data_from_input <= 1;

                eval_iteration <= 1'b1;  // Optimisation for the next state - it will start with 2nd iteration value.
                state <= S_FIRST_LAYER_EVAL;
            end

            // Input data form IO coordinator arrived, evaluate 1st layer.
            // Layer must be evaluated in 4 cycles.
            S_FIRST_LAYER_EVAL: begin
                // Evaluate the next parart of the first layer.
                pl_i_data_vld <= ~eval_iteration[3]; // On 3rd iteration set data_vld = 0.
                pl_i_param_idx <= pl_i_param_idx + 1;

                eval_iteration <= { eval_iteration[3:0], 1'b1 };
                state <= eval_iteration[3] ? S_FIRST_LAYER_AWAIT_DONE : S_FIRST_LAYER_EVAL;
            end

            // Wait until the whole layer is evaluated.
            S_FIRST_LAYER_AWAIT_DONE: begin
                eval_iteration <= 2'b11;    // Optimisation for the next state - it will start with 2nd iteration value.

                if (pl_o_data_vld_all) begin
                    state <= S_FIRST_LAYER_WAIT_FOR_DONE;
                end else begin
                    state <= S_FIRST_LAYER_AWAIT_DONE;
                end
            end

            S_FIRST_LAYER_WAIT_FOR_DONE: begin
                assert (pl_o_data_vld_all == 1) else $error("STATE MACHINE ERROR - Waiting too long for first layer to finish");
                eval_iteration <= { eval_iteration[3:0], 1'b1 };

                if (eval_iteration[3]) begin
                    // In the next state we will start evaluating the 2nd layer.

                    // We will need a dropout mask.
                    bs_i_read_next_sample <= 1;
                    // Setup processing lanes.
                    pl_i_bypass_dropout <= 0;
                    pl_i_bypass_relu <= 0;
                    // pl_i_param_idx <= pl_i_param_idx -- it was updated in state S_FIRST_LAYER_EVAL.
                    pl_i_data_tag <= DT_TO_IL_CACHE;

                    // Internal state.
                    ctrl_i_data_from_input <= 0;    // Data coming from IL cache.
                    eval_iteration <= 1'b1;
                    param_idx_checkpoint <= pl_i_param_idx;
                    sample_iteration <= 0;

                    state <= S_SECOND_LAYER_EVAL;
                end else begin
                    state <= S_FIRST_LAYER_WAIT_FOR_DONE;
                end
            end

            S_SECOND_LAYER_EVAL: begin
                bs_i_read_next_sample <= 0;
                
                pl_i_param_idx <= pl_i_param_idx + 1;
                eval_iteration <= { eval_iteration[3:0], 1'b1 };

                if (eval_iteration[3]) begin
                    pl_i_param_idx <= param_idx_checkpoint;
                    bs_i_read_next_sample <= 1;
                    sample_iteration <= sample_iteration + 1;
                end
            end

            default: state <= S_INIT;
        endcase
        end
    end

endmodule
