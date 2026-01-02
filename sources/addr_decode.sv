module addr_decode (
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

    // Outputs
    output wire [55:0] addr_out,   // concatenated processed address
    output wire [3:0]  cs_out      // concatenated CS
);

    // Internal arrays
    wire [13:0] addr_phase [0:3];
    wire [13:0] addr_phase_processed [0:3];
    wire        cs_phase [0:3];
    wire        cs_prev  [0:3];
    wire        all_ones [0:3];

    // Map inputs to arrays
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

            // Conditional inversion logic
            assign addr_phase_processed[i] =
                (all_ones[i] && !(cs_prev[i] && cs_phase[i])) ?
                    addr_phase[i] :        // do NOT invert
                    ~addr_phase[i];        // invert

        end
    endgenerate

    // Concatenate processed addresses (P3 MSB, P0 LSB)
    assign addr_out = {
        addr_phase_processed[3],
        addr_phase_processed[2],
        addr_phase_processed[1],
        addr_phase_processed[0]
    };

    // Concatenate CS (P3 MSB, P0 LSB)
    assign cs_out = {
        cs_phase[3],
        cs_phase[2],
        cs_phase[1],
        cs_phase[0]
    };

endmodule
