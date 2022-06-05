`timescale 1ns / 1ps
`include "types.sv"

module tb_PEControllerV2;

    logic clk = 1;
    logic rst = 1;
    always #5 clk = ~clk;

    localparam string PERC_PARAM_FILES [PARALLELISM] = {
        "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem",
        "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem",
        "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem",
        "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem",
        "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem",
        "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem",
        "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem",
        "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem", "perc_weights_bias.mem"
    };

    PEControllerV2 #(.PERC_PARAM_FILES(PERC_PARAM_FILES)) UUT (
        .clk,
        .rst
    );
    
    initial begin
        #10;
        rst = 0;
        
        #390;
        
        $finish;
    end

endmodule
