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

    // TODO: Implement the multi-phase address decode logic
    // See docs/Specification.md for details

endmodule
