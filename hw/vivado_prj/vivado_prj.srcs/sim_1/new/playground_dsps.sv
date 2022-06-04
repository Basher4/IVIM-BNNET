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

module playground_dsps;
    
    logic clk = 1, rst = 1, ce = 1;
    always #5 clk = ~clk;
    
    int16 mult_a, mult_b;
    int32 mult_p;
    
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

//    MULT_MACRO #(
//        .DEVICE("7SERIES"), // Target Device: "7SERIES" 
//        .LATENCY(3),        // Desired clock cycle latency, 0-4
//        .WIDTH_A(16),       // Multiplier A-input bus width, 1-25
//        .WIDTH_B(16),       // Multiplier B-input bus width, 1-18
//        .WIDTH_P(32)
//    ) u_macro_inst (
//        .P(mult_p),     // Multiplier output bus, width determined by WIDTH_P parameter
//        .A(mult_a),     // Multiplier input A bus, width determined by WIDTH_A parameter
//        .B(mult_b),     // Multiplier input B bus, width determined by WIDTH_B parameter
//        .CE(ce),   // 1-bit active high input clock enable
//        .CLK(clk), // 1-bit positive edge clock input
//        .RST(rst)  // 1-bit input active high reset
//    );

    mult_s16_s16_dsp your_instance_name (
        .CLK(clk),
        .A(mult_a),
        .B(mult_b),
        .P(mult_p)
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
        
        #100 ce = ~ce;
        
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
