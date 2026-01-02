import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import random

ADDR_WIDTH = 14
ALL_ONES = (1 << ADDR_WIDTH) - 1


def expected_addr(addr, cs_prev, cs_cur):
    """Reference model for one phase"""
    if addr == ALL_ONES and not (cs_prev and cs_cur):
        return addr
    else:
        return (~addr) & ALL_ONES


@cocotb.test()
async def test_addr_decode_registered(dut):
    """Test registered addr_decode with 1-cycle latency"""

    # Start clock (10 ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.rst_n.value = 0
    dut.address_P0.value = 0
    dut.address_P1.value = 0
    dut.address_P2.value = 0
    dut.address_P3.value = 0
    dut.cs_P0.value = 0
    dut.cs_P1.value = 0
    dut.cs_P2.value = 0
    dut.cs_P3.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1  # deassert reset

    await RisingEdge(dut.clk)

    # Run randomized tests
    for _ in range(200):

        addr = [random.randint(0, ALL_ONES) for _ in range(4)]
        cs   = [random.randint(0, 1) for _ in range(4)]

        # Drive inputs
        dut.address_P0.value = addr[0]
        dut.address_P1.value = addr[1]
        dut.address_P2.value = addr[2]
        dut.address_P3.value = addr[3]

        dut.cs_P0.value = cs[0]
        dut.cs_P1.value = cs[1]
        dut.cs_P2.value = cs[2]
        dut.cs_P3.value = cs[3]

        # Capture expected values (for NEXT cycle)
        cs_prev = [0, cs[0], cs[1], cs[2]]

        exp_addr = [
            expected_addr(addr[i], cs_prev[i], cs[i])
            for i in range(4)
        ]

        expected_addr_out = (
            (exp_addr[3] << 42) |
            (exp_addr[2] << 28) |
            (exp_addr[1] << 14) |
            (exp_addr[0] << 0)
        )

        expected_cs_out = (
            (cs[3] << 3) |
            (cs[2] << 2) |
            (cs[1] << 1) |
            (cs[0] << 0)
        )

        # Wait 1 cycle (registered output)
        await RisingEdge(dut.clk)

        # Check outputs
        assert dut.addr_out.value.integer == expected_addr_out, (
            f"\nADDR MISMATCH\n"
            f"addr = {addr}\n"
            f"cs   = {cs}\n"
            f"exp  = {hex(expected_addr_out)}\n"
            f"got  = {hex(dut.addr_out.value.integer)}"
        )

        assert dut.cs_out.value.integer == expected_cs_out, (
            f"\nCS MISMATCH\n"
            f"exp = {bin(expected_cs_out)}\n"
            f"got = {bin(dut.cs_out.value.integer)}"
        )

    dut._log.info("All registered addr_decode tests PASSED ✅")


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

