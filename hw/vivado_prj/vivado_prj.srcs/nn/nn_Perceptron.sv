`timescale 1ns/1ps
`include "types.sv"

// Parameter memory:
//  - Every address is (FEATURES+1) * 16b wide. If FEATURES=128 -> 2064, if FEATURES=32 (tb) -> 528.
//  - Bias is 16 LSBs
module nn_Perceptron #(integer FEATURES = 128, string PARAM_FILE = "none") (
    input  logic  clk,
    input  logic  rst,

    input  perc_param_addr param_addr,

    input  nndata din[FEATURES],
    input  logic  din_vld,
    output nndata dout,
    output logic  dout_vld,

    input  logic  i_pp_bypass_relu,
    output logic  o_pp_bypass_relu,
    input  logic  i_pp_data_tag,
    output logic  o_pp_data_tag
);

    // Assertions to validate parameters.
    initial begin
        assert ((FEATURES & (FEATURES - 1)) == 0) else $error("#FEATURES must be a power of two");
        assert (FEATURES <= 128) else $error("#FEATURES can't be >128 - rest assumes that");
    end

    localparam integer LEVELS      = $clog2(FEATURES);
    localparam integer MULT_LAT    = 3;
    localparam integer ADD_LAT     = 2;
    localparam integer STAGES      = MULT_LAT + ADD_LAT * (LEVELS + 1);    // LEVELS for adder tree and additional stage to add bias.
    genvar i, j;

    nndata weights [FEATURES];
    nndata bias_latency_adjusted;
    nndata bias_rom;

    nndata_dbl adder_tree[2 * FEATURES - 1];

    // BRAM for weights and biases.
    bit [129*FP_SIZE-1:0] rom_out;
    assign {>>{weights}} = rom_out[128*FP_SIZE-1:0];
    assign bias_rom = rom_out[129*FP_SIZE-1:128*FP_SIZE];

    xpm_memory_sprom #(
        .ADDR_WIDTH_A(PERC_PARAM_ADDR_WIDTH),              // DECIMAL
        .AUTO_SLEEP_TIME(0),           // DECIMAL
        .CASCADE_HEIGHT(0),            // DECIMAL
        .ECC_MODE("no_ecc"),           // String
        .MEMORY_INIT_FILE(PARAM_FILE), // String
        .MEMORY_INIT_PARAM(""),        // String
        .MEMORY_OPTIMIZATION("true"),  // String
        .MEMORY_PRIMITIVE("block"),    // String
        .MEMORY_SIZE(PERC_PARAM_ROM_SIZE), // DECIMAL
        .MESSAGE_CONTROL(0),           // DECIMAL
        .READ_DATA_WIDTH_A(FP_SIZE * (FEATURES + 1)), // DECIMAL
        .READ_LATENCY_A(1),            // DECIMAL
        .READ_RESET_VALUE_A("0"),      // String
        .RST_MODE_A("SYNC"),           // String
        .SIM_ASSERT_CHK(1),            // DECIMAL; 0=disable simulation messages, 1=enable simulation messages
        .USE_MEM_INIT(1),              // DECIMAL
        .USE_MEM_INIT_MMI(0),          // DECIMAL
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
        
    // Parallel multipliers.
    // Fill in the last level of adder_tree with dotproduct of data and weights.
    // Last `FEATURES` elements of the `adder_tree` array represent the lowest level of the adder tree.
    generate
        for (i = 0; i < FEATURES; i=i+1) begin: PARALLEL_MULTIPLIERS
            // Not applicable now but if FP_SIZE is 8 then DSPs can be used more efficiently
            // https://www.xilinx.com/content/dam/xilinx/support/documents/white_papers/wp486-deep-learning-int8.pdf
            if (FP_SIZE == 16)
                mult_s16_s16_dsp dotprod_mult (
                  .CLK(clk),            // input wire CLK
                  .A(weights[i]),       // input wire [7 : 0] A
                  .B(din[i]),           // input wire [7 : 0] B
                  .P(adder_tree[FEATURES - 1 + i])        // output wire [15 : 0] P
                );
            else if (FP_SIZE == 8)
                mult_s8_s8_dsp dotprod_mult (
                  .CLK(clk),            // input wire CLK
                  .A(weights[i]),       // input wire [7 : 0] A
                  .B(din[i]),           // input wire [7 : 0] B
                  .P(adder_tree[FEATURES - 1 + i])        // output wire [15 : 0] P
                );
            else $error("Bit Width Not supported");
        end
    endgenerate
    
    // Adder tree.
    // Sum all levels - one level per clock cycle.
    generate
        for (i = 0; i < LEVELS; i=i+1) begin: ADDER_TREE_LEVEL
        // First level is already computed in the PARALLEL_MULTIPLIERS loop. Compute i-th level of adder tree.
            for (j = 0; j < 2**i; j=j+1) begin: ADDER_TREE_LEVEL_ELEMENTS
                add_s32_s32_dsp adder_intermediate (
                  .A(adder_tree[(2**i + j) * 2 - 1]),   // input wire [31 : 0] A
                  .B(adder_tree[(2**i + j) * 2]),       // input wire [31 : 0] B
                  .CLK(clk),                            // input wire CLK
                  .S(adder_tree[2**i - 1 + j])          // output wire [31 : 0] S
                );
            end
        end
    endgenerate
    

    // Add bias to the output of the dotproduct.
    ShiftRegister #(.WIDTH(FP_SIZE), .LENGTH(STAGES - ADD_LAT)) u_ShrBias (.clk, .rst, .din(bias_rom), .dout(bias_latency_adjusted));
    nndata_dbl out_w_bias, bias_expanded, dout_shifted;
    
    assign bias_expanded = { {QM_BITS{1'b0}} , bias_latency_adjusted , {QN_BITS{1'b0}} };
    add_s32_s32_dsp adder_bias (
      .A(adder_tree[0]),  // input wire [31 : 0] A
      .B(bias_expanded), // input wire [31 : 0] B
      .CLK(clk),          // input wire CLK
      .S(out_w_bias)      // output wire [31 : 0] S
    );

    // Scaled output of the perceptron.
//    assign dout_shifted = out_w_bias >>> QM_BITS; 
//    assign dout = dout_shifted[(FP_DBL_SIZE - QM_BITS) : QN_BITS];
    assign dout = nndata_double_to_single(out_w_bias);

    // Moving data along a pipeline.
    ShiftRegister #(.WIDTH(1), .LENGTH(STAGES)) u_ShrDoutVld (.clk, .rst, .din(din_vld), .dout(dout_vld));
    ShiftRegister #(.WIDTH(1), .LENGTH(STAGES)) u_ShrDataTag (.clk, .rst, .din(i_pp_data_tag), .dout(o_pp_data_tag));
    ShiftRegister #(.WIDTH(1), .LENGTH(STAGES)) u_ShrBypassRelu (.clk, .rst, .din(i_pp_bypass_relu), .dout(o_pp_bypass_relu));

endmodule: nn_Perceptron 

/*
Results:
          0: Computed: 062e0 (1.544922) Expected: 062e1 (1.544983)
Incorrect result for index           0
          1: Computed: 07fdd (1.997864) Expected: 07fdd (1.997864)
          2: Computed: 07165 (1.771790) Expected: 07166 (1.771851)
Incorrect result for index           2
*/

