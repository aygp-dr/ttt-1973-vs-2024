# Unix V4 TTT Binary Analysis

## File Information

```
$ file ttt.bin
ttt.bin: PDP-11 executable

$ ls -la
-rwxr-xr-x  1 bin  2192 Jun 10 1974 ttt.bin
-rw-r--r--  1 bin   268 Jun 10 1974 ttt.k
```

## Extracted Strings

```
$ strings ttt.bin
Tic-Tac-Toe
Accumulated knowledge?
 'bits' of knowledge
new game
Illegal move
You win
I concede
I win
Draw
 'bits' returned
/usr/games/ttt.k
```

## Knowledge File Format

The `ttt.k` file is 268 bytes of binary data:

```
$ xxd ttt.k | head -10
00000000: 1d43 483f 623d 8a3c 783c 7d42 c542 9541  .CH?b=.<x<}B.B.A
00000010: 962d 9f42 a83e b02b c23c 322e 3330 4c2c  .-.B.>.+.<2.30L,
00000020: 3b40 633f 513f ce42 693f 3b2e            ;@c?Q?.Bi?;.
```

## Probable Data Structure

Based on the size and behavior, the knowledge file likely stores:

- Board state encodings (3^9 = 19,683 possible states)
- With heavy compression, only visited states stored
- Each entry probably contains:
  - Encoded board state (variable bits)
  - Value/weight for that position

### Estimated Format

```c
/* Speculative reconstruction */
struct knowledge_entry {
    unsigned short board_hash;  /* Compressed board state */
    char value;                 /* Win/lose/draw weight */
};
```

With 268 bytes, this could store roughly 89 three-byte entries,
which aligns with a learning system that stores "interesting" states
rather than the full game tree.

## Behavior Analysis

When losing:
```
I concede
134 'bits' returned
```

The "bits returned" updates the knowledge file. The number varies
based on the game played—more complex losses generate more learning.

## Comparison to Modern Approach

| Aspect | Unix V4 (1973) | Modern Lookup (2024) |
|--------|----------------|----------------------|
| Strategy | Learn from losses | Pre-computed optimal |
| Initial play | Suboptimal | Perfect |
| Storage | 268 bytes (grows) | ~765 bytes (fixed) |
| Improvement | Yes (over games) | No (already perfect) |

## Why Learning?

In 1973, the learning approach made sense:

1. **Memory scarcity**: 268 bytes vs 765 for full table
2. **Research value**: Bell Labs was interested in AI
3. **Engagement**: A learning opponent is more interesting
4. **Adaptability**: Could potentially learn player tendencies

The trade-off was accepting early losses in exchange for
long-term improvement—a design choice still relevant in
modern reinforcement learning systems.
