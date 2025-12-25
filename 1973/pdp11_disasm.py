#!/usr/bin/env python3
"""
PDP-11 Disassembler for Unix V4 a.out binaries
Focused on extracting control flow from ttt.bin
"""
import struct
import sys
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# PDP-11 registers
REGS = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc']

# Addressing modes
def decode_operand(mode: int, reg: int, data: bytes, offset: int) -> Tuple[str, int]:
    """Decode PDP-11 addressing mode, return (operand_str, bytes_consumed)"""
    if mode == 0:  # Register
        return REGS[reg], 0
    elif mode == 1:  # Register deferred
        return f"({REGS[reg]})", 0
    elif mode == 2:  # Autoincrement
        if reg == 7:  # PC - immediate
            if offset + 2 <= len(data):
                val = struct.unpack_from('<H', data, offset)[0]
                return f"${val:o}", 2
            return "$?", 0
        return f"({REGS[reg]})+", 0
    elif mode == 3:  # Autoincrement deferred
        if reg == 7:  # Absolute
            if offset + 2 <= len(data):
                val = struct.unpack_from('<H', data, offset)[0]
                return f"*${val:o}", 2
            return "*$?", 0
        return f"*({REGS[reg]})+", 0
    elif mode == 4:  # Autodecrement
        return f"-({REGS[reg]})", 0
    elif mode == 5:  # Autodecrement deferred
        return f"*-({REGS[reg]})", 0
    elif mode == 6:  # Index
        if offset + 2 <= len(data):
            idx = struct.unpack_from('<h', data, offset)[0]  # signed
            if reg == 7:  # PC-relative
                return f"{idx:o}(pc)", 2
            return f"{idx:o}({REGS[reg]})", 2
        return f"?({REGS[reg]})", 0
    elif mode == 7:  # Index deferred
        if offset + 2 <= len(data):
            idx = struct.unpack_from('<h', data, offset)[0]
            if reg == 7:
                return f"*{idx:o}(pc)", 2
            return f"*{idx:o}({REGS[reg]})", 2
        return f"*?({REGS[reg]})", 0
    return "???", 0

@dataclass
class Instruction:
    addr: int
    opcode: int
    mnemonic: str
    operands: str
    size: int
    is_branch: bool = False
    is_call: bool = False
    is_return: bool = False
    branch_target: Optional[int] = None
    comment: str = ""

def disassemble_one(data: bytes, offset: int, base_addr: int) -> Instruction:
    """Disassemble one instruction"""
    if offset + 2 > len(data):
        return Instruction(base_addr + offset, 0, ".word", "???", 2)

    word = struct.unpack_from('<H', data, offset)[0]
    addr = base_addr + offset
    size = 2
    mnemonic = "???"
    operands = ""
    is_branch = False
    is_call = False
    is_return = False
    branch_target = None

    # Decode instruction
    op = (word >> 12) & 0xF

    # Double operand instructions
    if op in [1, 2, 3, 4, 5, 6]:
        src_mode = (word >> 9) & 7
        src_reg = (word >> 6) & 7
        dst_mode = (word >> 3) & 7
        dst_reg = word & 7

        mnemonics = {1: 'mov', 2: 'cmp', 3: 'bit', 4: 'bic', 5: 'bis', 6: 'add'}
        mnemonic = mnemonics[op]

        src, src_bytes = decode_operand(src_mode, src_reg, data, offset + 2)
        size += src_bytes
        dst, dst_bytes = decode_operand(dst_mode, dst_reg, data, offset + size)
        size += dst_bytes
        operands = f"{src}, {dst}"

    elif op == 0o16:  # sub
        src_mode = (word >> 9) & 7
        src_reg = (word >> 6) & 7
        dst_mode = (word >> 3) & 7
        dst_reg = word & 7
        mnemonic = 'sub'
        src, src_bytes = decode_operand(src_mode, src_reg, data, offset + 2)
        size += src_bytes
        dst, dst_bytes = decode_operand(dst_mode, dst_reg, data, offset + size)
        size += dst_bytes
        operands = f"{src}, {dst}"

    elif op == 0o07:  # EIS: mul, div, ash, ashc
        pass

    elif op == 0:
        # Branch and single operand instructions
        if (word >> 8) == 0:
            # Misc instructions
            if word == 0:
                mnemonic = "halt"
            elif word == 1:
                mnemonic = "wait"
            elif word == 2:
                mnemonic = "rti"
                is_return = True
            elif word == 3:
                mnemonic = "bpt"
            elif word == 4:
                mnemonic = "iot"
            elif word == 5:
                mnemonic = "reset"
            elif word == 6:
                mnemonic = "rtt"
                is_return = True
        elif (word >> 6) == 0o001:  # JMP
            mnemonic = "jmp"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
            is_branch = True
        elif (word >> 6) == 0o003:  # SWAB
            mnemonic = "swab"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 8) == 0o001:  # BR
            mnemonic = "br"
            disp = word & 0xFF
            if disp > 127:
                disp -= 256
            branch_target = addr + 2 + disp * 2
            operands = f"{branch_target:o}"
            is_branch = True
        elif (word >> 8) == 0o002:  # BNE
            mnemonic = "bne"
            disp = word & 0xFF
            if disp > 127:
                disp -= 256
            branch_target = addr + 2 + disp * 2
            operands = f"{branch_target:o}"
            is_branch = True
        elif (word >> 8) == 0o003:  # BEQ
            mnemonic = "beq"
            disp = word & 0xFF
            if disp > 127:
                disp -= 256
            branch_target = addr + 2 + disp * 2
            operands = f"{branch_target:o}"
            is_branch = True
        elif (word >> 8) == 0o004:  # BGE
            mnemonic = "bge"
            disp = word & 0xFF
            if disp > 127:
                disp -= 256
            branch_target = addr + 2 + disp * 2
            operands = f"{branch_target:o}"
            is_branch = True
        elif (word >> 8) == 0o005:  # BLT
            mnemonic = "blt"
            disp = word & 0xFF
            if disp > 127:
                disp -= 256
            branch_target = addr + 2 + disp * 2
            operands = f"{branch_target:o}"
            is_branch = True
        elif (word >> 8) == 0o006:  # BGT
            mnemonic = "bgt"
            disp = word & 0xFF
            if disp > 127:
                disp -= 256
            branch_target = addr + 2 + disp * 2
            operands = f"{branch_target:o}"
            is_branch = True
        elif (word >> 8) == 0o007:  # BLE
            mnemonic = "ble"
            disp = word & 0xFF
            if disp > 127:
                disp -= 256
            branch_target = addr + 2 + disp * 2
            operands = f"{branch_target:o}"
            is_branch = True
        elif (word >> 6) == 0o050:  # CLR
            mnemonic = "clr"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o051:  # COM
            mnemonic = "com"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o052:  # INC
            mnemonic = "inc"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o053:  # DEC
            mnemonic = "dec"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o054:  # NEG
            mnemonic = "neg"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o055:  # ADC
            mnemonic = "adc"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o056:  # SBC
            mnemonic = "sbc"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o057:  # TST
            mnemonic = "tst"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o060:  # ROR
            mnemonic = "ror"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o061:  # ROL
            mnemonic = "rol"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o062:  # ASR
            mnemonic = "asr"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 6) == 0o063:  # ASL
            mnemonic = "asl"
            mode = (word >> 3) & 7
            reg = word & 7
            dst, dst_bytes = decode_operand(mode, reg, data, offset + 2)
            size += dst_bytes
            operands = dst
        elif (word >> 9) == 0o004:  # JSR
            mnemonic = "jsr"
            reg = (word >> 6) & 7
            mode = (word >> 3) & 7
            dst_reg = word & 7
            dst, dst_bytes = decode_operand(mode, dst_reg, data, offset + 2)
            size += dst_bytes
            operands = f"{REGS[reg]}, {dst}"
            is_call = True
        elif (word >> 3) == 0o00020:  # RTS
            mnemonic = "rts"
            operands = REGS[word & 7]
            is_return = True

    elif op == 0o10:  # Byte instructions: MOVB, CMPB, etc
        sub_op = (word >> 12) & 0xF
        if sub_op == 0o11:
            mnemonic = "movb"
        elif sub_op == 0o12:
            mnemonic = "cmpb"
        elif sub_op == 0o13:
            mnemonic = "bitb"
        elif sub_op == 0o14:
            mnemonic = "bicb"
        elif sub_op == 0o15:
            mnemonic = "bisb"
        src_mode = (word >> 9) & 7
        src_reg = (word >> 6) & 7
        dst_mode = (word >> 3) & 7
        dst_reg = word & 7
        src, src_bytes = decode_operand(src_mode, src_reg, data, offset + 2)
        size += src_bytes
        dst, dst_bytes = decode_operand(dst_mode, dst_reg, data, offset + size)
        size += dst_bytes
        operands = f"{src}, {dst}"

    elif (word >> 8) == 0o200:  # BPL
        mnemonic = "bpl"
        disp = word & 0xFF
        if disp > 127:
            disp -= 256
        branch_target = addr + 2 + disp * 2
        operands = f"{branch_target:o}"
        is_branch = True
    elif (word >> 8) == 0o201:  # BMI
        mnemonic = "bmi"
        disp = word & 0xFF
        if disp > 127:
            disp -= 256
        branch_target = addr + 2 + disp * 2
        operands = f"{branch_target:o}"
        is_branch = True
    elif (word >> 8) == 0o202:  # BHI
        mnemonic = "bhi"
        disp = word & 0xFF
        if disp > 127:
            disp -= 256
        branch_target = addr + 2 + disp * 2
        operands = f"{branch_target:o}"
        is_branch = True
    elif (word >> 8) == 0o203:  # BLOS
        mnemonic = "blos"
        disp = word & 0xFF
        if disp > 127:
            disp -= 256
        branch_target = addr + 2 + disp * 2
        operands = f"{branch_target:o}"
        is_branch = True
    elif (word >> 8) == 0o204:  # BVC
        mnemonic = "bvc"
        disp = word & 0xFF
        if disp > 127:
            disp -= 256
        branch_target = addr + 2 + disp * 2
        operands = f"{branch_target:o}"
        is_branch = True
    elif (word >> 8) == 0o205:  # BVS
        mnemonic = "bvs"
        disp = word & 0xFF
        if disp > 127:
            disp -= 256
        branch_target = addr + 2 + disp * 2
        operands = f"{branch_target:o}"
        is_branch = True
    elif (word >> 8) == 0o206:  # BCC/BHIS
        mnemonic = "bcc"
        disp = word & 0xFF
        if disp > 127:
            disp -= 256
        branch_target = addr + 2 + disp * 2
        operands = f"{branch_target:o}"
        is_branch = True
    elif (word >> 8) == 0o207:  # BCS/BLO
        mnemonic = "bcs"
        disp = word & 0xFF
        if disp > 127:
            disp -= 256
        branch_target = addr + 2 + disp * 2
        operands = f"{branch_target:o}"
        is_branch = True
    elif (word >> 8) == 0o104:  # EMT/TRAP
        if word & 0x100:
            mnemonic = "trap"
        else:
            mnemonic = "sys"  # EMT - Unix system calls
        operands = f"{word & 0xFF}"
        is_call = True

    # Unknown - show as data
    if mnemonic == "???":
        mnemonic = ".word"
        operands = f"{word:06o}"

    return Instruction(addr, word, mnemonic, operands, size,
                       is_branch, is_call, is_return, branch_target)

def parse_aout_header(data: bytes) -> Dict:
    """Parse Unix a.out header"""
    magic, text_size, data_size, bss_size, sym_size, entry, unused, reloc = \
        struct.unpack_from('<8H', data, 0)
    return {
        'magic': magic,
        'text_size': text_size,
        'data_size': data_size,
        'bss_size': bss_size,
        'sym_size': sym_size,
        'entry': entry,
        'reloc_suppressed': reloc
    }

def disassemble(data: bytes, start: int = 0x10, base: int = 0) -> List[Instruction]:
    """Disassemble entire text section"""
    instructions = []
    offset = start
    while offset < len(data):
        inst = disassemble_one(data, offset, base)
        instructions.append(inst)
        offset += inst.size
    return instructions

def find_strings(data: bytes) -> Dict[int, str]:
    """Find string constants in the binary"""
    strings = {}
    i = 0
    while i < len(data):
        if 0x20 <= data[i] < 0x7F:
            end = i
            while end < len(data) and 0x20 <= data[end] < 0x7F:
                end += 1
            if end - i >= 4:
                s = data[i:end].decode('ascii', errors='replace')
                strings[i] = s
                i = end
            else:
                i += 1
        else:
            i += 1
    return strings

def analyze_control_flow(instructions: List[Instruction]) -> Dict:
    """Analyze control flow and identify functions"""
    # Find all call targets (function entries)
    call_targets = set()
    branch_targets = set()

    for inst in instructions:
        if inst.is_call and inst.branch_target:
            call_targets.add(inst.branch_target)
        if inst.is_branch and inst.branch_target:
            branch_targets.add(inst.branch_target)

    # Find function boundaries (after RTS)
    function_starts = {0}  # Entry point
    function_starts.update(call_targets)

    return {
        'call_targets': sorted(call_targets),
        'branch_targets': sorted(branch_targets),
        'function_starts': sorted(function_starts)
    }

def main():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, 'ttt.bin'), 'rb') as f:
        data = f.read()

    header = parse_aout_header(data)
    print("=== Unix V4 a.out Header ===")
    print(f"Magic:      {header['magic']:06o} (should be 000407)")
    print(f"Text size:  {header['text_size']} bytes")
    print(f"Data size:  {header['data_size']} bytes")
    print(f"BSS size:   {header['bss_size']} bytes")
    print(f"Entry:      {header['entry']:06o}")
    print()

    # Text starts after 16-byte header
    text_start = 0x10
    text_end = text_start + header['text_size']

    print("=== Disassembly ===")
    instructions = disassemble(data, text_start, 0)

    # Annotate with strings
    strings = find_strings(data)

    # Build address-to-string map
    str_refs = {}
    for off, s in strings.items():
        str_refs[off] = s

    # Print with analysis
    cf = analyze_control_flow(instructions)

    for inst in instructions:
        prefix = ""
        if inst.addr in cf['function_starts']:
            prefix = "\n; === FUNCTION ==="
            print(prefix)
        elif inst.addr in cf['branch_targets']:
            prefix = "; --- label ---"
            print(prefix)

        # Check for string references
        comment = ""
        if "jsr" in inst.mnemonic and "pc" in inst.operands:
            comment = "  ; subroutine call"
        if inst.mnemonic == "sys":
            # Unix V4 system calls
            syscalls = {
                0: 'indir', 1: 'exit', 2: 'fork', 3: 'read', 4: 'write',
                5: 'open', 6: 'close', 8: 'creat', 9: 'link', 10: 'unlink',
                11: 'exec', 12: 'chdir', 15: 'chmod', 17: 'break', 19: 'seek',
                20: 'getpid', 21: 'mount', 23: 'setuid'
            }
            num = int(inst.operands) if inst.operands.isdigit() else 0
            if num in syscalls:
                comment = f"  ; {syscalls[num]}()"

        print(f"{inst.addr:06o}: {inst.opcode:06o}  {inst.mnemonic:6s} {inst.operands:20s}{comment}")

    print("\n=== Control Flow Summary ===")
    print(f"Possible functions at: {[f'{a:06o}' for a in cf['function_starts']]}")
    print(f"Branch targets: {len(cf['branch_targets'])}")

    # Print strings found
    print("\n=== Strings ===")
    for off, s in sorted(strings.items()):
        if len(s) > 3:
            print(f"  {off:06o}: \"{s}\"")

if __name__ == '__main__':
    main()
