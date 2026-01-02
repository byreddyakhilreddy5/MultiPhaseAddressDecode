module addr_decode (
    input  wire        clk,
    input  wire        rst_n,        // active-low reset (optional but recommended)

    // Address per phase
    input  wire [13:0] address_P0,
    input  wire [13:0] address_P1,
    input  wire [13:0] address_P2,
    input  wire [13:0] address_P3,

    // CS per phase
    input  wire        cs_P0,
    input  wire        cs_P1,
    input  wire        cs_P2,
    input  wire        cs_P3,

    // Registered outputs (1-cycle delayed)
    output reg  [55:0] addr_out,
    output reg  [3:0]  cs_out
);

    // Internal arrays
    wire [13:0] addr_phase [0:3];
    wire [13:0] addr_phase_processed [0:3];
    wire        cs_phase [0:3];
    wire        cs_prev  [0:3];
    wire        all_ones [0:3];

    // Map inputs
    assign addr_phase[0] = address_P0;
    assign addr_phase[1] = address_P1;
    assign addr_phase[2] = address_P2;
    assign addr_phase[3] = address_P3;

    assign cs_phase[0] = cs_P0;
    assign cs_phase[1] = cs_P1;
    assign cs_phase[2] = cs_P2;
    assign cs_phase[3] = cs_P3;

    // Previous CS
    assign cs_prev[0] = 1'b0;
    assign cs_prev[1] = cs_phase[0];
    assign cs_prev[2] = cs_phase[1];
    assign cs_prev[3] = cs_phase[2];

    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : ADDR_PROCESS

            // Detect all-ones address
            assign all_ones[i] = &addr_phase[i];

            // Conditional inversion logic (combinational)
            assign addr_phase_processed[i] =
                (all_ones[i] && !(cs_prev[i] && cs_phase[i])) ?
                    addr_phase[i] :
                    ~addr_phase[i];

        end
    endgenerate

    // Register outputs → available next clock cycle
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            addr_out <= 56'b0;
            cs_out   <= 4'b0;
        end else begin
            addr_out <= {
                addr_phase_processed[3],
                addr_phase_processed[2],
                addr_phase_processed[1],
                addr_phase_processed[0]
            };

            cs_out <= {
                cs_phase[3],
                cs_phase[2],
                cs_phase[1],
                cs_phase[0]
            };
        end
    end

endmodule
