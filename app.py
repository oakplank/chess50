import copy

# CLI Chess Game
# Unicode representations for chess pieces and empty squares
unicode_pieces = {
    'br': '♜', 'bn': '♞', 'bb': '♝', 'bq': '♛', 'bk': '♚', 'bp': '♟︎',
    'wr': '♖', 'wn': '♘', 'wb': '♗', 'wq': '♕', 'wk': '♔', 'wp': '♙',
    None: '  ' 
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

# Tracking castling pieces movement
pieces_moved = {
    'wk': False, 'wr1': False, 'wr2': False,
    'bk': False, 'br1': False, 'br2': False
}


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

# Piece movement functions
    
def is_first_move(position, board_state):
    row, col = position
    piece = board_state[row][col]

    if piece and piece[1] == 'p':  # Check if it's a pawn
        if piece[0] == 'w' and row == 6:  # White pawn on its starting row
            return True
        elif piece[0] == 'b' and row == 1:  # Black pawn on its starting row
            return True

    return False


def get_pawn_moves(start_position, board_state, is_first_move, last_move):
    '''Returns a list of valid moves for a pawn given the current board state.'''
    moves = []
    direction = -1 if board_state[start_position[0]][start_position[1]].startswith('w') else 1
    row, col = start_position

    # Forward move
    forward_row = row + direction
    if 0 <= forward_row < 8 and board_state[forward_row][col] is None:
        moves.append((forward_row, col))
        if is_first_move:
            double_forward_row = forward_row + direction
            if 0 <= double_forward_row < 8 and board_state[double_forward_row][col] is None:
                moves.append((double_forward_row, col))

    # Diagonal captures including en passant
    for diagonal_col in [col - 1, col + 1]:
        if 0 <= diagonal_col < 8:
            diagonal_row = row + direction
            target_piece = board_state[diagonal_row][diagonal_col]

            if target_piece and target_piece[0] != board_state[row][col][0]:
                moves.append((diagonal_row, diagonal_col))

            elif not target_piece and last_move:
                # Adjusted Conditions for En Passant
                condition_1 = last_move and last_move['piece_code'][1] == 'p' and abs(last_move['from_position'][0] - last_move['to_position'][0]) == 2
                condition_2 = abs(last_move['to_position'][1] - col) == 1  # Adjacent column
                condition_3 = (direction == -1 and row == 3) or (direction == 1 and row == 4)
                condition_4 = abs(diagonal_col - col) == 1  # Diagonal to adjacent column
                condition_5 = diagonal_col == last_move['to_position'][1]  # Diagonal towards last move's pawn

                if condition_1 and condition_2 and condition_3 and condition_4 and condition_5:
                    en_passant_capture_row = row  # The row of the captured pawn
                    en_passant_capture_col = diagonal_col  # The column of the captured pawn
                    board_state[en_passant_capture_row][en_passant_capture_col] = None  # Remove the captured pawn
                    moves.append((diagonal_row, diagonal_col))  # Add en passant move
    return moves


def get_knight_moves(start_position, board_state):
    '''Returns a list of valid moves for a knight given the current board state.'''
    moves = []
    directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
    start_piece = board_state[start_position[0]][start_position[1]]

    for direction in directions:
        row = start_position[0] + direction[0]
        col = start_position[1] + direction[1]

        if 0 <= row < 8 and 0 <= col < 8:
            target_piece = board_state[row][col]
            if target_piece is None or target_piece[0] != start_piece[0]:
                moves.append((row, col))
    return moves


def get_bishop_moves(start_position, board_state):
    '''Returns a list of valid moves for a bishop given the current board state.'''
    moves = []
    directions = [(1, 1), (1, -1), (-1, -1), (-1, 1)]  # diagonal directions
    start_piece = board_state[start_position[0]][start_position[1]]

    for direction in directions:
        for i in range(1, 8):
            row = start_position[0] + direction[0] * i
            col = start_position[1] + direction[1] * i

            if not (0 <= row < 8 and 0 <= col < 8):
                break

            target_piece = board_state[row][col]
            if target_piece is None:
                moves.append((row, col))
            else:
                if target_piece[0] != start_piece[0]:
                    moves.append((row, col))
                break
    return moves


def get_rook_moves(start_position, board_state):
    '''Returns a list of valid moves for a rook given the current board state.'''
    moves = []
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # down, up, right, left
    start_piece = board_state[start_position[0]][start_position[1]]

    for direction in directions:
        for i in range(1, 8):
            row = start_position[0] + direction[0] * i
            col = start_position[1] + direction[1] * i

            if not (0 <= row < 8 and 0 <= col < 8):
                break

            target_piece = board_state[row][col]
            if target_piece is None:
                moves.append((row, col))
            else:
                if target_piece[0] != start_piece[0]:  # Capture if it's an opponent's piece
                    moves.append((row, col))
                break
    return moves


def get_queen_moves(start_position, board_state):
    '''Returns a list of valid moves for a queen given the current board state.'''
    # Combine the moves of a rook and a bishop
    return get_rook_moves(start_position, board_state) + get_bishop_moves(start_position, board_state)


def get_king_moves(start_position, board_state):
    '''Returns a list of valid moves for a king given the current board state.'''
    moves = []
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, -1), (-1, 1)]
    start_piece = board_state[start_position[0]][start_position[1]]

    for direction in directions:
        row = start_position[0] + direction[0]
        col = start_position[1] + direction[1]

        if 0 <= row < 8 and 0 <= col < 8:
            target_piece = board_state[row][col]
            if target_piece is None or target_piece[0] != start_piece[0]:
                moves.append((row, col))
    return moves


def is_move_valid(start_position, end_position, board_state):
    '''Returns True if the move is valid, False otherwise.'''
    piece = board_state[start_position[0]][start_position[1]]
    temp_board = copy.deepcopy(board_state)
    move_piece(temp_board, start_position, end_position)
    king_position = find_king(temp_board, piece[0])
    return not is_in_check(king_position, temp_board)


def move_piece(board, from_index, to_index):
    '''Moves a piece from the from_index to the to_index on the board.'''
    global pieces_moved
    piece = board[from_index[0]][from_index[1]]
    captured_piece = board[to_index[0]][to_index[1]]

    board[from_index[0]][from_index[1]] = None
    board[to_index[0]][to_index[1]] = piece

    # Update pieces_moved flag for kings and rooks
    if piece in ['wk', 'wr', 'bk', 'br']:
        if piece in ['wk', 'bk']:  # Kings
            pieces_moved[piece] = True
        elif piece in ['wr', 'br']:  # Rooks
            rook_index = '1' if from_index[1] == 0 else '2'
            pieces_moved[piece + rook_index] = True

    return captured_piece


def is_legal_move(from_position, to_position, board_state, player, last_move):
    from_row, from_col = from_position
    to_row, to_col = to_position
    piece = board_state[from_row][from_col]

    # Ensure a piece is selected and it belongs to the current player
    if piece is None or piece[0] != player:
        return False

    # Determine the type of the piece and get its valid moves
    valid_moves = []
    if piece[1] == 'p':  # Pawn
        valid_moves = get_pawn_moves(from_position, board_state, is_first_move(from_position, board_state), last_move)
    elif piece[1] == 'n':  # Knight
        valid_moves = get_knight_moves(from_position, board_state)
    elif piece[1] == 'b':  # Bishop
        valid_moves = get_bishop_moves(from_position, board_state)
    elif piece[1] == 'r':  # Rook
        valid_moves = get_rook_moves(from_position, board_state)
    elif piece[1] == 'q':  # Queen
        valid_moves = get_queen_moves(from_position, board_state)
    elif piece[1] == 'k':  # King
        valid_moves = get_king_moves(from_position, board_state)

    # Check if the to_position is in the list of valid moves
    return (to_row, to_col) in valid_moves


def is_in_check(king_position, board_state):
    '''Returns True if the king is in check, False otherwise.'''
    king_row, king_col = king_position
    king_piece = board_state[king_row][king_col]
    opponent = 'b' if king_piece[0] == 'w' else 'w'

    # Directions for rooks, bishops, and queens
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1),  # Rook moves
                  (1, 1), (1, -1), (-1, -1), (-1, 1)]  # Bishop moves

    # Check for threats from rooks, bishops, and queens
    for d_row, d_col in directions:
        r, c = king_row, king_col
        while 0 <= r < 8 and 0 <= c < 8:
            r, c = r + d_row, c + d_col
            if 0 <= r < 8 and 0 <= c < 8 and board_state[r][c]:
                if board_state[r][c][0] == opponent:
                    if (abs(d_row) + abs(d_col) == 1 and board_state[r][c][1] in ['r', 'q']) or \
                       (abs(d_row) + abs(d_col) == 2 and board_state[r][c][1] in ['b', 'q']):
                        return True
                break

    # Check for threats from knights
    knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    for d_row, d_col in knight_moves:
        r, c = king_row + d_row, king_col + d_col
        if 0 <= r < 8 and 0 <= c < 8 and board_state[r][c] and board_state[r][c] == opponent + 'n':
            return True

    # Check for threats from pawns
    pawn_directions = [(-1, -1), (-1, 1)] if opponent == 'w' else [(1, -1), (1, 1)]
    for d_row, d_col in pawn_directions:
        r, c = king_row + d_row, king_col + d_col
        if 0 <= r < 8 and 0 <= c < 8 and board_state[r][c] and board_state[r][c] == opponent + 'p':
            return True

    # Check for threats from the enemy king (not common but possible in some cases)
    king_moves = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, -1), (-1, 1)]
    for d_row, d_col in king_moves:
        r, c = king_row + d_row, king_col + d_col
        if 0 <= r < 8 and 0 <= c < 8 and board_state[r][c] and board_state[r][c] == opponent + 'k':
            return True

    return False


def has_legal_moves(board_state, player, last_move):
    # Check for any legal moves for all pieces of the given player
    for row in range(8):
        for col in range(8):
            if board_state[row][col] and board_state[row][col].startswith(player):
                if piece_has_legal_moves((row, col), board_state, player, last_move):
                    return True
    return False

def piece_has_legal_moves(start_position, board_state, player, last_move):
    piece = board_state[start_position[0]][start_position[1]]
    if not piece:
        return False

    # Get all potential moves for the piece
    potential_moves = get_potential_moves(start_position, piece, board_state, last_move)
    # Check if any of the potential moves are legal
    for end_position in potential_moves:
        if is_legal_move(start_position, end_position, board_state, player, last_move):
            # Simulate the move and check if it leaves the king in check
            temp_board = copy.deepcopy(board_state)
            move_piece(temp_board, start_position, end_position)
            king_position = find_king(temp_board, player)
            if not is_in_check(king_position, temp_board):
                return True
    return False


def get_potential_moves(start_position, piece, board_state, last_move):
    '''Returns a list of potential moves for the given piece.'''
    if piece[1] == 'p':  # Pawn
        return get_pawn_moves(start_position, board_state, is_first_move(start_position, board_state), last_move)
    elif piece[1] == 'n':  # Knight
        return get_knight_moves(start_position, board_state)
    elif piece[1] == 'b':  # Bishop
        return get_bishop_moves(start_position, board_state)
    elif piece[1] == 'r':  # Rook
        return get_rook_moves(start_position, board_state)
    elif piece[1] == 'q':  # Queen
        return get_queen_moves(start_position, board_state)
    elif piece[1] == 'k':  # King
        return get_king_moves(start_position, board_state)
    else:
        return []  # For an unrecognized piece, return an empty list



def is_path_clear(start_position, end_position, board_state):
    '''Returns True if there are no pieces between the start and end positions, False otherwise.'''
    start_row, start_col = start_position
    end_row, end_col = end_position

    # Ensure both positions are on the same row
    if start_row != end_row:
        return False

    # Determine the direction of the check (left or right)
    step = 1 if start_col < end_col else -1

    # Check each square between the start and end positions
    for col in range(start_col + step, end_col, step):
        if board_state[start_row][col] is not None:
            return False

    return True


def is_opponents_piece(start_position, end_position, board_state):
    '''Returns True if the end position contains an opponent's piece, False otherwise.'''
    start_piece = board_state[start_position[0]][start_position[1]]
    end_piece = board_state[end_position[0]][end_position[1]]

    if end_piece is None:
        return False

    # Opponents piece if the colors are different
    return start_piece[0] != end_piece[0]


def perform_castling(move, board_state, player):

    # Determine the row for the king and rook based on the player
    row = 7 if player == 'w' else 0
    king_start_col, king_end_col, rook_start_col, rook_end_col = (4, 6, 7, 5) if move in ['e1g1', 'e8g8'] else (4, 2, 0, 3)

    # Check if the king or rook has moved
    if pieces_moved[f'{player}k'] or pieces_moved[f'{player}r{1 if move in ["e1c1", "e8c8"] else 2}']:
        print("Cannot castle, the king or rook has moved.")
        return False

    # Check conditions for castling (not in check, no pieces between king and rook, etc.)
    if is_in_check((row, 4), board_state) or not is_path_clear((row, king_start_col), (row, rook_start_col), board_state):
        print("Cannot castle due to castling rules.")
        return False

    # Move king and rook to their new positions
    board_state[row][king_start_col] = None
    board_state[row][rook_start_col] = None
    board_state[row][king_end_col] = f'{player}k'
    board_state[row][rook_end_col] = f'{player}r'

    # Update pieces_moved flags
    pieces_moved[f'{player}k'] = True
    pieces_moved[f'{player}r{1 if move in ["e1c1", "e8c8"] else 2}'] = True

    return True


def find_king(board_state, color):
    for row in range(8):
        for col in range(8):
            if board_state[row][col] and board_state[row][col] == color + 'k':
                return (row, col)
    return None


def is_game_over(board_state, player, last_move):
    king_position = find_king(board_state, player)
    if is_in_check(king_position, board_state):
        # Player is in check. Check if they have any legal moves left
        if not has_legal_moves(board_state, player, last_move):
            print(f"Checkmate! {'Black' if player == 'w' else 'White'} wins!")
            return True
        
    return False


def reset_game():
    global current_board_state, current_player, last_move, pieces_moved
    # Reset the board to the initial state
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
    # Reset current player to white
    current_player = 'w'
    # Reset last move
    last_move = None
    # Reset pieces moved flags
    pieces_moved = {
        'wk': False, 'wr1': False, 'wr2': False,
        'bk': False, 'br1': False, 'br2': False
    }


def get_piece_type(piece_code):

    return {
        'wp': '', 'bp': '',
        'wn': 'N', 'bn': 'N',
        'wb': 'B', 'bb': 'B',
        'wr': 'R', 'br': 'R',
        'wq': 'Q', 'bq': 'Q',
        'wk': 'K', 'bk': 'K'
    }[piece_code]


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

        if user_input in ['e1g1', 'e1c1', 'e8g8', 'e8c8']:
            return user_input, None

        # Check if the normalized input is exactly 4 characters (e.g., 'e2e4')
        if len(normalized_input) == 4 and all(char.isalnum() for char in normalized_input):
            start_pos = normalized_input[:2]
            end_pos = normalized_input[2:]
            return start_pos, end_pos

        else:
            print("Invalid input. Please enter your move in the format 'e2e4' or 'e2 to e4'.")
            continue


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


# Main Game Loop
def main():
    global current_board_state, current_player, last_move
    current_player = 'w'  # White starts the game
    last_move = None  # Initialize last_move
    print("Welcome to Chess!")
    print("Enter moves in algebraic notation or verbose notation (e.g., 'e2e4' or 'e2 to e4').")
    print("Enter 'reset' to reset the game.")

    while not is_game_over(current_board_state, current_player, last_move):
        display_board(current_board_state)
        
        print(f"{current_player.upper()}'s turn.")
        from_move, to_move = get_user_move()

        # Check for reset command
        if from_move == 'reset':
            reset_game()
            print("Game has been reset.")
            display_board(current_board_state)
            continue

        # Handle castling moves
        if to_move is None and from_move in ['e1g1', 'e1c1', 'e8g8', 'e8c8']:
            print("Castling move")
            if perform_castling(from_move, current_board_state, current_player):
                # Toggle player after a successful castling move
                current_player = 'b' if current_player == 'w' else 'w'
                continue
            else:
                print("Invalid castling move. Please try again.")
                continue
        else:
            # Handle regular moves
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
    print(f"handle_special_move called with move: {move}, board_state: {board_state}, player: {player}")
    if move in ['e1g1', 'e1c1', 'e8g8', 'e8c8']:
        return perform_castling(move, board_state, player)
    return False

if __name__ == '__main__':
    main()