# TTT: 1973 vs 2024

CC = cc
CFLAGS = -O2 -Wall

.PHONY: all clean test analysis

all: 2024/ttt_optimal

2024/ttt_optimal: 2024/ttt_optimal.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f 2024/ttt_optimal

test: 2024/ttt_optimal
	@echo "Testing optimal implementation..."
	@echo "X5\n1\n9\n3\n7\n2" | ./2024/ttt_optimal || true

analysis:
	@echo "=== Game Tree Analysis ==="
	python3 2024/ttt_minimax.py

# Analyze the 1973 binary
analyze-1973:
	@echo "=== Unix V4 TTT Binary Analysis ==="
	@file 1973/ttt.bin
	@echo "\nStrings:"
	@strings 1973/ttt.bin
	@echo "\nKnowledge file (ttt.k):"
	@xxd 1973/ttt.k | head -10
	@echo "..."
	@wc -c 1973/ttt.k

# Size comparison
sizes:
	@echo "=== Size Comparison ==="
	@echo "1973 (PDP-11):"
	@ls -l 1973/ttt.bin 1973/ttt.k
	@echo "\n2024 (x86-64):"
	@ls -l 2024/ttt_optimal 2>/dev/null || echo "  (not built yet - run 'make')"
	@wc -c 2024/ttt_optimal.c 2024/ttt_minimax.py
