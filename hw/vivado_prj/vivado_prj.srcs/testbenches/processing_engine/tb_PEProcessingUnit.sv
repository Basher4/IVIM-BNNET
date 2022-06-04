`timescale 1ns / 1ps
`include "types.sv"

module tb_PEProcessingUnit;

    logic clk = 1;
    logic rst = 1;
    always #5 clk = ~clk;
    
    logic         pl_i_bypass_dropout;
    logic         pl_i_bypass_relu;
    perc_param_addr pl_i_param_idx;
    logic         pl_i_data_tag;
    logic         pl_o_data_tag;
    nndata        pl_i_data [INPUT_DIM];
    logic         pl_i_data_vld;
    nndata        pl_o_data;
    logic         pl_o_data_vld;
    bit [127 : 0] bs_o_dropout_mask;
        
    PEProcessingUnit #(.IN_WIDTH(128), .PARAM_FILE("perc_weights_bias.mem")) u_ProcessingLane (
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
        .dout(pl_o_data),
        .dout_vld(pl_o_data_vld)
    );
    
    // Test data.
    nndata test_din [4][128];
    nndata test_dout [4];
    // Load data
    initial begin
        $readmemh("perc_data_in.mem", test_din);
        $readmemh("perc_data_out.mem", test_dout);
        // $readmemh({`PROJECT_PATH, "roms/tb/perceptron/data_out.mem"}, nn_desired_out);
    end
    
    integer cycles_before_first_valid = 4;

    // Test routine.
    initial begin
        pl_i_param_idx = 3;
        #10 rst = ~rst;
        
        
        // Schedule first input.
        pl_i_bypass_dropout = 1;
        pl_i_bypass_relu = 0;
        pl_i_param_idx = 1;
        pl_i_data_tag = DT_TO_IL_CACHE;
        pl_i_data = test_din[0];
        pl_i_data_vld = 1;
        bs_o_dropout_mask = 128'hAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;
        #10;
        
        // Test that valid out works as expected. 
        pl_i_bypass_dropout = 0;
        pl_i_data_vld = 0;
        bs_o_dropout_mask = 128'h55555555555555555555555555555555;
        #10;
        
        // Schedule second input.
        pl_i_bypass_dropout = 0;
        pl_i_bypass_relu = 0;
        pl_i_param_idx = 2;
        pl_i_data_tag = DT_TO_IL_CACHE;
        pl_i_data = test_din[1];
        pl_i_data_vld = 1;
        bs_o_dropout_mask = 128'hAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;
        #10;
        
        // Schedule third input.
        pl_i_bypass_dropout = 0;
        pl_i_bypass_relu = 1;
        pl_i_param_idx = 3;
        pl_i_data_tag = DT_TO_OUTPUT;
        pl_i_data = test_din[2];
        pl_i_data_vld = 1;
        bs_o_dropout_mask = 128'h55555555555555555555555555555555;
        #10;
        pl_i_bypass_dropout = 1'dx;
        pl_i_bypass_relu = 1'dx;
        pl_i_param_idx = 17'dx;
        pl_i_data_tag = 1'dx;
        {>>{pl_i_data}} = 2048'dx;
        pl_i_data_vld = 1'dx;
        bs_o_dropout_mask = 128'dx;
        
        // Wait until data out is valid.
        while (pl_o_data_vld == 0) begin
            #10 cycles_before_first_valid += 1;
        end
        $display("It took %d cycles to see the first valid output.", cycles_before_first_valid);
        
        // Check that input parameters are as expected.
        assert (pl_o_data_tag == DT_TO_IL_CACHE) else $error("Invalid data tag associated with first batch");
        assert (pl_o_data == 0) else $error("Data in 1st batch is 0 - not correct");
        $display("Data from 1st batch = %f (%d)", fixed2real(pl_o_data), pl_o_data);
        #10;
        
        assert (pl_o_data_vld == 0) else $error("Data should be invalid in 2nd batch.");
        #10;
        
        assert (pl_o_data_vld == 1) else $error("Data should be valid in 3rd batch.");
        assert (pl_o_data_tag == DT_TO_IL_CACHE) else $error("Invalid data tag associated with 3rd batch.");
        assert (pl_o_data != 0) else $error("Data in 3rd batch is 0 - not correct");
        $display("Data from 3rd batch = %f (%d)", fixed2real(pl_o_data), pl_o_data);
        #10;
        
        assert (pl_o_data_vld == 1) else $error("Data should be valid in 3rd batch.");
        assert (pl_o_data_tag == DT_TO_OUTPUT) else $error("Invalid data tag associated with 3rd batch.");
        assert (pl_o_data != 0) else $error("Data in 4th batch is 0 - not correct");
        $display("Data from 4th batch = %f (%d)", fixed2real(pl_o_data), pl_o_data);
        #10;
        
        $display("All metadata checks passed. Data *SHOULD* be correct if Perceptron tests pass.");
        $display("...there should also be check for data but that doesn't quite work. So...");
        $finish;
    end

endmodule
