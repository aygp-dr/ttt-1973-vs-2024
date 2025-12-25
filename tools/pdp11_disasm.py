#!/usr/bin/env python3
"""
pdp11_disasm.py - Simple PDP-11 disassembler for Unix V4 binaries

The a.out format for PDP-11:
  Offset  Size  Description
  0x00    2     Magic number (0407 = OMAGIC, 0410 = NMAGIC, 0411 = ZMAGIC)
  0x02    2     Text segment size
  0x04    2     Data segment size
  0x06    2     BSS segment size
  0x08    2     Symbol table size
  0x0A    2     Entry point
  0x0C    2     Unused (stack size)
  0x0E    2     Flag (relocation stripped if non-zero)
  0x10    ...   Text segment
"""

import struct
import sys
from dataclasses import dataclass
from typing import List, Tuple

# PDP-11 Addressing Modes
MODES = [
    "Rn",           # 0: Register
    "(Rn)",         # 1: Register deferred
    "(Rn)+",        # 2: Autoincrement
    "@(Rn)+",       # 3: Autoincrement deferred
    "-(Rn)",        # 4: Autodecrement
    "@-(Rn)",       # 5: Autodecrement deferred
    "X(Rn)",        # 6: Index
    "@X(Rn)",       # 7: Index deferred
]

REGS = ["r0", "r1", "r2", "r3", "r4", "r5", "sp", "pc"]

# PDP-11 Instruction Set (partial)
OPCODES = {
    # Double operand
    0o01: ("mov", 2),
    0o02: ("cmp", 2),
    0o03: ("bit", 2),
    0o04: ("bic", 2),
    0o05: ("bis", 2),
    0o06: ("add", 2),
    0o11: ("movb", 2),
    0o12: ("cmpb", 2),
    0o13: ("bitb", 2),
    0o14: ("bicb", 2),
    0o15: ("bisb", 2),
    0o16: ("sub", 2),

    # Single operand (high 10 bits)
    0o0050: ("clr", 1),
    0o0051: ("com", 1),
    0o0052: ("inc", 1),
    0o0053: ("dec", 1),
    0o0054: ("neg", 1),
    0o0055: ("adc", 1),
    0o0056: ("sbc", 1),
    0o0057: ("tst", 1),
    0o0060: ("ror", 1),
    0o0061: ("rol", 1),
    0o0062: ("asr", 1),
    0o0063: ("asl", 1),

    # Branch instructions
    0o0004: ("br", "branch"),
    0o0010: ("bne", "branch"),
    0o0014: ("beq", "branch"),
    0o0020: ("bge", "branch"),
    0o0024: ("blt", "branch"),
    0o0030: ("bgt", "branch"),
    0o0034: ("ble", "branch"),
    0o1000: ("bpl", "branch"),
    0o1004: ("bmi", "branch"),
    0o1010: ("bhi", "branch"),
    0o1014: ("blos", "branch"),
    0o1020: ("bvc", "branch"),
    0o1024: ("bvs", "branch"),
    0o1030: ("bcc", "branch"),
    0o1034: ("bcs", "branch"),

    # JSR/RTS
    0o004: ("jsr", "jsr"),
    0o00020: ("rts", "rts"),

    # System calls
    0o104400: ("sys", "sys"),
}

@dataclass
class Instruction:
    addr: int
    raw: List[int]
    mnemonic: str
    operands: str
    comment: str = ""

def decode_operand(mode: int, reg: int, data: bytes, offset: int) -> Tuple[str, int]:
    """Decode a PDP-11 operand, return (string, bytes consumed)."""
    extra = 0

    if mode == 0:  # Register
        return REGS[reg], 0
    elif mode == 1:  # Register deferred
        return f"({REGS[reg]})", 0
    elif mode == 2:  # Autoincrement
        if reg == 7:  # PC - immediate
            if offset + 2 <= len(data):
                val = struct.unpack_from("<H", data, offset)[0]
                return f"${val:o}", 2
            return "(pc)+", 0
        return f"({REGS[reg]})+", 0
    elif mode == 3:  # Autoincrement deferred
        if reg == 7:  # PC - absolute
            if offset + 2 <= len(data):
                val = struct.unpack_from("<H", data, offset)[0]
                return f"@${val:o}", 2
        return f"@({REGS[reg]})+", 0
    elif mode == 4:  # Autodecrement
        return f"-({REGS[reg]})", 0
    elif mode == 5:  # Autodecrement deferred
        return f"@-({REGS[reg]})", 0
    elif mode == 6:  # Index
        if offset + 2 <= len(data):
            disp = struct.unpack_from("<h", data, offset)[0]
            if reg == 7:  # PC-relative
                return f"{disp:o}(pc)", 2
            return f"{disp:o}({REGS[reg]})", 2
        return f"?({REGS[reg]})", 0
    elif mode == 7:  # Index deferred
        if offset + 2 <= len(data):
            disp = struct.unpack_from("<h", data, offset)[0]
            return f"@{disp:o}({REGS[reg]})", 2
        return f"@?({REGS[reg]})", 0

    return "?", 0

def disassemble(data: bytes, base_addr: int = 0) -> List[Instruction]:
    """Disassemble PDP-11 binary."""
    instructions = []
    offset = 0

    while offset < len(data) - 1:
        addr = base_addr + offset
        word = struct.unpack_from("<H", data, offset)[0]
        raw = [word]
        consumed = 2

        mnemonic = "???"
        operands = ""
        comment = ""

        # Try to decode
        opcode_high = (word >> 12) & 0o17

        # Double operand instructions
        if opcode_high in [0o01, 0o02, 0o03, 0o04, 0o05, 0o06,
                          0o11, 0o12, 0o13, 0o14, 0o15, 0o16]:
            names = {0o01: "mov", 0o02: "cmp", 0o03: "bit", 0o04: "bic",
                    0o05: "bis", 0o06: "add", 0o11: "movb", 0o12: "cmpb",
                    0o13: "bitb", 0o14: "bicb", 0o15: "bisb", 0o16: "sub"}
            mnemonic = names[opcode_high]

            src_mode = (word >> 9) & 0o7
            src_reg = (word >> 6) & 0o7
            dst_mode = (word >> 3) & 0o7
            dst_reg = word & 0o7

            src_str, src_extra = decode_operand(src_mode, src_reg, data, offset + consumed)
            consumed += src_extra
            if src_extra:
                raw.append(struct.unpack_from("<H", data, offset + 2)[0])

            dst_str, dst_extra = decode_operand(dst_mode, dst_reg, data, offset + consumed)
            consumed += dst_extra
            if dst_extra:
                raw.append(struct.unpack_from("<H", data, offset + consumed - 2)[0])

            operands = f"{src_str}, {dst_str}"

        # Branch instructions
        elif (word >> 8) in [0o004, 0o010, 0o014, 0o020, 0o024, 0o030, 0o034,
                            0o100, 0o104, 0o110, 0o114, 0o120, 0o124, 0o130, 0o134]:
            branches = {
                0o004: "br", 0o010: "bne", 0o014: "beq", 0o020: "bge",
                0o024: "blt", 0o030: "bgt", 0o034: "ble", 0o100: "bpl",
                0o104: "bmi", 0o110: "bhi", 0o114: "blos", 0o120: "bvc",
                0o124: "bvs", 0o130: "bcc", 0o134: "bcs"
            }
            branch_op = word >> 8
            if branch_op in branches:
                mnemonic = branches[branch_op]
                disp = word & 0o377
                if disp & 0o200:
                    disp = disp - 256
                target = addr + 2 + (disp * 2)
                operands = f"{target:o}"

        # JSR
        elif (word >> 9) == 0o004:
            mnemonic = "jsr"
            reg = (word >> 6) & 0o7
            dst_mode = (word >> 3) & 0o7
            dst_reg = word & 0o7
            dst_str, dst_extra = decode_operand(dst_mode, dst_reg, data, offset + consumed)
            consumed += dst_extra
            operands = f"{REGS[reg]}, {dst_str}"

        # RTS
        elif (word >> 3) == 0o00020:
            mnemonic = "rts"
            operands = REGS[word & 0o7]

        # Single operand
        elif (word >> 6) in [0o0050, 0o0051, 0o0052, 0o0053, 0o0054, 0o0055,
                            0o0056, 0o0057, 0o0060, 0o0061, 0o0062, 0o0063,
                            0o1050, 0o1051, 0o1052, 0o1053, 0o1054, 0o1055,
                            0o1056, 0o1057, 0o1060, 0o1061, 0o1062, 0o1063]:
            singles = {
                0o0050: "clr", 0o0051: "com", 0o0052: "inc", 0o0053: "dec",
                0o0054: "neg", 0o0055: "adc", 0o0056: "sbc", 0o0057: "tst",
                0o0060: "ror", 0o0061: "rol", 0o0062: "asr", 0o0063: "asl",
                0o1050: "clrb", 0o1051: "comb", 0o1052: "incb", 0o1053: "decb",
                0o1054: "negb", 0o1055: "adcb", 0o1056: "sbcb", 0o1057: "tstb",
                0o1060: "rorb", 0o1061: "rolb", 0o1062: "asrb", 0o1063: "aslb"
            }
            op = word >> 6
            if op in singles:
                mnemonic = singles[op]
                dst_mode = (word >> 3) & 0o7
                dst_reg = word & 0o7
                dst_str, dst_extra = decode_operand(dst_mode, dst_reg, data, offset + consumed)
                consumed += dst_extra
                operands = dst_str

        # TRAP/EMT/SYS
        elif (word >> 8) == 0o104:
            trap_num = word & 0o377
            if trap_num == 0:
                mnemonic = "sys"
                operands = "indir"
            else:
                mnemonic = "sys"
                sys_names = {
                    1: "exit", 2: "fork", 3: "read", 4: "write", 5: "open",
                    6: "close", 7: "wait", 8: "creat", 9: "link", 10: "unlink",
                    11: "exec", 12: "chdir", 13: "time", 14: "mknod", 15: "chmod",
                    16: "chown", 17: "break", 18: "stat", 19: "seek", 20: "getpid"
                }
                operands = sys_names.get(trap_num, str(trap_num))

        # Halt/Wait/etc
        elif word == 0:
            mnemonic = "halt"

        instructions.append(Instruction(addr, raw, mnemonic, operands, comment))
        offset += consumed

    return instructions

def analyze_aout(filename: str):
    """Analyze a.out format binary."""
    with open(filename, "rb") as f:
        data = f.read()

    # Parse header
    magic = struct.unpack_from("<H", data, 0)[0]
    text_size = struct.unpack_from("<H", data, 2)[0]
    data_size = struct.unpack_from("<H", data, 4)[0]
    bss_size = struct.unpack_from("<H", data, 6)[0]
    sym_size = struct.unpack_from("<H", data, 8)[0]
    entry = struct.unpack_from("<H", data, 10)[0]

    print(f"=== PDP-11 a.out Header ===")
    print(f"Magic:       {magic:06o} ({'OMAGIC' if magic == 0o407 else 'NMAGIC' if magic == 0o410 else 'unknown'})")
    print(f"Text size:   {text_size} bytes ({text_size:o} octal)")
    print(f"Data size:   {data_size} bytes")
    print(f"BSS size:    {bss_size} bytes")
    print(f"Symbol size: {sym_size} bytes")
    print(f"Entry point: {entry:06o}")
    print()

    # Text segment starts at offset 16 (0x10)
    text_start = 16
    text_data = data[text_start:text_start + text_size]

    print(f"=== Disassembly (first 100 instructions) ===")
    instructions = disassemble(text_data, 0)

    for i, inst in enumerate(instructions[:100]):
        raw_str = " ".join(f"{w:06o}" for w in inst.raw)
        print(f"{inst.addr:06o}: {raw_str:20s} {inst.mnemonic:6s} {inst.operands}")

    print(f"\n... ({len(instructions)} total instructions)")

    return instructions

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: pdp11_disasm.py <binary>")
        sys.exit(1)

    analyze_aout(sys.argv[1])
