`timescale 1ns / 1ps

module tb_SIPO;

    logic clk;
    logic rst_n;
    
    bit  [ 3:0] sipo_in;
    wire [15:0] sipo_out;
    wire        sipo_vld;
    
    SIPO #(.IN_WIDTH(4), .OUT_WIDTH(16))
        uut (.clk, .rst_n, .in(sipo_in), .out(sipo_out), .out_vld(sipo_vld));
        
    always #5 clk <= ~clk;
        
    initial begin
        clk = 1;
        rst_n = 0;
        sipo_in = 0;
        
        // Wait 5 cycles for reset.
        #50;
        rst_n = 1;
        
        // After reset valid is not asserted.
        assert (sipo_vld == 0) else $error("SIPO reports valid output after reset.");
        
        // Feed in data in 4 cycles.
        for (integer i = 1; i <= 4; i++) begin
            assert (sipo_vld == 0) else $error("SIPO is in valid state before it should be (i=%d).", i);
            sipo_in = i;
            #10;
        end
        
        // Check we are in valid state after 4 clock cycles.
        assert (sipo_vld == 1) else $error("SIPO is in invalid state after 4 cycles - output should be valid");
        assert (sipo_out == 16'h4321) else $error("SIPO has unexpected output");
        
        // Next 4 clock cycles should show invalid out.
        for (bit[3:0] i = 0; i < 4; i++) begin
            #10;
            assert (sipo_vld == 0) else $error("SIPO out should be invalid after strobing out_vld (i=%d).", i);
        end
        
        // After 4 more cycles the output should be valid again.
        assert (sipo_vld == 1) else $error("SIPO is in invalid state after 4 cycles - output should be valid");
        assert (sipo_out == 16'h4444) else $error("SIPO has unexpected output");
        
        $display("SIPO Testbench OK.");
        $finish;
    end 
endmodule
