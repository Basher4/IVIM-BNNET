`timescale 1ns/1ps

module BernoulliSampler #(WIDTH = 128) (
    input logic clk,
    input logic rst,
    
    input logic fifo_rd_en,
    output bit [WIDTH-1:0] fifo_out,
    output logic fifo_full,
    output logic fifo_empty,
    output logic fifo_valid
);

    localparam integer SIPO_BITS = WIDTH / 4;   // Generate a sample every 4 clock cycles.
    localparam bit [127:0] bs_init [SIPO_BITS][3] = {
        { 128'hc018a03d5f06769732852cbf8651dc93, 128'h1ecd2d17de33f737d20a68802f2b99d5, 128'h53723fc67b6a6229a5afcb3347ad31e8 },
        { 128'h61f8595abe6db5f3569d27dff806a771, 128'h690ef684e1cf0d0779aa80e153173332, 128'h82d014a77650cef915e9237a5daa1d50 },
        { 128'hcf2235a02c6b8f30362bcd3e2dbdf3a5, 128'hab562232de439364eef028f6693860b8, 128'h354f2a599253373339ef57c369bc4118 },
        { 128'h33ba900b784e041b308f43bceb30a202, 128'h604b53211233e6976dc7885eea0c8ece, 128'h330cea4342e03b9bb242f2598257c4c1 },
        { 128'h4a9f45b4f225153c4e721a28b8cc4ab7, 128'hfa00cd09d995bec31f067ff5cfb3e8f9, 128'hb018d1c54853a3b217b49c364afe3b76 },
        { 128'h5ce40e99afdddd4e613f8792faf328d9, 128'hcf95d2919b9ff8b24a2346e3fb66d508, 128'h064533a2675a94569a2c10c2a942a9df },
        { 128'h7e3d8a595439e75ec5c68544e11c4f0d, 128'h928610235b7bcaece923d9936547d314, 128'h32fb800db03cce4d1583b187e193d019 },
        { 128'hfb5d0dfbb4a80c553d62362a6f50ab90, 128'h756515d51286d55b1a424fecdedc1aaa, 128'hf19453416e874d4b9d5952fdfa735ec2 },
        { 128'ha29f77dffbe5c577bc52f87e24a53c79, 128'hb1e729a462a073420fb2f5afb3c5fec0, 128'h20f2df13aec4885fc570b9012a63a949 },
        { 128'h25e9d91b67cdc52a53e8e424939c37c3, 128'h1058cb89e8a874c0b81c42dee226d2f3, 128'hb2db7d78fb3ecc5a46380a83ac8abf1a },
        { 128'hbb9ef9c1bc0c320742e8e01cf168f5a7, 128'h05b138580643334769368cad22313002, 128'hd8f23905763f5d775d4bbdf5ecce2b62 },
        { 128'h50baec571c6373ceca25bb6c57a478d3, 128'h5cf42e23b001b6b321295736a0967e1e, 128'h5608ab5c67ec6c19cdea6d011fecf191 },
        { 128'h6c50f6136b25d7033eb79e8411e998ce, 128'h81d443455b38282dbf08d3bc683a4d33, 128'h7172fb8165be33f0da2d913145a06549 },
        { 128'h642816813ee7e10ddccef481ce3dc62c, 128'hf46957295a7a74c6c41b23bcf8fa351f, 128'hfbd9b7cce84339acbdca4a8e3ebb323b },
        { 128'he7e69985280b8c78607d234a56df24a3, 128'h69f9c53a59e91ff99a35232b1c928a29, 128'h8719abf1c227e4cadf6d2f620d0d27db },
        { 128'h408673a05baef95b0c91b2325af46930, 128'h49af74bbfedcdaf66153d28ffdc4559c, 128'h9a6f2c3db5a35eef6af7510a4e7ec079 },
        { 128'heb508149a700b6e0efdf15d43e0f9e65, 128'h1a404745a0c1ec1979a5bed20acba4ca, 128'he84defed890178361059fbf3b8947051 },
        { 128'hbba1986be2e5065d8e561e3280915e21, 128'h5090e7023109325dd27f57a1b24befe8, 128'hee9e36ae45076d7604fb50bc1af2736f },
        { 128'hf1ec288e2af1b0b5e8eafd346f38885e, 128'haa9768d9b139fc17c8adca3e7d4266cb, 128'hecccddbb9f8af4f932a4ee0e3b00901a },
        { 128'hea7b137f7b41cb5f5602eda12bd9b9b3, 128'h6fab9dad2e0c9923452ab61b0de947e8, 128'h067542a3e83c0447439f9aafe08171e6 },
        { 128'h8c61c38fbf6c6c838f9150cc91ecce8a, 128'h22cdd20f0bb256c704c36feb208f187d, 128'h2a4a52ae764dc1fc6cf9ddf0a747ddc4 },
        { 128'h1d7967d9e311934a48d3418b680c56ef, 128'hbac595370623d80f27ce2b59a55e36bb, 128'h264933022b838948bc030b93445a3ee4 },
        { 128'h28941f7eb5abde3efb168f05c7fe31e8, 128'hc2088c30f77328478506bedf333f97ab, 128'h6d2ab01451f36b5fdd72970969ca06ac },
        { 128'hd0a153b58d972727a22cc81690170bc0, 128'h2acd7c880361620f78841c4d800c6aac, 128'h7b98187cd97d366b43349d75a9ed82af },
        { 128'h8dcff50cf6eee008154e5707845ae633, 128'ha5fe316b7ebc2560469904fb5fa36663, 128'hbe99c5e0ff990339841cc67c5286f81b },
        { 128'h9384311df88ae2b45001be22ee5de8dd, 128'he8fffc987dcf70b61281838e7f77e47c, 128'hda6a648980d167bdc448740598308632 },
        { 128'h090a6f79e4431c63681286a5a368052d, 128'h82ec9f1815406a0c175f5035e7cde77d, 128'h29b4782286e3f61011baab3e5a8f763f },
        { 128'hcb76ff2c190b2725f7d29d883d248d63, 128'h90732b6a236aab6f9d73b67c13751d82, 128'h24117fe1ea7e8d46e056610ef7b0a725 },
        { 128'hac6ca470108655eb0a361883226b8d42, 128'h65640110bfb89be56ace3a5ae9e47b5f, 128'hea2f5a8dac1bdccfe8d6f4f39b147eb8 },
        { 128'ha1f673b79e0608cdf06eb15ee2742c9c, 128'h3acd29dcc26a1bba4e5acc114ebd0ccb, 128'hbb000d2aea84c4b6978d5ce0a59e0eac },
        { 128'h125b433d09e3455b628176582b669b06, 128'hb314ea3ef2c04e0a927e191fb190bfb0, 128'h321db1c64e5ffa242ae9cef848f11b4c },
        { 128'hd8d06c2525fbe0239b52eccdd17b18d6, 128'h73afeb575346f1e81857deec963acc40, 128'hfa97eb059aa6dcfc3c8e955058ff02bd }
    };

    initial begin
        assert (WIDTH > 128) else $error("WIDTH must be less than internal fifo width.");
    end
    
    bit [SIPO_BITS-1:0] sipo_in;
    bit [WIDTH-1:0]     sipo_out;
    logic               sipo_out_vld;
    
    genvar i;
    generate
        for (i = 0; i < SIPO_BITS; i++) begin
            // LFSR to sample random bernoulli variables. Each has p=0.5.
            bit [2:0] lfsr_out;
            LFSR #(.RESET_VALUE(bs_init[i][0])) lfsr1 (.clk, .rst, .out(lfsr_out[0]));
            LFSR #(.RESET_VALUE(bs_init[i][1])) lfsr2 (.clk, .rst, .out(lfsr_out[1]));
            LFSR #(.RESET_VALUE(bs_init[i][2])) lfsr3 (.clk, .rst, .out(lfsr_out[2]));

            assign sipo_in[i] = &lfsr_out; // Make p=0.125
        end
    endgenerate
    
    SIPO #(.IN_WIDTH(SIPO_BITS),
           .OUT_WIDTH(WIDTH))
        sipo (
           .clk,
           .rst,
           .in(sipo_in),
           .out(sipo_out),
           .out_vld(sipo_out_vld)
    );
    
    fifo_128w_512d samples_fifo (
        .clk(clk),                  // input wire clk
        .srst(rst),                 // input wire srst
        
        .din(sipo_out),             // input wire [127 : 0] din
        .wr_en(sipo_out_vld),       // input wire wr_en
        .rd_en(fifo_rd_en),         // input wire rd_en
        .dout(fifo_out),            // output wire [127 : 0] dout
        .full(fifo_full),           // output wire full
        .empty(fifo_empty),         // output wire empty
        .valid(fifo_valid),         // output wire valid
        
        // TODO: I should probably do something with these signals.
        .wr_rst_busy(),  // output wire wr_rst_busy
        .rd_rst_busy()   // output wire rd_rst_busy
    );

endmodule
