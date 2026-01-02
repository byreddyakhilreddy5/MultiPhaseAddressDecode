"""
Testbench for Multi-Phase Address Decode Module

Tests the addr_decode implementation according to the specification.
The module conditionally inverts addresses based on all-ones detection
and chip-select conditions, then concatenates the results.
"""

import cocotb
from cocotb.triggers import Timer, ReadOnly, NextTimeStep


class AddrDecodeReference:
    """Reference model for addr_decode module"""
    
    def __init__(self):
        pass
    
    def process_phase(self, address, cs_prev, cs_curr):
        """
        Process a single address phase according to the specification.
        
        Args:
            address: 14-bit address value
            cs_prev: Previous phase chip-select (1-bit)
            cs_curr: Current phase chip-select (1-bit)
        
        Returns:
            Processed 14-bit address (inverted or not based on conditions)
        """
        # All-ones detection: address == 14'b11111111111111
        all_ones = (address == 0x3FFF)  # 14 bits all ones
        
        # Conditional inversion rule:
        # NOT invert if: (all_ones) AND NOT (cs_prev AND cs_curr)
        # Invert in all other cases
        if all_ones and not (cs_prev and cs_curr):
            # Do NOT invert
            return address
        else:
            # Invert (bitwise NOT of 14 bits)
            return (~address) & 0x3FFF
    
    def compute_outputs(self, addresses, cs_signals):
        """
        Compute expected outputs for all phases.
        
        Args:
            addresses: List of 4 addresses [P0, P1, P2, P3]
            cs_signals: List of 4 chip-selects [P0, P1, P2, P3]
        
        Returns:
            Tuple (addr_out, cs_out) where:
            - addr_out: 56-bit concatenated processed address
            - cs_out: 4-bit concatenated chip-select
        """
        # Compute previous phase CS
        cs_prev = [0, cs_signals[0], cs_signals[1], cs_signals[2]]
        
        # Process each phase
        processed = []
        for i in range(4):
            processed_addr = self.process_phase(addresses[i], cs_prev[i], cs_signals[i])
            processed.append(processed_addr)
        
        # Concatenate addresses: {P3, P2, P1, P0}
        addr_out = (processed[3] << 42) | (processed[2] << 28) | (processed[1] << 14) | processed[0]
        
        # Concatenate CS: {P3, P2, P1, P0}
        cs_out = (cs_signals[3] << 3) | (cs_signals[2] << 2) | (cs_signals[1] << 1) | cs_signals[0]
        
        return addr_out, cs_out


async def set_inputs(dut, addr_p0, addr_p1, addr_p2, addr_p3, cs_p0, cs_p1, cs_p2, cs_p3):
    """Set all inputs to the DUT"""
    dut.address_P0.value = addr_p0
    dut.address_P1.value = addr_p1
    dut.address_P2.value = addr_p2
    dut.address_P3.value = addr_p3
    dut.cs_P0.value = cs_p0
    dut.cs_P1.value = cs_p1
    dut.cs_P2.value = cs_p2
    dut.cs_P3.value = cs_p3
    await ReadOnly()  # Wait for combinational logic to settle


@cocotb.test()
async def test_all_ones_both_cs_deasserted(dut):
    """Test all-ones address with both previous and current CS deasserted - should NOT invert"""
    ref = AddrDecodeReference()
    
    # Test P1: all-ones, cs_P0=0, cs_P1=0
    addresses = [0x0001, 0x3FFF, 0x2000, 0x1000]
    cs_signals = [0, 0, 1, 1]
    
    await set_inputs(dut, addresses[0], addresses[1], addresses[2], addresses[3],
                     cs_signals[0], cs_signals[1], cs_signals[2], cs_signals[3])
    
    expected_addr_out, expected_cs_out = ref.compute_outputs(addresses, cs_signals)
    
    actual_addr_out = dut.addr_out.value.to_unsigned()
    actual_cs_out = dut.cs_out.value.to_unsigned()
    
    assert actual_addr_out == expected_addr_out, (
        f"Address output mismatch: expected 0x{expected_addr_out:014X}, got 0x{actual_addr_out:014X}"
    )
    assert actual_cs_out == expected_cs_out, (
        f"CS output mismatch: expected 0b{expected_cs_out:04b}, got 0b{actual_cs_out:04b}"
    )
    
    # Verify P1 is NOT inverted (all-ones preserved)
    p1_processed = (actual_addr_out >> 14) & 0x3FFF
    assert p1_processed == 0x3FFF, (
        f"P1 should NOT be inverted (all-ones with both CS deasserted), got 0x{p1_processed:04X}"
    )


@cocotb.test()
async def test_all_ones_prev_asserted_curr_deasserted(dut):
    """Test all-ones address with previous CS asserted, current deasserted - should NOT invert"""
    ref = AddrDecodeReference()
    
    # Test P1: all-ones, cs_P0=1, cs_P1=0
    addresses = [0x0001, 0x3FFF, 0x2000, 0x1000]
    cs_signals = [1, 0, 1, 1]
    
    await set_inputs(dut, addresses[0], addresses[1], addresses[2], addresses[3],
                     cs_signals[0], cs_signals[1], cs_signals[2], cs_signals[3])
    
    expected_addr_out, expected_cs_out = ref.compute_outputs(addresses, cs_signals)
    
    actual_addr_out = dut.addr_out.value.to_unsigned()
    actual_cs_out = dut.cs_out.value.to_unsigned()
    
    assert actual_addr_out == expected_addr_out, (
        f"Address output mismatch: expected 0x{expected_addr_out:014X}, got 0x{actual_addr_out:014X}"
    )
    
    # Verify P1 is NOT inverted
    p1_processed = (actual_addr_out >> 14) & 0x3FFF
    assert p1_processed == 0x3FFF, (
        f"P1 should NOT be inverted (all-ones with prev=1, curr=0), got 0x{p1_processed:04X}"
    )


@cocotb.test()
async def test_all_ones_prev_deasserted_curr_asserted(dut):
    """Test all-ones address with previous CS deasserted, current asserted - should NOT invert"""
    ref = AddrDecodeReference()
    
    # Test P1: all-ones, cs_P0=0, cs_P1=1
    addresses = [0x0001, 0x3FFF, 0x2000, 0x1000]
    cs_signals = [0, 1, 1, 1]
    
    await set_inputs(dut, addresses[0], addresses[1], addresses[2], addresses[3],
                     cs_signals[0], cs_signals[1], cs_signals[2], cs_signals[3])
    
    expected_addr_out, expected_cs_out = ref.compute_outputs(addresses, cs_signals)
    
    actual_addr_out = dut.addr_out.value.to_unsigned()
    actual_cs_out = dut.cs_out.value.to_unsigned()
    
    assert actual_addr_out == expected_addr_out, (
        f"Address output mismatch: expected 0x{expected_addr_out:014X}, got 0x{actual_addr_out:014X}"
    )
    
    # Verify P1 is NOT inverted
    p1_processed = (actual_addr_out >> 14) & 0x3FFF
    assert p1_processed == 0x3FFF, (
        f"P1 should NOT be inverted (all-ones with prev=0, curr=1), got 0x{p1_processed:04X}"
    )


@cocotb.test()
async def test_all_ones_both_cs_asserted(dut):
    """Test all-ones address with both previous and current CS asserted - should INVERT"""
    ref = AddrDecodeReference()
    
    # Test P1: all-ones, cs_P0=1, cs_P1=1
    addresses = [0x0001, 0x3FFF, 0x2000, 0x1000]
    cs_signals = [1, 1, 1, 1]
    
    await set_inputs(dut, addresses[0], addresses[1], addresses[2], addresses[3],
                     cs_signals[0], cs_signals[1], cs_signals[2], cs_signals[3])
    
    expected_addr_out, expected_cs_out = ref.compute_outputs(addresses, cs_signals)
    
    actual_addr_out = dut.addr_out.value.to_unsigned()
    actual_cs_out = dut.cs_out.value.to_unsigned()
    
    assert actual_addr_out == expected_addr_out, (
        f"Address output mismatch: expected 0x{expected_addr_out:014X}, got 0x{actual_addr_out:014X}"
    )
    
    # Verify P1 IS inverted (all-ones becomes all-zeros)
    p1_processed = (actual_addr_out >> 14) & 0x3FFF
    assert p1_processed == 0x0000, (
        f"P1 should be INVERTED (all-ones with both CS asserted), got 0x{p1_processed:04X}"
    )


@cocotb.test()
async def test_non_all_ones_address(dut):
    """Test non-all-ones address - should always INVERT regardless of CS"""
    ref = AddrDecodeReference()
    
    # Test P2: non-all-ones (0x2000), various CS combinations
    addresses = [0x0001, 0x1000, 0x2000, 0x3000]
    cs_signals = [0, 0, 0, 0]  # All CS deasserted
    
    await set_inputs(dut, addresses[0], addresses[1], addresses[2], addresses[3],
                     cs_signals[0], cs_signals[1], cs_signals[2], cs_signals[3])
    
    expected_addr_out, expected_cs_out = ref.compute_outputs(addresses, cs_signals)
    
    actual_addr_out = dut.addr_out.value.to_unsigned()
    actual_cs_out = dut.cs_out.value.to_unsigned()
    
    assert actual_addr_out == expected_addr_out, (
        f"Address output mismatch: expected 0x{expected_addr_out:014X}, got 0x{actual_addr_out:014X}"
    )
    
    # Verify P2 is inverted (non-all-ones always inverts)
    p2_processed = (actual_addr_out >> 28) & 0x3FFF
    expected_p2_inverted = (~0x2000) & 0x3FFF
    assert p2_processed == expected_p2_inverted, (
        f"P2 should be INVERTED (non-all-ones), expected 0x{expected_p2_inverted:04X}, got 0x{p2_processed:04X}"
    )


@cocotb.test()
async def test_all_phases_independent(dut):
    """Test that all phases are processed independently"""
    ref = AddrDecodeReference()
    
    # Mix of conditions across all phases
    # P0: non-all-ones -> invert
    # P1: all-ones, both CS deasserted -> NOT invert
    # P2: all-ones, both CS asserted -> invert
    # P3: all-ones, prev=1, curr=0 -> NOT invert
    addresses = [0x0001, 0x3FFF, 0x3FFF, 0x3FFF]
    cs_signals = [0, 1, 1, 0]  # P2 has both asserted (cs_P1=1, cs_P2=1), P3 has prev=1, curr=0
    
    await set_inputs(dut, addresses[0], addresses[1], addresses[2], addresses[3],
                     cs_signals[0], cs_signals[1], cs_signals[2], cs_signals[3])
    
    expected_addr_out, expected_cs_out = ref.compute_outputs(addresses, cs_signals)
    
    actual_addr_out = dut.addr_out.value.to_unsigned()
    actual_cs_out = dut.cs_out.value.to_unsigned()
    
    assert actual_addr_out == expected_addr_out, (
        f"Address output mismatch: expected 0x{expected_addr_out:014X}, got 0x{actual_addr_out:014X}"
    )
    assert actual_cs_out == expected_cs_out, (
        f"CS output mismatch: expected 0b{expected_cs_out:04b}, got 0b{actual_cs_out:04b}"
    )
    
    # Verify each phase independently
    p0_processed = (actual_addr_out >> 0) & 0x3FFF
    p1_processed = (actual_addr_out >> 14) & 0x3FFF
    p2_processed = (actual_addr_out >> 28) & 0x3FFF
    p3_processed = (actual_addr_out >> 42) & 0x3FFF
    
    # P0: non-all-ones -> inverted
    assert p0_processed == ((~0x0001) & 0x3FFF), f"P0 should be inverted, got 0x{p0_processed:04X}"
    # P1: all-ones, both CS deasserted -> NOT inverted
    assert p1_processed == 0x3FFF, f"P1 should NOT be inverted, got 0x{p1_processed:04X}"
    # P2: all-ones, both CS asserted -> inverted
    assert p2_processed == 0x0000, f"P2 should be inverted, got 0x{p2_processed:04X}"
    # P3: all-ones, prev=1, curr=0 -> NOT inverted
    assert p3_processed == 0x3FFF, f"P3 should NOT be inverted, got 0x{p3_processed:04X}"


@cocotb.test()
async def test_output_concatenation(dut):
    """Test that outputs are concatenated correctly (P3 MSB to P0 LSB)"""
    ref = AddrDecodeReference()
    
    # Use distinct values for each phase to verify concatenation order
    addresses = [0x0001, 0x0002, 0x0003, 0x0004]
    cs_signals = [1, 0, 1, 0]
    
    await set_inputs(dut, addresses[0], addresses[1], addresses[2], addresses[3],
                     cs_signals[0], cs_signals[1], cs_signals[2], cs_signals[3])
    
    expected_addr_out, expected_cs_out = ref.compute_outputs(addresses, cs_signals)
    
    actual_addr_out = dut.addr_out.value.to_unsigned()
    actual_cs_out = dut.cs_out.value.to_unsigned()
    
    assert actual_addr_out == expected_addr_out, (
        f"Address output mismatch: expected 0x{expected_addr_out:014X}, got 0x{actual_addr_out:014X}"
    )
    assert actual_cs_out == expected_cs_out, (
        f"CS output mismatch: expected 0b{expected_cs_out:04b}, got 0b{actual_cs_out:04b}"
    )
    
    # Verify concatenation order: {P3, P2, P1, P0}
    p0_processed = (actual_addr_out >> 0) & 0x3FFF
    p1_processed = (actual_addr_out >> 14) & 0x3FFF
    p2_processed = (actual_addr_out >> 28) & 0x3FFF
    p3_processed = (actual_addr_out >> 42) & 0x3FFF
    
    # Verify CS concatenation: {P3, P2, P1, P0}
    assert (actual_cs_out & 0x1) == cs_signals[0], "cs_out[0] should be cs_P0"
    assert ((actual_cs_out >> 1) & 0x1) == cs_signals[1], "cs_out[1] should be cs_P1"
    assert ((actual_cs_out >> 2) & 0x1) == cs_signals[2], "cs_out[2] should be cs_P2"
    assert ((actual_cs_out >> 3) & 0x1) == cs_signals[3], "cs_out[3] should be cs_P3"


@cocotb.test()
async def test_previous_phase_cs_calculation(dut):
    """Test that previous phase CS is calculated correctly"""
    ref = AddrDecodeReference()
    
    # Test with known CS pattern to verify cs_prev calculation
    # cs_prev[0] = 0 (always)
    # cs_prev[1] = cs_P0
    # cs_prev[2] = cs_P1
    # cs_prev[3] = cs_P2
    addresses = [0x1000, 0x3FFF, 0x3FFF, 0x3FFF]
    cs_signals = [1, 0, 1, 0]
    
    await set_inputs(dut, addresses[0], addresses[1], addresses[2], addresses[3],
                     cs_signals[0], cs_signals[1], cs_signals[2], cs_signals[3])
    
    expected_addr_out, expected_cs_out = ref.compute_outputs(addresses, cs_signals)
    
    actual_addr_out = dut.addr_out.value.to_unsigned()
    
    assert actual_addr_out == expected_addr_out, (
        f"Address output mismatch: expected 0x{expected_addr_out:014X}, got 0x{actual_addr_out:014X}"
    )
    
    # Verify cs_prev calculation by checking P1 behavior
    # P1: all-ones, cs_prev[1]=cs_P0=1, cs_P1=0
    # Condition: all_ones && !(1 && 0) = 1 && !0 = 1 -> NOT invert
    p1_processed = (actual_addr_out >> 14) & 0x3FFF
    assert p1_processed == 0x3FFF, (
        f"P1 should NOT be inverted (cs_prev[1]=cs_P0=1, cs_P1=0), got 0x{p1_processed:04X}"
    )
    
    # Verify P2: all-ones, cs_prev[2]=cs_P1=0, cs_P2=1
    # Condition: all_ones && !(0 && 1) = 1 && !0 = 1 -> NOT invert
    p2_processed = (actual_addr_out >> 28) & 0x3FFF
    assert p2_processed == 0x3FFF, (
        f"P2 should NOT be inverted (cs_prev[2]=cs_P1=0, cs_P2=1), got 0x{p2_processed:04X}"
    )
    
    # Verify P3: all-ones, cs_prev[3]=cs_P2=1, cs_P3=0
    # Condition: all_ones && !(1 && 0) = 1 && !0 = 1 -> NOT invert
    p3_processed = (actual_addr_out >> 42) & 0x3FFF
    assert p3_processed == 0x3FFF, (
        f"P3 should NOT be inverted (cs_prev[3]=cs_P2=1, cs_P3=0), got 0x{p3_processed:04X}"
    )


# ✅ CRITICAL: Pytest wrapper function (required for HUD format)
def test_addr_decode_runner():
    """Pytest wrapper for Cocotb tests"""
    import os
    from pathlib import Path
    from cocotb_tools.runner import get_runner
    
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    
    # Use sources directory for the DUT (HUD format requirement)
    sources = [proj_path / "sources/addr_decode.sv"]
    
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="addr_decode",
        always=True,
    )
    
    runner.test(hdl_toplevel="addr_decode", test_module="test_addr_decode")


