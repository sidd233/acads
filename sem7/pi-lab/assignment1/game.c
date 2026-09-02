#include <stdio.h>

int INITIAL_STONES = 2;
int PITS = 6;

int state[14] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13};
int turn = 0;
int game_over = 0;

// function to draw the board on
// the terminal after each turn.
void draw_board()
{
    printf("\n");
    printf("                 Player 1's Pits\n\n");

    // Pit numbers
    printf("Pit Number:       ");
    for (int i = 1; i < 7; i++)
    {
        printf("%2d", i);

        if (i < 6)
            printf("    ");
    }

    printf("\n");

    // Number of stones
    printf("Stones:           ");
    for (int i = 1; i < 7; i++)
    {
        printf("%2d", state[i]);

        if (i < 6)
            printf(" <- ");
    }

    // TODO: Remove this after writing sowing code
    // index
    printf("\n");
    printf("index:            ");
    for (int i = 1; i < 7; i++)
    {
        printf("%2d", i);

        if (i < 6)
            printf("    ");
    }

    printf("\n\n");

    // Stores
    // TODO: remove indices
    printf("Stores:      (%d) [P1] %2d                       %2d [P2] (%d)\n",
           0, state[0], state[7], 7);

    printf("\n");

    // TODO: Remove this after writing sowing code
    // index
    printf("index:            ");
    for (int i = 13; i >= 8; i--)
    {
        printf("%2d", i);

        if (i < 14)
            printf("    ");
    }
    printf("\n");

    // Number of stones
    printf("Stones:           ");
    for (int i = 13; i >= 8; i--)
    {
        printf("%2d", state[i]);

        if (i > 8)
            printf(" -> ");
    }

    printf("\n");

    // Pit numbers
    printf("Pit Number:       ");
    for (int i = 1; i < 7; i++)
    {
        printf("%2d", i);

        if (i < 6)
            printf("    ");
    }

    printf("\n\n");

    printf("                 Player 2's Pits\n");

    printf("\n----------------------------------------------------\n");
}

// declare the winner and end the game
void end_game(const int winner)
{
    printf("---FINAL SCORES---\n");
    printf("Player 1 : %d\n",state[0]);
    printf("Player 2 : %d\n",state[7]);
    if (winner == 0)
        // draw
        printf("The game ended in a draw!\n");
    else
        // win
        printf("PLAYER %d HAS WON THE GAME!\n", winner);
    // game over
    game_over = 1;
    printf("--- GAME OVER ---\n");
}

// check if any side is empty and if it is then whose store is greater?
void check_win()
{
    // sum all stones on each side
    int player1_sum = 0;
    int player2_sum = 0;
    for (int i = 1; i < 7; i++)
        player1_sum += state[i];
    for (int i = 8; i < 14; i++)
        player2_sum += state[i];

    int player1_store = state[0];
    int player2_store = state[7];

    // score = store + leftover stones a/c to rules
    int player1_score = player1_store + player1_sum;
    int player2_score = player2_store + player2_sum;

    if (player1_sum == 0 || player2_sum == 0)
    {
        for (int i = 1; i < 7; i++)
            state[i] = 0;
        for (int i = 8; i < 14; i++)
            state[i] = 0;
        state[0] += player1_sum;
        state[7] += player2_sum;
        printf("---FINAL BOARD STATE---\n");
        draw_board();
        if (player1_score > player2_score)
            end_game(1);
        else if (player2_score > player1_score)
            end_game(2);
        else
            end_game(0);
    }
}

// main game loop
void game()
{
    int players_turn = 1;
    while (!game_over)
    {
        // taking input from player
        printf("Player %d must choose a pit: ", players_turn);
        int pit;

        // input validation
        if (scanf("%d", &pit) != 1)
        {
            printf("Invalid input. Please enter a number.\n");
            // no clue why the invalid character still clogs the stdin
            // removing this loop causes infinite error message
            while (getchar() != '\n')
                ;
            continue;
        }

        if (pit < 1 || pit > PITS)
        {
            printf("Invalid pit number. Choose again.\n");
            continue;
        }

        printf("Player %d chose pit %d.\n", players_turn, pit);

        // convert into index for state array
        int idx = (players_turn == 1) ? pit : 14 - pit;

        // find number of stones in the pit.
        int stones = state[idx];
        if (stones == 0)
        {
            printf("No stones in this pit. Pick another pit.\n");
            continue;
        }

        printf("Pit %d of Player %d has %d stones.\n", pit, players_turn, stones);
        printf("Distributing pit %d of Player %d...\n", pit, players_turn);

        printf("----------------------------------------------------\n");

        // counter clockwise distribution
        state[idx] = 0;
        int extra_turn = 0; // variable to set true if last stone lands on player's store
        int player_store_idx = (players_turn - 1) * 7;
        while (stones > 0)
        {
            idx--;

            // wrap around if going out of bounds
            if (idx == -1)
                idx = 13;

            // skip opponent's store
            if (idx == ((2 - players_turn) * 7))
                continue;

            // check for extra turn
            if (stones == 1 && idx == (player_store_idx))
                extra_turn = 1;

            // check for capture
            if (stones == 1 && state[idx] == 0 && idx >= (player_store_idx + 1) && idx <= (player_store_idx + 6))
            {
                printf("Last stone landed on an empty pit.\n");
                printf("Opposite pit and current stone were captured.\n");
                printf("----------------------------------------------------\n");
                state[player_store_idx] += state[14 - idx] + 1;
                state[14 - idx] = 0;
            }
            else
                state[idx]++;

            // next
            stones--;
        }

        // use extra turn
        if (extra_turn)
        {
            printf("Last stone landed on player's store.\n");
            printf("Player %d gets an extra turn.\n", players_turn);
            printf("----------------------------------------------------\n");
        }
        else
            players_turn = 3 - players_turn;

        draw_board();
        check_win();
    }
}

// init function
void init()
{
    printf("\n");
    printf(" __  __    _    _   _  ____    _    _        _    \n");
    printf("|  \\/  |  / \\  | \\ | |/ ___|  / \\  | |      / \\   \n");
    printf("| |\\/| | / _ \\ |  \\| | |     / _ \\ | |     / _ \\  \n");
    printf("| |  | |/ ___ \\| |\\  | |___ / ___ \\| |___ / ___ \\ \n");
    printf("|_|  |_/_/   \\_\\_| \\_|\\____/_/   \\_\\____//_/   \\_\\\n");
    printf("\n");

    printf("----------------------------------------------------\n");
    printf("Name     : Siddharth Narayan Mishra\n");
    printf("Roll No. : 123CS0189\n");
    printf("----------------------------------------------------");
    printf("\n");

    // initialise game state
    for (int i = 0; i < 14; i++)
        state[i] = INITIAL_STONES;
    state[0] = 0;
    state[7] = 0;
    turn = 0;
    game_over = 0;

    // first board draw
    draw_board();

    // start game
    game();
}

int main()
{
    init();
}