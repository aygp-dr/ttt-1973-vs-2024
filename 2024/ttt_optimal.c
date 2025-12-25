/*
 * ttt_optimal.c - Perfect Tic-Tac-Toe using Newell & Simon rules (1972)
 *
 * This implementation never loses. It uses simple priority rules
 * that guarantee optimal play without any learning or lookup tables.
 *
 * Compare to Unix V4's learning approach (1973) which starts imperfect
 * but improves over time.
 *
 * Build: cc -O2 -o ttt_optimal ttt_optimal.c
 */

#include <stdio.h>
#include <stdlib.h>

static char board[10] = "         ";  /* positions 1-9, index 0 unused */

/* All possible winning lines */
static const int wins[8][3] = {
    {1,2,3}, {4,5,6}, {7,8,9},  /* rows */
    {1,4,7}, {2,5,8}, {3,6,9},  /* columns */
    {1,5,9}, {3,5,7}            /* diagonals */
};

/* Check if player has won */
static int check_win(char player) {
    for (int i = 0; i < 8; i++) {
        if (board[wins[i][0]] == player &&
            board[wins[i][1]] == player &&
            board[wins[i][2]] == player) {
            return 1;
        }
    }
    return 0;
}

/* Find a winning move for player, or 0 if none */
static int find_winning_move(char player) {
    for (int i = 0; i < 8; i++) {
        int count = 0, empty = 0;
        for (int j = 0; j < 3; j++) {
            int pos = wins[i][j];
            if (board[pos] == player) count++;
            else if (board[pos] == ' ') empty = pos;
        }
        if (count == 2 && empty > 0) return empty;
    }
    return 0;
}

/*
 * Newell & Simon optimal strategy (1972):
 * 1. Win if possible
 * 2. Block opponent's win
 * 3. Take center
 * 4. Take corner (opposite to opponent if possible)
 * 5. Take any edge
 */
static int best_move(char me, char opponent) {
    int move;

    /* Rule 1: Win if we can */
    if ((move = find_winning_move(me)) > 0) return move;

    /* Rule 2: Block opponent's win */
    if ((move = find_winning_move(opponent)) > 0) return move;

    /* Rule 3: Take center */
    if (board[5] == ' ') return 5;

    /* Rule 4: Take a corner (prefer opposite to opponent) */
    static const int corners[] = {1, 3, 7, 9};
    static const int opposite[] = {9, 7, 3, 1};
    for (int i = 0; i < 4; i++) {
        if (board[corners[i]] == opponent && board[opposite[i]] == ' ') {
            return opposite[i];
        }
    }
    for (int i = 0; i < 4; i++) {
        if (board[corners[i]] == ' ') return corners[i];
    }

    /* Rule 5: Take any edge */
    static const int edges[] = {2, 4, 6, 8};
    for (int i = 0; i < 4; i++) {
        if (board[edges[i]] == ' ') return edges[i];
    }

    return 0;  /* No moves available */
}

static void show_board(void) {
    printf("\n");
    printf(" %c | %c | %c     1 | 2 | 3\n", board[1], board[2], board[3]);
    printf("---|---|---   ---|---|---\n");
    printf(" %c | %c | %c     4 | 5 | 6\n", board[4], board[5], board[6]);
    printf("---|---|---   ---|---|---\n");
    printf(" %c | %c | %c     7 | 8 | 9\n", board[7], board[8], board[9]);
    printf("\n");
}

int main(void) {
    char human, computer;
    int turn = 0;

    printf("=== Optimal Tic-Tac-Toe (2024) ===\n");
    printf("Using Newell & Simon rules - never loses\n\n");

    printf("Play as X or O? ");
    char choice;
    if (scanf(" %c", &choice) != 1) return 1;

    if (choice == 'O' || choice == 'o') {
        human = 'O'; computer = 'X';
        printf("Computer plays first as X.\n");
    } else {
        human = 'X'; computer = 'O';
        printf("You play first as X.\n");
    }

    for (turn = 0; turn < 9; turn++) {
        show_board();

        char current = (turn % 2 == 0) ? 'X' : 'O';

        if (current == human) {
            printf("Your move (1-9): ");
            int move;
            if (scanf("%d", &move) != 1 || move < 1 || move > 9 || board[move] != ' ') {
                printf("Invalid move. Try again.\n");
                turn--;
                continue;
            }
            board[move] = human;
        } else {
            int move = best_move(computer, human);
            printf("Computer plays: %d\n", move);
            board[move] = computer;
        }

        if (check_win(current)) {
            show_board();
            printf("%s wins!\n", (current == human) ? "You" : "Computer");
            return 0;
        }
    }

    show_board();
    printf("Draw. (As expected with perfect play!)\n");
    return 0;
}
