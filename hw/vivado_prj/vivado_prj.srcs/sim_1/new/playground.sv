`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 05/25/2022 03:24:33 PM
// Design Name: 
// Module Name: playground
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////
`include "types.sv"

module playground;

    parameter int FEATURES = 128;

    logic clk = 0, rst = 1;
    always #5 clk = ~clk;

    bit [129*FP_SIZE-1:0] rom_out;
    perc_param_addr param_addr = 0;

    xpm_memory_sprom #(
        .ADDR_WIDTH_A(PERC_PARAM_ADDR_WIDTH),              // DECIMAL
        .AUTO_SLEEP_TIME(1'b0),           // DECIMAL
        .CASCADE_HEIGHT(1'b0),            // DECIMAL
        .ECC_MODE("no_ecc"),           // String
        .MEMORY_INIT_FILE("perc_weights_bias.mem"), // String
        .MEMORY_INIT_PARAM("0"),       // String
        .MEMORY_OPTIMIZATION("true"),  // String
        .MEMORY_PRIMITIVE("block"),    // String
        .MEMORY_SIZE(PERC_PARAM_ROM_SIZE), // DECIMAL
        .MESSAGE_CONTROL(1'b0),           // DECIMAL
        .READ_DATA_WIDTH_A(FP_SIZE * (FEATURES + 1)), // DECIMAL
        .READ_LATENCY_A(1'b1),            // DECIMAL
        .READ_RESET_VALUE_A("0"),      // String
        .RST_MODE_A("SYNC"),           // String
        .SIM_ASSERT_CHK(1'b0),            // DECIMAL; 0=disable simulation messages, 1=enable simulation messages
        .USE_MEM_INIT(1'b1),              // DECIMAL
        .USE_MEM_INIT_MMI(1'b0),          // DECIMAL
        .WAKEUP_TIME("disable_sleep")  // String
    )
    rom_weights_bias (
        .dbiterra(),             // 1-bit output: Leave open.
        .douta(rom_out),                   // READ_DATA_WIDTH_A-bit output: Data output for port A read operations.
        .sbiterra(),             // 1-bit output: Leave open.
        .addra(param_addr),              // ADDR_WIDTH_A-bit input: Address for port A read operations.
        .clka(clk),                     // 1-bit input: Clock signal for port A.
        .ena(1'b1),                       // 1-bit input: Memory enable signal for port A. Must be high on clock
                                         // cycles when read operations are initiated. Pipelined internally.

        .injectdbiterra(1'b0), // 1-bit input: Do not change from the provided value.
        .injectsbiterra(1'b0), // 1-bit input: Do not change from the provided value.
        .regcea(1'b1),                 // 1-bit input: Do not change from the provided value.
        .rsta(rst),                     // 1-bit input: Reset signal for the final port A output register stage.
                                        // Synchronously resets output port douta to the value specified by
                                        // parameter READ_RESET_VALUE_A.

        .sleep(1'b0)                    // 1-bit input: sleep signal to enable the dynamic power saving feature.
    );
    
    initial begin        
        #10 param_addr = param_addr + 1;
        #10 param_addr = param_addr + 1;
        #10 param_addr = param_addr + 1;
        
        #10 rst = ~rst;
        
        param_addr = 0;
        #10 param_addr = param_addr + 1;
        #10 param_addr = param_addr + 1;
        #10 param_addr = param_addr + 1;
        
        $finish;
    end
endmodule
/*
      
    int8 mult_a, mult_b, mult_p;
    
//    ADDMACC_MACRO #(
//      .DEVICE("7SERIES"),    // Target Device: "7SERIES" 
//      .LATENCY(3),           // Desired clock cycle latency, 0-4
//      .WIDTH_PREADD(8),     // Pre-adder input width, 1-25
//      .WIDTH_MULTIPLIER(8), // Multiplier input width, 1-18
//      .WIDTH_PRODUCT(16)     // MACC output width, 1-48
//   ) ADDMACC_MACRO_inst (
//      .PRODUCT(mult_p),   // MACC result output, width defined by WIDTH_PRODUCT parameter
//      .CARRYIN(0),   // 1-bit carry-in input
//      .CLK(clk),           // 1-bit clock input
//      .CE(1'b1),             // 1-bit clock enable input
//      .LOAD(0),         // 1-bit accumulator load input
//      .LOAD_DATA(0),   // Accumulator load data input, width defined by WIDTH_PRODUCT parameter
//      .MULTIPLIER(mult_a), // Multiplier data input, width defined by WIDTH_MULTIPLIER parameter
//      .PREADD2(0),   // Preadder data input, width defined by WIDTH_PREADD parameter
//      .PREADD1(mult_b),   // Preadder data input, width defined by WIDTH_PREADD parameter
//      .RST(rst)            // 1-bit active high synchronous reset
//   );

//    mult_s8_s8_dsp your_instance_name (
//      .CLK(clk),    // input wire CLK
//      .A(mult_a),        // input wire [7 : 0] A
//      .B(mult_b),        // input wire [7 : 0] B
//      .SCLR(0),  // input wire SCLR
//      .P(mult_p)        // output wire [15 : 0] P
//    );

    ADDSUB_MACRO #(
        .DEVICE("7SERIES"), // Target Device: "7SERIES"
        .LATENCY(2),  // Desired clock cycle latency, 0-2
        .WIDTH(8)   // Input / output bus width, 1-48
    ) dorprod_add (
        .CARRYOUT(),        // 1-bit carry-out output signal
        .RESULT(mult_p),  // Add/sub result output, width defined by WIDTH parameter
        .A(mult_a), // Input A bus, width defined by WIDTH parameter
        .ADD_SUB(1'b1),     // 1-bit add/sub input, high selects add, low selects subtract
        .B(mult_b),     // Input B bus, width defined by WIDTH parameter
        .CARRYIN(1'b0),     // 1-bit carry-in input
        .CE(1'b1),          // 1-bit clock enable input
        .CLK(clk),          // 1-bit clock input
        .RST(rst)          // 1-bit active high synchronous reset
    );
    
    initial begin
        #10 rst = ~rst;
        
        mult_a = 2;
        mult_b = 2;
        #10;
        
        mult_a = 3;
        mult_b = 3;
        #10;
        
        mult_a = 4;
        mult_b = 4;
        #10;
        
        mult_a = 8;
        mult_b = 9;
        #500;
        
        $finish;
    end

endmodule
*/