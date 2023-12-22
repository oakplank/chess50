from piecemoves import move_piece, is_in_check, is_game_over, find_king, is_legal_move, perform_castling
import copy

# CLI Chess Game
# Unicode representations for chess pieces and empty squares
unicode_pieces = {
    'br': '♜', 'bn': '♞', 'bb': '♝', 'bq': '♛', 'bk': '♚', 'bp': '♟︎',
    'wr': '♖', 'wn': '♘', 'wb': '♗', 'wq': '♕', 'wk': '♔', 'wp': '♙',
    None: '  '  # To be replaced with checkerboard pattern
}

# Initial board setup
current_board_state = [
    ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
    ['bp'] * 8,
    [None] * 8,
    [None] * 8,
    [None] * 8,
    [None] * 8,
    ['wp'] * 8,
    ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr']
]

def display_board(board_state):
    # Add two spaces before the column headers
    header = ' ' * 4 + '   '.join('abcdefgh') + '  '
    print(header)
    
    # Print the top border of the board
    print('  +' + '---+' * 8)
    
    # Print each row of the board
    for i, row in enumerate(board_state):
        # Start the row with the row number and an extra space
        row_str = f"{8 - i} |"
        
        # For each square in the row, add the piece or the colored square
        for j, piece in enumerate(row):
            char = unicode_pieces[piece] if piece else get_square_color(i, j)
            row_str += f" {char} |"
        
        # Print the row with an extra leading space for alignment
        print(row_str)
        
        # Print the border below the row
        print('  +' + '---+' * 8)
    
    # Print the bottom header with two extra spaces for alignment
    print(header)


def get_square_color(row, col):
    # Use a full block for dark squares and a space for light squares
    return '█' if (row + col) % 2 else ' '


def get_user_move():
    while True:
        user_input = input("Enter your move: ").lower().strip()
        if user_input == 'reset':
            return 'reset', None
        
        # Normalize the input by removing ' to ' if present
        normalized_input = user_input.replace(' to ', '')

        # Check if the normalized input is exactly 4 characters (e.g., 'e2e4')
        if len(normalized_input) == 4 and all(char.isalnum() for char in normalized_input):
            start_pos = normalized_input[:2]
            end_pos = normalized_input[2:]
            return start_pos, end_pos
        if user_input in ['e1g1', 'e1c1', 'e8g8', 'e8c8']:
            return user_input, None
        else:
            print("Invalid input. Please enter your move in the format 'e2e4' or 'e2 to e4'.")


def convert_position(pos):
    # Converts algebraic notation to a tuple of array indices (row, column)
    row = 8 - int(pos[1])  # Rows are numbered from 1 to 8
    column = ord(pos[0]) - ord('a')  # Columns are labeled from 'a' to 'h'
    return (row, column)


def process_move(from_position, to_position, board_state, current_player, last_move):
    # Make the move temporarily
    temp_board = copy.deepcopy(board_state)
    move_piece(temp_board, from_position, to_position)

    # Check if the opponent is now in check
    opponent = 'b' if current_player == 'w' else 'w'
    opponent_king_position = find_king(temp_board, opponent)

    if is_in_check(opponent_king_position, temp_board):
        print("Check!")
    elif is_in_check(find_king(temp_board, current_player), temp_board):
        print("Illegal move: cannot leave or place own king in check.")
        return False  # Illegal move

    # Confirm and make the actual move
    move_piece(board_state, from_position, to_position)
    return True

def reset_game():
    global current_board_state
    current_board_state = [
        ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
        ['bp'] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        ['wp'] * 8,
        ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr']
    ]
    print("Game reset.")

# Main Game Loop

def main():
    global current_board_state
    current_player = 'w'  # White starts the game
    last_move = None  # Initialize last_move
    print("Welcome to Chess!")
    print("Enter moves in algebraic notation or verbose notation (e.g., 'e2e4' or 'e2 to e4').")
    print("Enter 'reset' to reset the game.")

    while not is_game_over(current_board_state, current_player, last_move):
        display_board(current_board_state)
        
        print(f"{current_player.upper()}'s turn.")
        user_move = get_user_move()

        # Handle reset command
        if user_move[0] == 'reset':
            reset_game()
            current_player = 'w'
            continue

        from_move, to_move = user_move
        if to_move is None:  # This indicates a special move like castling
            if not handle_special_move(from_move, current_board_state, current_player):
                print("Invalid special move. Please try again.")
                continue
        else:
            from_row, from_col = convert_position(from_move)
            to_row, to_col = convert_position(to_move)
            piece_code = current_board_state[from_row][from_col]

            if is_legal_move((from_row, from_col), (to_row, to_col), current_board_state, current_player, last_move):
                # Update last_move before processing the current move
                last_move = {
                    'piece_code': piece_code,
                    'from_position': (from_row, from_col),
                    'to_position': (to_row, to_col)
                }

                if not process_move((from_row, from_col), (to_row, to_col), current_board_state, current_player, last_move):
                    print("Invalid move. Please try again.")
                    continue

                # Toggle player after a successful move
                current_player = 'b' if current_player == 'w' else 'w'
            else:
                print("Invalid move. Please try again.")

    print("Game over")

def handle_special_move(move, board_state, player):
    if move in ['e1g1', 'e1c1', 'e8g8', 'e8c8']:
        return perform_castling(move, board_state, player)
    return False

if __name__ == '__main__':
    main()