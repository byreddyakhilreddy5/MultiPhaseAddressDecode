# Multi-Phase Address Decode and Concatenation Logic Specification

## 📋 Quick Summary for AI Implementation

**Task:** Implement a multi-phase address decode and concatenation module in SystemVerilog.

**Module Name:** `addr_decode`

**Key Requirements:**
1. Process 4 phases of 14-bit addresses (P0, P1, P2, P3)
2. Conditionally invert each address phase based on all-ones detection and chip-select conditions
3. Concatenate processed addresses into 56-bit output (P3 MSB to P0 LSB)
4. Concatenate chip-selects into 4-bit output (P3 MSB to P0 LSB)
5. All logic is combinational (no clocking or state)

**Critical Constraint:** Address inversion is conditional - addresses are NOT inverted only when the address is all-ones AND either previous or current CS is deasserted.

---

## Module Interface

### Port Declaration

**Module Name:** `addr_decode`

**Ports:**
- `address_P0[13:0]` (input, 14-bit): Address for Phase 0
- `address_P1[13:0]` (input, 14-bit): Address for Phase 1
- `address_P2[13:0]` (input, 14-bit): Address for Phase 2
- `address_P3[13:0]` (input, 14-bit): Address for Phase 3
- `cs_P0` (input, 1-bit): Chip-select for Phase 0 (1 = asserted/active)
- `cs_P1` (input, 1-bit): Chip-select for Phase 1 (1 = asserted/active)
- `cs_P2` (input, 1-bit): Chip-select for Phase 2 (1 = asserted/active)
- `cs_P3` (input, 1-bit): Chip-select for Phase 3 (1 = asserted/active)
- `addr_out[55:0]` (output, 56-bit): Concatenated processed address output
- `cs_out[3:0]` (output, 4-bit): Concatenated chip-select output

### Signal Descriptions

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `address_P0[13:0]` | 14-bit | Input | Address for Phase 0 (LSB phase) |
| `address_P1[13:0]` | 14-bit | Input | Address for Phase 1 |
| `address_P2[13:0]` | 14-bit | Input | Address for Phase 2 |
| `address_P3[13:0]` | 14-bit | Input | Address for Phase 3 (MSB phase) |
| `cs_P0` | 1-bit | Input | Chip-select for Phase 0 (1 = active) |
| `cs_P1` | 1-bit | Input | Chip-select for Phase 1 (1 = active) |
| `cs_P2` | 1-bit | Input | Chip-select for Phase 2 (1 = active) |
| `cs_P3` | 1-bit | Input | Chip-select for Phase 3 (1 = active) |
| `addr_out[55:0]` | 56-bit | Output | Concatenated processed addresses: {P3, P2, P1, P0} |
| `cs_out[3:0]` | 4-bit | Output | Concatenated chip-selects: {P3, P2, P1, P0} |

---

## Purpose and Overview

This module processes a 4-phase address and chip-select interface. Each address phase is conditionally inverted based on:
1. Whether the address is all-ones (14'b11111111111111)
2. The state of the current phase chip-select signal
3. The state of the previous phase chip-select signal

After processing, the addresses and chip-selects are concatenated and presented as outputs. The logic is purely combinational with no clocking or state storage.

---

## Phase Relationships

The design operates on 4 phases (P0, P1, P2, P3) where:
- **P0** is the least significant phase (LSB)
- **P3** is the most significant phase (MSB)

### Previous Phase Chip-Select Definition

For each phase Pi, the previous phase chip-select (`cs_prev`) is defined as:

| Phase | Previous Phase CS | Definition |
|-------|-------------------|------------|
| P0 | `cs_prev[0]` | Always `1'b0` (no previous phase) |
| P1 | `cs_prev[1]` | `cs_P0` |
| P2 | `cs_prev[2]` | `cs_P1` |
| P3 | `cs_prev[3]` | `cs_P2` |

**Implementation:**
```
cs_prev[0] = 1'b0
cs_prev[1] = cs_P0
cs_prev[2] = cs_P1
cs_prev[3] = cs_P2
```

---

## Address Decoding Rules

### All-Ones Detection

For each phase Pi, detect if the address is all-ones:

**All-ones condition:**
```
address_Pi == 14'b11111111111111
```

**Implementation:**
```
all_ones[i] = &address_Pi  // Reduction AND operator
```

This is equivalent to checking if all 14 bits are 1.

### Conditional Inversion Rule

For each phase Pi, the processed address is determined by the following logic:

**Address is NOT inverted if and only if:**
1. The address for that phase is all-ones (`address_Pi == 14'b11111111111111`), AND
2. Either the previous phase CS or the current phase CS is deasserted (0)

**Formally:**
```
NOT invert if: (address_Pi == all_ones) AND NOT (cs_prev[Pi] AND cs_Pi)
```

**Address IS inverted in all other cases:**
- Bitwise inversion is applied across all 14 bits

### Per-Phase Processing Logic

For each phase Pi (i = 0, 1, 2, 3):

**⚠️ IMPORTANT: Use `assign` statements to ensure outputs are always defined:**

```systemverilog
// Detect all-ones
assign all_ones[i] = &address_Pi;

// Conditional inversion - MUST use assign with ternary operator
// This ensures the output is ALWAYS assigned a value (no X/Z states)
assign addr_phase_processed[i] = (all_ones[i] && !(cs_prev[i] && cs_Pi)) ?
                                  address_Pi :      // Do NOT invert
                                  ~address_Pi;      // Invert
```

**❌ DO NOT use this pattern (may leave outputs undefined):**
```systemverilog
// WRONG: If-else without assign may leave outputs undefined
if (all_ones[i] && !(cs_prev[i] && cs_Pi)) begin
    addr_phase_processed[i] = address_Pi;
end else begin
    addr_phase_processed[i] = ~address_Pi;
end
```

**✅ CORRECT: Always use `assign` with ternary operator for combinational logic:**
```systemverilog
assign addr_phase_processed[i] = (all_ones[i] && !(cs_prev[i] && cs_Pi)) ?
                                  address_Pi :      // Do NOT invert
                                  ~address_Pi;      // Invert
```

### Truth Table for Inversion Decision

| All-Ones? | cs_prev[Pi] | cs_Pi | Condition | Result |
|-----------|-------------|-------|-----------|--------|
| 0 | X | X | Not all-ones | **INVERT** |
| 1 | 0 | 0 | All-ones, both CS deasserted | **NO INVERT** |
| 1 | 0 | 1 | All-ones, prev=0, curr=1 | **NO INVERT** |
| 1 | 1 | 0 | All-ones, prev=1, curr=0 | **NO INVERT** |
| 1 | 1 | 1 | All-ones, both CS asserted | **INVERT** |

**Key Insight:** Address is NOT inverted only when it's all-ones AND at least one CS (previous or current) is deasserted.

---

## Output Formation

### Address Output Concatenation

After all phases are processed, concatenate the processed addresses in descending phase order:

**⚠️ CRITICAL: Use `assign` statement to ensure output is always defined:**

```systemverilog
assign addr_out[55:0] = {
    addr_phase_processed[3],  // P3: bits [55:42] (MSB)
    addr_phase_processed[2],  // P2: bits [41:28]
    addr_phase_processed[1],  // P1: bits [27:14]
    addr_phase_processed[0]   // P0: bits [13:0]  (LSB)
};
```

**All 56 bits of `addr_out` must be assigned - no undefined values allowed.**

**Bit Mapping:**
- `addr_out[55:42]` = `addr_phase_processed[3]` (P3, 14 bits)
- `addr_out[41:28]` = `addr_phase_processed[2]` (P2, 14 bits)
- `addr_out[27:14]` = `addr_phase_processed[1]` (P1, 14 bits)
- `addr_out[13:0]` = `addr_phase_processed[0]` (P0, 14 bits)

### Chip-Select Output Concatenation

Concatenate chip-selects in descending phase order:

**⚠️ CRITICAL: Use `assign` statement to ensure output is always defined:**

```systemverilog
assign cs_out[3:0] = {
    cs_P3,  // Bit [3] (MSB)
    cs_P2,  // Bit [2]
    cs_P1,  // Bit [1]
    cs_P0   // Bit [0] (LSB)
};
```

**All 4 bits of `cs_out` must be assigned - no undefined values allowed.**

**Bit Mapping:**
- `cs_out[3]` = `cs_P3`
- `cs_out[2]` = `cs_P2`
- `cs_out[1]` = `cs_P1`
- `cs_out[0]` = `cs_P0`

---

## Implementation Guidelines

### ⚠️ CRITICAL: Avoiding Undefined (X/Z) Values

**All outputs MUST be assigned in all cases to avoid undefined (X/Z) values:**

1. **Use `assign` statements for all outputs** - Never leave outputs unassigned
2. **Ensure all paths assign values** - Every conditional must have a value assigned
3. **Use combinational logic only** - No sequential logic that could leave outputs undefined
4. **Test that outputs are always driven** - All bits of `addr_out[55:0]` and `cs_out[3:0]` must have defined values

**Common mistake:** Using `if-else` without `else` clause, or incomplete conditional assignments that leave outputs undefined.

**Correct pattern:**
```systemverilog
// ✅ CORRECT: Always assigns a value
assign addr_phase_processed[i] = (condition) ? value1 : value2;

// ❌ WRONG: May leave output undefined
if (condition) begin
    addr_phase_processed[i] = value1;
end
// Missing else clause = undefined value!
```

### Required Internal Signals

**Arrays for phase processing:**
- `wire [13:0] addr_phase[0:3]` - Input addresses organized by phase
- `wire [13:0] addr_phase_processed[0:3]` - Processed addresses after conditional inversion
- `wire cs_phase[0:3]` - Chip-selects organized by phase
- `wire cs_prev[0:3]` - Previous phase chip-selects
- `wire all_ones[0:3]` - All-ones detection flags for each phase


---

## Examples

### Example 1: All-ones address with both CS deasserted

**Inputs:**
- `address_P1 = 14'b11111111111111` (all-ones)
- `cs_P0 = 1'b0` (previous phase CS deasserted)
- `cs_P1 = 1'b0` (current phase CS deasserted)

**Processing:**
- `all_ones[1] = 1` (address is all-ones)
- `cs_prev[1] = cs_P0 = 0`
- Condition: `all_ones[1] && !(cs_prev[1] && cs_P1) = 1 && !(0 && 0) = 1 && !0 = 1`
- **Result:** `addr_phase_processed[1] = address_P1` (NOT inverted)

### Example 2: All-ones address with both CS asserted

**Inputs:**
- `address_P1 = 14'b11111111111111` (all-ones)
- `cs_P0 = 1'b1` (previous phase CS asserted)
- `cs_P1 = 1'b1` (current phase CS asserted)

**Processing:**
- `all_ones[1] = 1` (address is all-ones)
- `cs_prev[1] = cs_P0 = 1`
- Condition: `all_ones[1] && !(cs_prev[1] && cs_P1) = 1 && !(1 && 1) = 1 && !1 = 0`
- **Result:** `addr_phase_processed[1] = ~address_P1` (INVERTED)

### Example 3: Non-all-ones address

**Inputs:**
- `address_P2 = 14'b00000000000001` (not all-ones)
- `cs_P1 = 1'b1`
- `cs_P2 = 1'b0`

**Processing:**
- `all_ones[2] = 0` (address is NOT all-ones)
- Condition: `all_ones[2] && !(cs_prev[2] && cs_P2) = 0 && ... = 0`
- **Result:** `addr_phase_processed[2] = ~address_P2` (INVERTED)

### Example 4: Complete Output Formation

**Inputs:**
- `address_P0 = 14'h0001`, `cs_P0 = 1'b1`
- `address_P1 = 14'h3FFF` (all-ones), `cs_P1 = 1'b0`, `cs_P0 = 1'b1`
- `address_P2 = 14'h2000`, `cs_P2 = 1'b1`
- `address_P3 = 14'h3FFF` (all-ones), `cs_P3 = 1'b1`, `cs_P2 = 1'b1`

**Processing:**
- P0: Not all-ones → `addr_processed[0] = ~14'h0001 = 14'h3FFE`
- P1: All-ones, `cs_prev[1]=1`, `cs_P1=0` → `addr_processed[1] = 14'h3FFF` (NOT inverted)
- P2: Not all-ones → `addr_processed[2] = ~14'h2000 = 14'h1FFF`
- P3: All-ones, `cs_prev[3]=1`, `cs_P3=1` → `addr_processed[3] = ~14'h3FFF = 14'h0000` (inverted)

**Outputs:**
- `addr_out[55:0] = {14'h0000, 14'h1FFF, 14'h3FFF, 14'h3FFE}`
- `cs_out[3:0] = {1'b1, 1'b1, 1'b0, 1'b1}`

---

## Verification Requirements

### Test Cases That Must Pass

1. **All-ones with both CS deasserted:**
   - Input: `address_Pi = all-ones`, `cs_prev[i] = 0`, `cs_Pi = 0`
   - Expected: `addr_processed[i] = address_Pi` (NOT inverted)

2. **All-ones with previous CS asserted, current deasserted:**
   - Input: `address_Pi = all-ones`, `cs_prev[i] = 1`, `cs_Pi = 0`
   - Expected: `addr_processed[i] = address_Pi` (NOT inverted)

3. **All-ones with previous CS deasserted, current asserted:**
   - Input: `address_Pi = all-ones`, `cs_prev[i] = 0`, `cs_Pi = 1`
   - Expected: `addr_processed[i] = address_Pi` (NOT inverted)

4. **All-ones with both CS asserted:**
   - Input: `address_Pi = all-ones`, `cs_prev[i] = 1`, `cs_Pi = 1`
   - Expected: `addr_processed[i] = ~address_Pi` (INVERTED)

5. **Non-all-ones address:**
   - Input: `address_Pi != all-ones` (any value)
   - Expected: `addr_processed[i] = ~address_Pi` (INVERTED, regardless of CS)

6. **Output concatenation:**
   - Verify `addr_out[55:42]` = processed P3
   - Verify `addr_out[41:28]` = processed P2
   - Verify `addr_out[27:14]` = processed P1
   - Verify `addr_out[13:0]` = processed P0
   - Verify `cs_out[3:0]` = {cs_P3, cs_P2, cs_P1, cs_P0}

7. **Previous phase CS calculation:**
   - Verify `cs_prev[0] = 0`
   - Verify `cs_prev[1] = cs_P0`
   - Verify `cs_prev[2] = cs_P1`
   - Verify `cs_prev[3] = cs_P2`

---

## Common Implementation Mistakes to Avoid

1. **❌ Wrong inversion condition:**
   - **Mistake:** Inverting when address is all-ones and both CS are deasserted
   - **Fix:** Address is NOT inverted when all-ones AND at least one CS is deasserted

2. **❌ Wrong previous phase CS:**
   - **Mistake:** Using wrong phase for `cs_prev` calculation
   - **Fix:** `cs_prev[i]` uses `cs_phase[i-1]` (except P0 which uses 0)

3. **❌ Wrong output concatenation order:**
   - **Mistake:** Concatenating P0 to P3 instead of P3 to P0
   - **Fix:** MSB is P3, LSB is P0: `{P3, P2, P1, P0}`

4. **❌ Missing all-ones detection:**
   - **Mistake:** Not checking for all-ones before applying inversion logic
   - **Fix:** Always check `&address_Pi` first

5. **❌ Using sequential logic:**
   - **Mistake:** Using clocked always blocks or registers
   - **Fix:** All logic must be combinational (assign statements or combinational always blocks)

---

## Summary Checklist for Implementation

- [ ] Module name is `addr_decode`
- [ ] Ports match specification exactly (4 address inputs, 4 CS inputs, 2 outputs)
- [ ] **All outputs are assigned using `assign` statements (no unassigned outputs)**
- [ ] **Every conditional has both true and false branches that assign values**
- [ ] Previous phase CS calculated correctly: `cs_prev[0]=0`, `cs_prev[i]=cs_phase[i-1]`
- [ ] All-ones detection implemented: `all_ones[i] = &addr_phase[i]`
- [ ] Conditional inversion logic correct: NOT invert if `all_ones && !(cs_prev && cs_phase)`
- [ ] All 4 phases processed (use generate loop)
- [ ] Address output concatenated correctly: `{P3, P2, P1, P0}` (56 bits total)
- [ ] CS output concatenated correctly: `{P3, P2, P1, P0}` (4 bits total)
- [ ] All logic is combinational (no clocks or registers)
- [ ] All code paths covered
- [ ] **No undefined (X/Z) values in any output - verify all outputs are always assigned**

---
