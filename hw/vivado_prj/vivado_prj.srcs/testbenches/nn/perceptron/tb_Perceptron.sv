`timescale 1ns/1ns
`include "types.sv"

module tb_Perceptron;
    localparam FEATURES = 128;
    localparam ITERS = 4;

    // Test data.
    nndata test_din [ITERS][FEATURES];
    nndata test_dout [ITERS];
    // Verifying internal variables.
    integer clocks_until_dout_vld = 0;
    real nn_out_r, nn_des_out_r, delta_r, err;

    // Control signal.
    logic clk_in                = 1;
    logic rst                   = 1;
    perc_param_addr param_addr  = ~0;
    // IO.
    nndata perc_din [FEATURES];
    nndata perc_dout;
    logic  perc_din_vld         = 0;
    logic  perc_dout_vld;
    // Pipeline validation.
    logic  i_bypass_relu = 0, o_bypass_relu;
    logic  i_data_tag = 0, o_data_dat;    
    
    // UUT
    nn_Perceptron #(.FEATURES(FEATURES), .PARAM_FILE("perc_weights_bias.mem")) UUT (
        .clk(clk_in),
        .rst(rst),
        .param_addr(param_addr),
        
        .din(perc_din),
        .din_vld(perc_din_vld),
        .dout(perc_dout),
        .dout_vld(perc_dout_vld),

        .i_pp_bypass_relu(i_bypass_relu),
        .o_pp_bypass_relu(o_bypass_relu),
        .i_pp_data_tag(i_data_tag),
        .o_pp_data_tag(o_data_dat)
    );
    
    always #5 clk_in = ~clk_in; //100MHz clock.
    
    // Load data
    initial begin
        $readmemh("perc_data_in.mem", test_din);
        $readmemh("perc_data_out.mem", test_dout);
        // $readmemh({`PROJECT_PATH, "roms/tb/perceptron/data_out.mem"}, nn_desired_out);
    end

    // UUT behaviour.
    initial begin        
        // Wait 1 cycle for reset.
        #10 rst = ~rst;
        // param_addr += 1;

        // Feed data into the perceptron.
        for (integer i = 0; i < ITERS; i+=1) begin
            perc_din_vld = 1;
            perc_din = test_din[i];
            i_bypass_relu = ~i_bypass_relu;
            i_data_tag = ~i_data_tag;
            param_addr = param_addr + 1;
            clocks_until_dout_vld += 1;
            #10;
        end
        
        perc_din_vld = 0;
        perc_din = '{default:0};

        // Wait until we get valid data out.
        while (!perc_dout_vld) begin
            clocks_until_dout_vld += 1;
            #10;
        end

        assert (clocks_until_dout_vld == UUT.STAGES) else $error("Perceptron does not have expected latency");
        
        // Compute delta and expected result.
        for (integer i = 0; i < ITERS; i += 1) begin
            nn_out_r = fixed2real(perc_dout);
            nn_des_out_r = fixed2real(test_dout[i]);
            delta_r = nn_out_r - nn_des_out_r;
            err = $sqrt(delta_r * delta_r);

            if (err > 0.01) begin
                $error("Incorrect result for index %d. Expected %x (%f) got %x (%f)",
                        i, test_dout[i], nn_des_out_r, perc_dout, nn_out_r);
                // $finish;        
            end
            #10;            
        end

        $display("Perceptron testbench OK.");
        $finish;
    end
    
endmodule
