`timescale 1ns/1ns
`include "types.sv"

`ifndef PROJECT_PATH
`define PROJECT_PATH "C:/Users/user/source/fpga/fyp/SimpleNN/"
`endif // PROJECT_PATH

module tb_Linear;
    localparam IN_FEATS = 16;
    localparam OUT_FEATS = 3;
    
    // Control signal.
    logic clk_in;
    logic rst_n;    
    
    nn_data_t weight_mat    [OUT_FEATS][IN_FEATS];
    nn_data_t bias_vec      [OUT_FEATS];
    nn_data_t data_in       [IN_FEATS];
    logic     data_in_vld;
    nn_data_t data_out      [OUT_FEATS];
    logic     data_out_vld;
    nn_data_t data_out_gt   [OUT_FEATS];
    
    real    dout, dogt, delta_r;
    
    nn_Linear #(.IN_DIM(IN_FEATS), .OUT_DIM(OUT_FEATS)) UUT (
        .clk(clk_in),
        .rst_n(rst_n),
        
        .weight_mat(weight_mat),
        .bias_vec(bias_vec),
        
        .din(data_in),
        .din_vld(data_in_vld),
        .dout(data_out),
        .dout_vld(data_out_vld)
    );
    
    // Load ROMs.
    initial begin
        $readmemh({`PROJECT_PATH, "roms/tb/linear/weights.mem"}, weight_mat);
        $readmemh({`PROJECT_PATH, "roms/tb/linear/bias.mem"}, bias_vec);
        $readmemh({`PROJECT_PATH, "roms/tb/linear/data_in.mem"}, data_in);
        $readmemh({`PROJECT_PATH, "roms/tb/linear/data_out.mem"}, data_out_gt);
    end

    always #5 clk_in = ~clk_in; //100MHz clock.
    
    // UUT behaviour.
    initial begin
        // Initialization.
        clk_in = 0;
        rst_n = 0;
        data_in_vld = 0;
        
        // Wait 1 clock cycle for everything to reset.
        #10;
        rst_n = 1;
        data_in_vld = 1;
        
        // Wait 10 clock cycles for computation.
        #100;
        assert (data_out_vld == 1) $display("Computation did not finish after 10 clock cycles");        
        
        $display("Results:");
        for (int i = 0; i < OUT_FEATS; i++) begin
            dout = real'(data_out[i])/(2.0 ** FRAC_BITS);
            dogt = real'(data_out_gt[i])/(2.0 ** FRAC_BITS);
            delta_r = $sqrt((dout - dogt) * (dout - dogt));
            
            $display("%d: Computed: %x (%f) Expected: %x (%f) - delta = %f", i, data_out[i], dout, data_out_gt[i], dogt, delta_r);            
            if (delta_r > 0.01) begin
                $display("Incorrect result for index %d", i);
            end
        end
        
        $finish;         
    end
    
endmodule