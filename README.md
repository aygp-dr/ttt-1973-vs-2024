# TTT: 1973 vs 2024

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![C](https://img.shields.io/badge/C-1973%20K%26R-orange.svg)]()
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)]()

**A study in solved games: comparing Unix V4's learning tic-tac-toe (1973) with
a modern optimal implementation.**

## The Question

Tic-tac-toe is a solved game. With perfect play, every game ends in a draw.
The entire game tree contains only 255,168 possible games, reducible to far
fewer with symmetry.

So why did the Unix V4 programmers at Bell Labs write a tic-tac-toe that
*learns from experience*?

## The Numbers

| Approach | States | Storage | Perfect? |
|----------|--------|---------|----------|
| Full game tree | 5,478 | ~5 KB | Yes |
| Symmetry-reduced | 765 | ~765 bytes | Yes |
| Unix V4 learning | Variable | 268 bytes (ttt.k) | Eventually |
| Rule-based optimal | 0 | ~50 lines of code | Yes |

## The 1973 Approach

Unix V4's `ttt` (2,192 bytes) asks at startup:

```
Accumulated knowledge? y
268 'bits' of knowledge
```

It maintains `/usr/games/ttt.k`, updating it after each game. When it loses,
it remembers. The implementation is a form of reinforcement learning—
primitive by today's standards, but remarkable for 1973.

### Why Learning?

1. **Memory constraints**: A full lookup table was expensive in 1973
2. **Research interest**: Bell Labs was exploring AI concepts
3. **It's cooler**: A learning opponent is more interesting than a perfect one

## The 2024 Approach

Optimal tic-tac-toe can be implemented with simple rules (Newell & Simon, 1972):

1. Win if you can
2. Block opponent's win
3. Take center if available
4. Take a corner
5. Take any edge

This guarantees never losing in about 50 lines of C.

## Files

```
├── 1973/
│   ├── ttt.bin          # Unix V4 PDP-11 binary (from recovered tape)
│   ├── ttt.k            # Knowledge file (268 bytes of learned states)
│   └── analysis.md      # Binary analysis
├── 2024/
│   ├── ttt_optimal.c    # Rule-based perfect play
│   ├── ttt_lookup.c     # Lookup table approach
│   └── ttt_minimax.py   # Full game tree analysis
├── comparison/
│   └── results.md       # Head-to-head analysis
└── README.md
```

## Running

### Modern implementations

```bash
# Rule-based C version
make optimal
./ttt_optimal

# Python minimax (slow but complete)
python3 2024/ttt_minimax.py
```

### Original 1973 version (requires SimH)

```bash
pkg install open-simh
wget http://squoze.net/UNIX/v4/disk.rk
wget http://squoze.net/UNIX/v4/unix_v4.tap
pdp11 boot.ini
# Then: login root, /usr/games/ttt
```

## The Philosophical Point

Both approaches achieve perfect play (eventually). But they represent
different philosophies:

| 1973 | 2024 |
|------|------|
| Learn from mistakes | Encode all knowledge |
| Adaptive | Static |
| Memory-efficient | Computation-efficient |
| Interesting opponent | Boring opponent |

The Unix V4 approach is objectively "worse" at tic-tac-toe—it will lose
games while learning. But it's more *interesting*, and in 1973,
interestingness mattered.

## References

- [Unix V4 Games Analysis](https://github.com/aygp-dr/unix-v4)
- Newell, A. & Simon, H. (1972). Human Problem Solving
- [MENACE](https://en.wikipedia.org/wiki/MENACE) - Michie's 1961 matchbox learning machine

## License

MIT
