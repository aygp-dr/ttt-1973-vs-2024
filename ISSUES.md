# Project Issues

## Discovered During Development

### ttt-001: Source code not available for Unix V4 games
**Status:** open
**Priority:** low
**Type:** documentation

The Unix V4 tape contains only binaries for the games, not source code.
The games directory `/usr/games/` has executables but no corresponding
source in `/usr/source/`. We can only analyze via `strings` and behavior.

**Related:** The kernel source IS available in `/usr/sys/ken/` and `/usr/sys/dmr/`.

---

### ttt-002: TTT learning file format unknown
**Status:** open
**Priority:** medium
**Type:** research

The `ttt.k` file format is undocumented. Analysis shows:
- 268 bytes of binary data
- Updates after losses ("134 'bits' returned")
- Persists between sessions

Probable structure:
- Compressed board state encodings
- Win/lose/draw weights per state

**Next steps:**
- Disassemble PDP-11 binary to understand format
- Create decoder tool

---

### ttt-003: Makefile output directory issues
**Status:** resolved
**Priority:** low
**Type:** build

Build failed with no error output when targeting `2024/ttt_optimal`.
**Root cause:** Silent failure due to output path handling.
**Fix:** Build to `/tmp/` first, then copy.

---

### ttt-004: Symmetry reduction could be smaller
**Status:** open
**Priority:** low
**Type:** enhancement

Current analysis:
- 5,478 unique positions
- 765 with 8-fold symmetry

Could potentially reduce further:
- Consider X-first vs O-first equivalence
- Board rotation+reflection already handled
- Could get to ~400 states?

---

### ttt-005: Add web playground
**Status:** open
**Priority:** medium
**Type:** feature

Create a web-based comparison where users can:
1. Play against 1973-style learning AI
2. Play against 2024 optimal AI
3. See the difference in play quality

Technologies: WebAssembly for C version, vanilla JS for display.

---

### ttt-006: Document the philosophical point
**Status:** open
**Priority:** high
**Type:** documentation

The key insight deserves expansion:

> Unix V4's learning TTT is "worse" at the game but "better" as a product.
> It starts imperfect, loses games, but improves. A lookup table is
> perfect from move 1 but never changes.

This mirrors modern debates:
- Static rules vs machine learning
- Interpretable vs opaque systems
- "Correct" vs "interesting"

---

## Historical Research Needed

### ttt-007: Find original author
**Status:** open
**Priority:** low
**Type:** research

Who wrote the Unix V4 games? Candidates:
- Ken Thompson (kernel author, known game enthusiast)
- Dennis Ritchie (unlikely - focused on language/tools)
- Other Bell Labs employees?

Check Unix oral history archives.

---

### ttt-008: Compare with MENACE
**Status:** open
**Priority:** medium
**Type:** research

Donald Michie's MENACE (1961) used matchboxes and colored beads.
Unix V4 TTT uses a similar learning approach digitally.

Questions:
- Did the Unix author know of MENACE?
- How similar is the algorithm?
- Is ttt.k essentially digital matchboxes?
