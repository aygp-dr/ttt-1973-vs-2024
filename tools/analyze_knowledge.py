#!/usr/bin/env python3
"""
analyze_knowledge.py - Decode and visualize Unix V4 TTT knowledge file

The ttt.k file stores learned game states. This script attempts to
decode the format and visualize what the AI has learned.
"""

import struct
import sys
from pathlib import Path

def analyze_bytes(data: bytes):
    """Analyze byte patterns in the knowledge file."""
    print(f"=== Knowledge File Analysis ===")
    print(f"Total size: {len(data)} bytes")
    print()

    # Look for patterns
    print("=== Byte Frequency ===")
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1

    # Sort by frequency
    sorted_freq = sorted(freq.items(), key=lambda x: -x[1])[:20]
    for byte, count in sorted_freq:
        pct = count / len(data) * 100
        print(f"  0x{byte:02x} ({byte:3d}): {count:3d} times ({pct:5.1f}%)")

    print()

    # Value range analysis
    print("=== Value Ranges ===")
    print(f"  Min byte: {min(data)} (0x{min(data):02x})")
    print(f"  Max byte: {max(data)} (0x{max(data):02x})")
    print(f"  Mean: {sum(data)/len(data):.1f}")
    print()

    # Look for structure by trying different record sizes
    print("=== Record Size Analysis ===")
    for record_size in [2, 3, 4, 5, 6]:
        if len(data) % record_size == 0:
            num_records = len(data) // record_size
            print(f"  {record_size} bytes/record: {num_records} records")

    print()

def try_decode_board(value: int) -> str:
    """Try to decode a 16-bit value as a board state."""
    # Each cell: 0=empty, 1=X, 2=O
    # 9 cells, 3^9 = 19683, fits in 16 bits
    cells = []
    for _ in range(9):
        cells.append(value % 3)
        value //= 3
    cells.reverse()

    # Convert to visual
    symbols = ['.', 'X', 'O']
    board = [symbols[c] for c in cells]
    return f"{board[0]}{board[1]}{board[2]}|{board[3]}{board[4]}{board[5]}|{board[6]}{board[7]}{board[8]}"

def interpret_as_2byte_records(data: bytes):
    """Interpret as 2-byte records (board state only)."""
    print("=== Interpretation: 2-byte records ===")
    records = []
    for i in range(0, len(data) - 1, 2):
        val = struct.unpack_from("<H", data, i)[0]
        records.append(val)

    print(f"Found {len(records)} potential board states")
    print("\nFirst 20 decoded as boards:")
    for i, val in enumerate(records[:20]):
        if val < 19683:  # Valid board range
            board = try_decode_board(val)
            print(f"  {i:3d}: {val:5d} (0x{val:04x}) -> {board}")
        else:
            print(f"  {i:3d}: {val:5d} (0x{val:04x}) -> [invalid board]")
    print()

def interpret_as_3byte_records(data: bytes):
    """Interpret as 3-byte records (board + weight)."""
    print("=== Interpretation: 3-byte records (board + weight) ===")

    records = []
    for i in range(0, len(data) - 2, 3):
        board_val = struct.unpack_from("<H", data, i)[0]
        weight = struct.unpack_from("<b", data, i + 2)[0]  # signed
        records.append((board_val, weight))

    print(f"Found {len(records)} potential (board, weight) pairs")
    print("\nFirst 20 entries:")
    for i, (board_val, weight) in enumerate(records[:20]):
        if board_val < 19683:
            board = try_decode_board(board_val)
            print(f"  {i:3d}: board={board} weight={weight:+4d}")
        else:
            print(f"  {i:3d}: board=0x{board_val:04x} [invalid] weight={weight:+4d}")
    print()

    # Weight distribution
    weights = [r[1] for r in records]
    print(f"Weight statistics:")
    print(f"  Min: {min(weights)}")
    print(f"  Max: {max(weights)}")
    print(f"  Positive: {sum(1 for w in weights if w > 0)}")
    print(f"  Negative: {sum(1 for w in weights if w < 0)}")
    print(f"  Zero: {sum(1 for w in weights if w == 0)}")
    print()

def interpret_as_4byte_records(data: bytes):
    """Interpret as 4-byte records."""
    print("=== Interpretation: 4-byte records ===")

    records = []
    for i in range(0, len(data) - 3, 4):
        val = struct.unpack_from("<I", data, i)[0]
        records.append(val)

    print(f"Found {len(records)} records")
    print("First 10:")
    for i, val in enumerate(records[:10]):
        print(f"  {i}: 0x{val:08x}")
    print()

def hexdump(data: bytes, cols: int = 16, max_lines: int = 20):
    """Pretty hex dump."""
    print("=== Hex Dump ===")
    for i in range(0, min(len(data), cols * max_lines), cols):
        line = data[i:i + cols]
        hex_part = ' '.join(f'{b:02x}' for b in line)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in line)
        print(f"{i:04x}: {hex_part:<{cols*3}} {ascii_part}")
    if len(data) > cols * max_lines:
        print(f"... ({len(data) - cols * max_lines} more bytes)")
    print()

def main():
    if len(sys.argv) < 2:
        # Default to ttt.k in 1973/
        path = Path(__file__).parent.parent / "1973" / "ttt.k"
    else:
        path = Path(sys.argv[1])

    if not path.exists():
        print(f"Error: {path} not found")
        sys.exit(1)

    data = path.read_bytes()

    print(f"Analyzing: {path}")
    print("=" * 60)
    print()

    hexdump(data)
    analyze_bytes(data)
    interpret_as_2byte_records(data)
    interpret_as_3byte_records(data)
    interpret_as_4byte_records(data)

    print("=" * 60)
    print("CONCLUSION:")
    print("The most likely format is 3-byte records (board + signed weight)")
    print(f"with {len(data) // 3} learned positions.")
    print()
    print("The learning algorithm probably works like MENACE:")
    print("- Positive weights: favorable positions for computer")
    print("- Negative weights: positions leading to losses")
    print("- Computer chooses moves leading to highest-weight positions")

if __name__ == "__main__":
    main()
