`timescale 1ns / 1ps

module tb_EvalSynthData_FullyParallel;

    localparam VOXELS_TO_EVALUATE = 4;
    localparam PARAMS_TO_EVALUATE = 4;
    localparam SAMPLES = 32;
    localparam NUM_LANES = 11;
    localparam string perc_param_file [NUM_LANES] = { "perc_0_params.mem", "perc_1_params.mem", "perc_2_params.mem",
                                                      "perc_3_params.mem", "perc_4_params.mem", "perc_5_params.mem",
                                                      "perc_6_params.mem", "perc_7_params.mem", "perc_8_params.mem",
                                                      "perc_9_params.mem", "perc_10_params.mem" };

    integer voxel_idx = 0;
    integer param_idx = 0;
    integer sample = 0;
    integer f;

    logic clk = 1;
    logic rst = 1;
    always #5 clk = ~clk;

    // Memories for input and output data.
    nndata test_din [VOXELS_TO_EVALUATE][128];
    nndata accelerator_out [VOXELS_TO_EVALUATE][PARAMS_TO_EVALUATE][SAMPLES];
    integer ao_vox_idx = 0, ao_param_idx = 0, ao_sample_idx = 0;

    // IL$ memory - 11 elements * 64 deep
    integer il_cache_addr = 0;
    nndata il_cache [64][128];

    // Bernoulli sampler control signals.
    logic         bs_i_read_next_sample = 0;
    bit [127 : 0] bs_o_dropout_mask;
    logic         bs_o_dropout_mask_vld;
    logic         bs_o_ctrl_is_full;
    logic         bs_o_ctrl_is_empty;

    // Lane control signals.
    logic         pl_i_bypass_dropout = 0;
    logic         pl_i_bypass_relu = 0;
    perc_param_addr pl_i_param_idx = 0;
    logic         pl_i_data_tag = 0;
    logic         pl_o_data_tag;
    nndata        pl_i_data [128];
    logic         pl_i_data_vld = 0;
    nndata        pl_o_data [NUM_LANES];
    logic         pl_o_data_vld_partial [NUM_LANES];
    logic         pl_o_data_vld_all;
    assign pl_o_data_vld_all = pl_o_data_vld_partial[0];

    initial begin
        $readmemh("din.mem", test_din);
    end
    
    // Instantiate Bernoulli Sampler
    BernoulliSampler #(.WIDTH(128), .DIV(1)) u_BernoulliSampler (
        .clk,
        .rst,
        .fifo_rd_en(bs_i_read_next_sample),
        .fifo_out(bs_o_dropout_mask),
        .fifo_full(bs_o_ctrl_is_full),
        .fifo_empty(bs_o_ctrl_is_empty),
        .fifo_valid(bs_o_dropout_mask_vld)
    );

    // Instantiate all 11 lanes to evaluate data.
    genvar i;
    generate
        for (i = 0; i < NUM_LANES; i += 1) begin : GEN_LANES
            PEProcessingUnit #(.IN_WIDTH(128), .PARAM_FILE(perc_param_file[i])) u_Lane (
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

    // Sanity check for simulation - make sure dropout mask is never empty if it's needed.
    always @(posedge clk) begin
        if (bs_o_ctrl_is_empty && $realtime > 100) begin
            $display("BernoulliSampler is empty at time %d (%t)! This is a functional simulation, shouldn't happen.", $realtime, $realtime);
            $stop;
        end
    end

    // Setup write handlers for IL$ and output struct.
    always @(posedge clk) begin
        if (pl_o_data_vld_all) begin
            if (pl_o_data_tag == DT_TO_IL_CACHE) begin
                il_cache[il_cache_addr][0:10] = pl_o_data;
                for (integer i = 11; i < 128; i += 1) il_cache[il_cache_addr][i] = 0;
                il_cache_addr += 1;
            end else begin
                assert (pl_o_data_tag == DT_TO_OUTPUT) else $stop;
                accelerator_out[ao_vox_idx][ao_param_idx][ao_sample_idx] = pl_o_data[0];
                ao_sample_idx += 1;

                if (ao_sample_idx == SAMPLES) begin
                    ao_param_idx += 1;
                    ao_sample_idx = 0;

                    if (ao_param_idx == PARAMS_TO_EVALUATE) begin
                        ao_vox_idx += 1;
                        ao_param_idx = 0;
                    end
                end
            end
        end
    end

    initial begin
        #10;
        rst = 0;

        /// Wait for BernoulliSampler to be full.
        while (!bs_o_ctrl_is_full) #10;

        for (voxel_idx = 0; voxel_idx < VOXELS_TO_EVALUATE; voxel_idx += 1) begin
            pl_i_param_idx = 0;

            for (param_idx = 0; param_idx < PARAMS_TO_EVALUATE; param_idx += 1) begin
                /// Evaluate the first layer.
                // Set up evaluation.
                pl_i_bypass_dropout = 1;
                pl_i_bypass_relu = 0;
                pl_i_data_tag = DT_TO_IL_CACHE;
                pl_i_data = test_din[voxel_idx];
                pl_i_data_vld = 1;
                #10;
                pl_i_data_vld = 0;

                // Wait for lanes to compute the result.
                // while (!pl_o_data_vld_all) #10;
                #200;
                // Write the result into IL$.
                #10;
                

                /// Evaluate the second layer.
                pl_i_param_idx += 1;
                bs_i_read_next_sample = 1;
                #10;
                for (sample = 0; sample < SAMPLES; sample += 1) begin
                    pl_i_bypass_dropout = 0;
                    pl_i_bypass_relu = 0;
                    pl_i_data_tag = DT_TO_IL_CACHE;
                    pl_i_data = il_cache[0];
                    pl_i_data_vld = 1;
                    #10;
                end
                assert (il_cache_addr > 0) else $error("No data hit the IL cache yet - must wait.");

                /// Evaluate encoder for all samples.
                pl_i_param_idx += 1;
                for (sample = 0; sample < SAMPLES; sample += 1) begin
                    pl_i_bypass_dropout = 0;
                    pl_i_bypass_relu = 1;
                    pl_i_data_tag = DT_TO_OUTPUT;
                    pl_i_data = il_cache[1 + sample];
                    pl_i_data_vld = 1;
                    #10;
                end
            end
        end
        pl_i_data_vld = 0;
        
        // Wait until all elements are written.
        while (ao_vox_idx < VOXELS_TO_EVALUATE) begin
            #10;
            if ($realtime > 30000) begin
                $error("Waiting too long for finish");
                $stop;
            end
        end
        
        // Print results.
        for (integer i = 0; i < VOXELS_TO_EVALUATE; i += 1) begin
            $display("Voxel %d: out0 = %x (%f), out1 = %x (%f), out2 = %x (%f), out3 = %x (%f)", i,
                accelerator_out[i][0][0], fixed2real(accelerator_out[i][0][0]),
                accelerator_out[i][1][0], fixed2real(accelerator_out[i][1][0]),
                accelerator_out[i][2][0], fixed2real(accelerator_out[i][2][0]),
                accelerator_out[i][3][0], fixed2real(accelerator_out[i][3][0]));
        end

        f = $fopen("output.txt","w");
        
        $display();
        $display("===== OUTPUT FOR FURTHER EVALUATION =====");
        $fwrite(f, "fully_parallel_out = [\n"); 
        for (integer v = 0; v < VOXELS_TO_EVALUATE; v += 1) begin
            $fwrite(f, "[");
            for (integer p = 0; p < PARAMS_TO_EVALUATE; p += 1) begin
                $fwrite("bit2fixed(");
                for (integer s = 0; s < SAMPLES; s += 1) begin
                    $fwrite("0x%x, ", accelerator_out[v][p][s]);                    
                end
                $fwrite("),\n");
            end
            $fwrite("],\n");
        end
        $fwrite("]\n");

        $fclose(f);
    
        $finish;
    end

endmodule