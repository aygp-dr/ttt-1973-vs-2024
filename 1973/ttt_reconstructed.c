/*
 * ttt_reconstructed.c - Reconstructed Unix V4 Tic-Tac-Toe
 *
 * This is a speculative reconstruction based on:
 * 1. Binary analysis of /usr/games/ttt
 * 2. String extraction from the executable
 * 3. Behavior observation in SimH emulator
 * 4. Analysis of ttt.k knowledge file format
 * 5. Comparison with MENACE learning algorithm
 *
 * Original: Bell Laboratories, ~1973
 * Reconstruction: 2025
 *
 * Build (modern): cc -o ttt ttt_reconstructed.c
 * Build (K&R):    cc -traditional -o ttt ttt_reconstructed.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

#define EMPTY   0
#define HUMAN   1       /* X - human plays X */
#define COMPUTER 2      /* O - computer plays O */

#define MAX_KNOWLEDGE 200

/* Knowledge entry: packed board state + weight */
struct kentry {
    unsigned short board;       /* Encoded board state */
    signed char weight;         /* Position evaluation */
};

/* Global state */
static char board[9];                           /* Current board */
static struct kentry knowledge[MAX_KNOWLEDGE];  /* Learned positions */
static int nknowledge;                          /* Number of entries */
static int move_history[9];                     /* Moves this game */
static int nmoves;                              /* Number of moves */

/*
 * Encode board as 16-bit value
 * Each cell: 0=empty, 1=X, 2=O
 * Total: 3^9 = 19683 states (fits in 16 bits)
 */
static unsigned short
encode_board(void)
{
    unsigned short result;
    int i;

    result = 0;
    for (i = 0; i < 9; i++)
        result = result * 3 + board[i];
    return result;
}

/*
 * Check for winner
 * Returns: HUMAN, COMPUTER, or 0 (no winner)
 */
static int
check_winner(void)
{
    /* Winning lines: rows, columns, diagonals */
    static int lines[8][3] = {
        {0, 1, 2}, {3, 4, 5}, {6, 7, 8},  /* rows */
        {0, 3, 6}, {1, 4, 7}, {2, 5, 8},  /* cols */
        {0, 4, 8}, {2, 4, 6}              /* diagonals */
    };
    int i;

    for (i = 0; i < 8; i++) {
        if (board[lines[i][0]] != EMPTY &&
            board[lines[i][0]] == board[lines[i][1]] &&
            board[lines[i][1]] == board[lines[i][2]])
            return board[lines[i][0]];
    }
    return 0;
}

/*
 * Check if board is full
 */
static int
board_full(void)
{
    int i;
    for (i = 0; i < 9; i++)
        if (board[i] == EMPTY)
            return 0;
    return 1;
}

/*
 * Look up weight for current board position
 */
static int
lookup_weight(void)
{
    unsigned short code;
    int i;

    code = encode_board();
    for (i = 0; i < nknowledge; i++)
        if (knowledge[i].board == code)
            return knowledge[i].weight;
    return 0;  /* Unknown position */
}

/*
 * Find or create knowledge entry for board state
 */
static int
find_or_create(unsigned short code)
{
    int i;

    for (i = 0; i < nknowledge; i++)
        if (knowledge[i].board == code)
            return i;

    /* Create new entry */
    if (nknowledge < MAX_KNOWLEDGE) {
        knowledge[nknowledge].board = code;
        knowledge[nknowledge].weight = 0;
        return nknowledge++;
    }
    return -1;  /* Table full */
}

/*
 * Computer's move - MENACE-like algorithm
 *
 * For each possible move, look up the resulting position's weight.
 * Choose the move with highest weight. Randomize among equal weights.
 */
static int
compute_move(void)
{
    int best_move;
    int best_weight;
    int weight;
    int i;
    unsigned short code;

    best_move = -1;
    best_weight = -1000;

    for (i = 0; i < 9; i++) {
        if (board[i] == EMPTY) {
            /* Try this move */
            board[i] = COMPUTER;
            weight = lookup_weight();
            board[i] = EMPTY;

            if (weight > best_weight) {
                best_weight = weight;
                best_move = i;
            }
        }
    }

    /* If no knowledge, take first available (center, corner, edge) */
    if (best_move < 0 || best_weight == 0) {
        /* Prefer: center, corners, edges */
        static int priority[] = {4, 0, 2, 6, 8, 1, 3, 5, 7};
        for (i = 0; i < 9; i++)
            if (board[priority[i]] == EMPTY)
                return priority[i];
    }

    return best_move;
}

/*
 * Update knowledge after game ends
 *
 * This is the learning step - adjust weights based on outcome.
 * Similar to MENACE's bead adding/removing.
 */
static void
update_knowledge(int outcome)
{
    int i, idx;
    unsigned short code;
    int delta;

    /* Determine weight change based on outcome */
    if (outcome == COMPUTER) {
        delta = 3;      /* Win: reinforce these positions */
    } else if (outcome == 0) {
        delta = 1;      /* Draw: slight reinforcement */
    } else {
        delta = -2;     /* Loss: weaken these positions */
    }

    /* Replay and update each position the computer was in */
    memset(board, EMPTY, sizeof(board));

    for (i = 0; i < nmoves; i++) {
        /* Make move */
        if (i % 2 == 0)
            board[move_history[i]] = HUMAN;
        else
            board[move_history[i]] = COMPUTER;

        /* Update weight for computer's positions */
        if (i % 2 == 1) {
            code = encode_board();
            idx = find_or_create(code);
            if (idx >= 0) {
                knowledge[idx].weight += delta;
                /* Clamp to signed char range */
                if (knowledge[idx].weight > 127)
                    knowledge[idx].weight = 127;
                if (knowledge[idx].weight < -128)
                    knowledge[idx].weight = -128;
            }
        }
    }
}

/*
 * Display board
 */
static void
display_board(void)
{
    int i, j;
    char symbols[] = " XO";

    printf("\n");
    for (i = 0; i < 3; i++) {
        printf(" ");
        for (j = 0; j < 3; j++) {
            printf("%c", symbols[(int)board[i*3+j]]);
            if (j < 2) printf(" | ");
        }
        printf("\n");
        if (i < 2) printf("-----------\n");
    }
    printf("\n");
}

/*
 * Load knowledge from file
 */
static int
load_knowledge(const char *path)
{
    int fd;
    unsigned char buf[3];
    int n;

    fd = open(path, O_RDONLY);
    if (fd < 0)
        return 0;

    nknowledge = 0;
    while (read(fd, buf, 3) == 3 && nknowledge < MAX_KNOWLEDGE) {
        knowledge[nknowledge].board = buf[0] | (buf[1] << 8);
        knowledge[nknowledge].weight = (signed char)buf[2];
        nknowledge++;
    }

    close(fd);
    return nknowledge;
}

/*
 * Save knowledge to file
 */
static int
save_knowledge(const char *path)
{
    int fd;
    unsigned char buf[3];
    int i;

    fd = creat(path, 0644);
    if (fd < 0)
        return -1;

    for (i = 0; i < nknowledge; i++) {
        buf[0] = knowledge[i].board & 0xff;
        buf[1] = (knowledge[i].board >> 8) & 0xff;
        buf[2] = knowledge[i].weight;
        write(fd, buf, 3);
    }

    close(fd);
    return nknowledge;
}

/*
 * Main game loop
 */
int
main(void)
{
    char response[16];
    int move;
    int winner;
    int bits;
    const char *kpath = "ttt.k";

    printf("Tic-Tac-Toe\n");

    /* Load accumulated knowledge? */
    printf("Accumulated knowledge? ");
    fflush(stdout);
    if (fgets(response, sizeof(response), stdin) == NULL)
        return 0;

    if (response[0] == 'y' || response[0] == 'Y') {
        bits = load_knowledge(kpath);
        if (bits > 0)
            printf("%d 'bits' of knowledge\n", bits * 3);
    }

    /* Game loop */
    for (;;) {
        printf("new game\n");
        memset(board, EMPTY, sizeof(board));
        nmoves = 0;

        /* Play until game over */
        for (;;) {
            display_board();

            /* Human's turn (X) */
            printf("? ");
            fflush(stdout);
            if (fgets(response, sizeof(response), stdin) == NULL)
                goto done;

            move = response[0] - '1';
            if (move < 0 || move > 8 || board[move] != EMPTY) {
                printf("Illegal move\n");
                continue;
            }

            board[move] = HUMAN;
            move_history[nmoves++] = move;

            winner = check_winner();
            if (winner == HUMAN) {
                display_board();
                printf("You win\n");
                update_knowledge(HUMAN);
                break;
            }
            if (board_full()) {
                display_board();
                printf("Draw\n");
                update_knowledge(0);
                break;
            }

            /* Computer's turn (O) */
            move = compute_move();
            if (move < 0) {
                printf("I concede\n");
                update_knowledge(HUMAN);
                break;
            }

            board[move] = COMPUTER;
            move_history[nmoves++] = move;

            winner = check_winner();
            if (winner == COMPUTER) {
                display_board();
                printf("I win\n");
                update_knowledge(COMPUTER);
                break;
            }
        }

        /* Save knowledge */
        bits = save_knowledge(kpath);
        if (bits > 0)
            printf("%d 'bits' returned\n", bits * 3);
    }

done:
    return 0;
}
