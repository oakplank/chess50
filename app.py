from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import copy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chess50.db'
db = SQLAlchemy(app)

PIECE_TO_SVG = {
    'bn': 'svg/pieces/bn.svg',
    'br': 'svg/pieces/br.svg',
    'bb': 'svg/pieces/bb.svg',
    'bq': 'svg/pieces/bq.svg',
    'bk': 'svg/pieces/bk.svg',
    'bp': 'svg/pieces/bp.svg',
    'wr': 'svg/pieces/wr.svg',
    'wn': 'svg/pieces/wn.svg',
    'wb': 'svg/pieces/wb.svg',
    'wq': 'svg/pieces/wq.svg',
    'wk': 'svg/pieces/wk.svg',
    'wp': 'svg/pieces/wp.svg'
}

# Global variables for the current state of the game
taken_pieces = {'white': [], 'black': []}
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

initial_board_state = [
    ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
    ['bp'] * 8,
    [None] * 8,
    [None] * 8,
    [None] * 8,
    [None] * 8,
    ['wp'] * 8,
    ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr']
]

game_moves = []

current_move_number = 1

pieces_moved = {
    'wk': False, 'wr1': False, 'wr2': False,
    'bk': False, 'br1': False, 'br2': False
}

def store_initial_board_state():
    global initial_board_state
    initial_board_state = copy.deepcopy(current_board_state)

def count_pieces(board_state):
    piece_count = {'wp': 0, 'bp': 0, 'wn': 0, 'bn': 0, 'wb': 0, 'bb': 0, 'wr': 0, 'br': 0, 'wq': 0, 'bq': 0, 'wk': 0, 'bk': 0}

    for row in board_state:
        for piece in row:
            if piece:
                piece_count[piece] += 1

    return piece_count

def calculate_taken_pieces():
    initial_counts = count_pieces(initial_board_state)
    current_counts = count_pieces(current_board_state)

    taken_pieces = {'white': [], 'black': []}

    for piece, count in initial_counts.items():
        taken_count = count - current_counts[piece]
        for _ in range(taken_count):
            color = 'white' if piece.startswith('b') else 'black'
            taken_pieces[color].append(piece)

    return taken_pieces


def get_rook_moves(start_position, board_state):
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

def get_bishop_moves(start_position, board_state):
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

def get_knight_moves(start_position, board_state):
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

def get_pawn_moves(start_position, board_state, is_first_move, last_move):
    moves = []
    direction = -1 if board_state[start_position[0]][start_position[1]].startswith('w') else 1
    row, col = start_position

    print(f"Starting Position: {start_position}, Direction: {direction}")

    # Forward move
    forward_row = row + direction
    if 0 <= forward_row < 8 and board_state[forward_row][col] is None:
        moves.append((forward_row, col))
        print(f"Forward Move Added: {(forward_row, col)}")
        if is_first_move:
            double_forward_row = forward_row + direction
            if 0 <= double_forward_row < 8 and board_state[double_forward_row][col] is None:
                moves.append((double_forward_row, col))
                print(f"Double Forward Move Added: {(double_forward_row, col)}")

    # Diagonal captures including en passant
    for diagonal_col in [col - 1, col + 1]:
        if 0 <= diagonal_col < 8:
            diagonal_row = row + direction
            target_piece = board_state[diagonal_row][diagonal_col]

            if target_piece and target_piece[0] != board_state[row][col][0]:
                moves.append((diagonal_row, diagonal_col))
                print(f"Regular Capture Move Added: {(diagonal_row, diagonal_col)}")

            elif not target_piece and last_move:
                print(f"Checking En Passant at Diagonal: {(diagonal_row, diagonal_col)}")
                # Adjusted Conditions for En Passant
                condition_1 = last_move and last_move['piece_code'][1] == 'p' and abs(last_move['from_position'][0] - last_move['to_position'][0]) == 2
                condition_2 = abs(last_move['to_position'][1] - col) == 1  # Adjacent column
                condition_3 = (direction == -1 and row == 3) or (direction == 1 and row == 4)
                condition_4 = abs(diagonal_col - col) == 1  # Diagonal to adjacent column
                condition_5 = diagonal_col == last_move['to_position'][1]  # Diagonal towards last move's pawn

                print(f"Last Move Data: {last_move}")
                print(f"Condition 1 (Last move was a two-square advance): {condition_1}")
                print(f"Condition 2 (Last move pawn is in the same column as current pawn's start): {condition_2}")
                print(f"Condition 3 (Pawn is in correct row for en passant): {condition_3}")
                print(f"Condition 4 (Diagonal move is to adjacent column): {condition_4}")
                print(f"Condition 5 (Diagonal move is towards last move's pawn): {condition_5}")

                if condition_1 and condition_2 and condition_3 and condition_4 and condition_5:
                    en_passant_capture_row = row  # The row of the captured pawn
                    en_passant_capture_col = diagonal_col  # The column of the captured pawn
                    board_state[en_passant_capture_row][en_passant_capture_col] = None  # Remove the captured pawn
                    moves.append((diagonal_row, diagonal_col))  # Add en passant move
                    print(f"En Passant Move Added: {(en_passant_capture_row, en_passant_capture_col)}")
                else:
                    print("En Passant Conditions Not Met")

    print(f"Final Move List: {moves}")
    return moves



def get_queen_moves(start_position, board_state):
    # Combine the moves of a rook and a bishop
    return get_rook_moves(start_position, board_state) + get_bishop_moves(start_position, board_state)

def get_king_moves(start_position, board_state):
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
    piece = board_state[start_position[0]][start_position[1]]
    temp_board = copy.deepcopy(board_state)
    move_piece(temp_board, start_position, end_position)
    king_position = find_king(temp_board, piece[0])
    return not is_in_check(king_position, temp_board)

def find_king(board_state, color):
    for row in range(8):
        for col in range(8):
            if board_state[row][col] and board_state[row][col] == color + 'k':
                return (row, col)
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/game')
def game():
    print("Current board state:", current_board_state)
    return render_template('game.html', board=current_board_state, piece_to_svg=PIECE_TO_SVG, enumerate=enumerate)

def get_piece_type(piece_code):

    return {
        'wp': '', 'bp': '',
        'wn': 'N', 'bn': 'N',
        'wb': 'B', 'bb': 'B',
        'wr': 'R', 'br': 'R',
        'wq': 'Q', 'bq': 'Q',
        'wk': 'K', 'bk': 'K'
    }[piece_code]

def move_piece(board, from_index, to_index):
    global pieces_moved

    # Print the current board state for debugging
    print("Current board state before move:")
    for row in board:
        print(row)

    # Print the move details
    print(f"Moving from {from_index} to {to_index}")

    piece = board[from_index[0]][from_index[1]]
    captured_piece = board[to_index[0]][to_index[1]]

    # Print the piece details
    print(f"Piece to move: {piece}")
    print(f"Captured piece, if any: {captured_piece}")

    board[from_index[0]][from_index[1]] = None
    board[to_index[0]][to_index[1]] = piece

    # Update pieces_moved flag for kings and rooks
    if piece in ['wk', 'wr', 'bk', 'br']:
        if piece in ['wk', 'bk']:  # Kings
            pieces_moved[piece] = True
        elif piece in ['wr', 'br']:  # Rooks
            rook_index = '1' if from_index[1] == 0 else '2'
            pieces_moved[piece + rook_index] = True

    # Print the updated board state for debugging
    print("Updated board state after move:")
    for row in board:
        print(row)

    return captured_piece


def convert_to_pgn(from_position, to_position, piece_code, is_capture, promotion=None, check=False, checkmate=False):
        piece_type = get_piece_type(piece_code)
        capture_notation = 'x' if is_capture else ''
        promotion_notation = f'={promotion.upper()}' if promotion else ''
        check_notation = '+' if check else ('#' if checkmate else '')

        # For pawns, include the starting file if there is a capture
        from_file = from_position[0] if piece_type == '' and is_capture else ''

        # Construct the PGN move notation
        pgn_move = f"{piece_type}{from_file}{capture_notation}{to_position}{promotion_notation}{check_notation}"

        return pgn_move


def convert_position(pos):
        column = ord(pos[0]) - ord('a')
        row = 8 - int(pos[1])
        return row, column

# Game Logic

def has_moved(piece_code, position):
    piece_key = piece_code if piece_code in ['wk', 'bk'] else piece_code + str(position[1])
    return pieces_moved.get(piece_key, False)

def is_white_piece(position, board_state):
    piece = board_state[position[0]][position[1]]
    return piece and piece.startswith('w')

def is_black_piece(position, board_state):
    piece = board_state[position[0]][position[1]]
    return piece and piece.startswith('b')

def is_legal_move(start_position, end_position, piece_code, board_state):

    # Determine valid moves based on the piece type
    valid_moves = []
    if piece_code[1] == 'p':
        valid_moves = get_pawn_moves(from_position, current_board_state, is_first_move, last_move)
    elif piece_code[1] == 'r':
        valid_moves = get_rook_moves(start_position, board_state)
    elif piece_code[1] == 'n':
        valid_moves = get_knight_moves(start_position, board_state)
    elif piece_code[1] == 'b':
        valid_moves = get_bishop_moves(start_position, board_state)
    elif piece_code[1] == 'q':
        valid_moves = get_queen_moves(start_position, board_state)
    elif piece_code[1] == 'k':
        valid_moves = get_king_moves(start_position, board_state)

    # Check if the end position is within valid moves
    if end_position not in valid_moves:
        return False

    # Make a temporary move and check for check
    temp_board = copy.deepcopy(board_state)
    move_piece(temp_board, start_position, end_position)
    king_position = find_king(temp_board, piece_code[0])
    if is_in_check(king_position, temp_board):
        return False

    return True


def is_in_check(king_position, board_state):
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

def is_opponents_piece(start_position, end_position, board_state):
    start_piece = board_state[start_position[0]][start_position[1]]
    end_piece = board_state[end_position[0]][end_position[1]]

    if end_piece is None:
        return False

    # Opponents piece if the colors are different
    return start_piece[0] != end_piece[0]


def is_path_clear(start_position, end_position, board_state):
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


def perform_castling(king_position, rook_position, board_state, is_kingside):
    global pieces_moved

    king_row, king_col = king_position
    rook_row, rook_col = rook_position

    king_piece = 'wk' if king_row == 7 else 'bk'

    # Determine the correct key for the rook in pieces_moved
    if rook_col == 0:  # Queen's side rook
        rook_piece = 'wr1' if rook_row == 7 else 'br1'
    elif rook_col == 7:  # King's side rook
        rook_piece = 'wr2' if rook_row == 7 else 'br2'
    else:
        raise ValueError("Invalid rook position for castling")

    # Check if the king or rook has moved
    if pieces_moved[king_piece] or pieces_moved[rook_piece]:
        raise ValueError("Cannot castle if the king or rook has moved")


    # Check conditions for castling (not in check, no pieces between king and rook, etc.)
    # Assuming functions like is_in_check and is_path_clear exist
    if is_in_check(king_position, board_state) or not is_path_clear(king_position, rook_position, board_state):
        raise ValueError("Castling conditions not met")

    if is_kingside:
        # Kingside castling logic
        new_king_col = king_col + 2
        new_rook_col = new_king_col - 1
    else:
        # Queenside castling logic
        new_king_col = king_col - 2
        new_rook_col = new_king_col + 1

    # Move king and rook to their new positions
    board_state[king_row][king_col] = None
    board_state[rook_row][rook_col] = None
    board_state[king_row][new_king_col] = 'wk' if king_row == 7 else 'bk'  # Adjust piece code if necessary
    board_state[rook_row][new_rook_col] = 'wr' if rook_row == 7 else 'br'  # Adjust piece code if necessary

    return board_state

@app.route('/record_move', methods=['POST'])
def record_move():
    global current_board_state, taken_pieces, game_moves, current_move_number, last_move
    data = request.json
    print("Received move data:", data)

    from_position = convert_position(data.get('from'))
    to_position = convert_position(data.get('to'))
    piece_code = current_board_state[from_position[0]][from_position[1]]

    # Initialize last_move if it does not exist
    if 'last_move' not in globals():
        last_move = None

    # Check for invalid move (same square)
    if from_position == to_position:
        return jsonify({'success': False, 'message': 'Move to the same square is not allowed'})

    if piece_code is None:
        return jsonify({'success': False, 'message': 'No piece at the source position'})

    captured_piece = None

    # Castling move detection
    if piece_code in ['wk', 'bk'] and abs(from_position[1] - to_position[1]) == 2:
        try:
            rook_col = 7 if to_position[1] > from_position[1] else 0
            perform_castling((from_position[0], from_position[1]), (from_position[0], rook_col), current_board_state, to_position[1] > from_position[1])
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)})
    else:
        # Other moves
        is_en_passant = False
        if piece_code[1] == 'p':
            is_first_move = (piece_code == 'wp' and from_position[0] == 6) or (piece_code == 'bp' and from_position[0] == 1)
            valid_moves = get_pawn_moves(from_position, current_board_state, is_first_move, last_move)
            if to_position not in valid_moves:
                return jsonify({'success': False, 'message': 'Invalid move'})
            is_en_passant = to_position in [move for move in valid_moves if current_board_state[move[0]][move[1]] is None]
        else:
            if not is_legal_move(from_position, to_position, piece_code, current_board_state):
                return jsonify({'success': False, 'message': 'Invalid move'})

        captured_piece = move_piece(current_board_state, from_position, to_position)

        if is_en_passant:
            captured_pawn_row = from_position[0]
            captured_pawn_col = to_position[1]
            captured_piece = current_board_state[captured_pawn_row][captured_pawn_col]
            current_board_state[captured_pawn_row][captured_pawn_col] = None

        if captured_piece and captured_piece != piece_code:
            color = 'white' if captured_piece[0] == 'b' else 'black'
            taken_pieces[color].append(captured_piece)

    pgn_move = convert_to_pgn(data.get('from'), data.get('to'), piece_code, captured_piece is not None)

    if len(game_moves) == 0 or len(game_moves[-1].split(' ')) == 3:
        game_moves.append(f"{current_move_number}. {pgn_move}")
    else:
        game_moves[-1] += f" {pgn_move}"
        current_move_number += 1

    last_move = {
        'from_position': from_position,
        'to_position': to_position,
        'piece_code': piece_code
    }

    # Calculate the taken pieces after the move
    taken_pieces = calculate_taken_pieces()

    response_data = {
        'success': True,
        'message': 'Move recorded',
        'newBoardState': current_board_state,
        'takenPieces': taken_pieces,
        'gameMoves': ' '.join(game_moves)
    }

    print("Sending response data:", response_data)
    return jsonify(response_data)


@app.route('/reset_game', methods=['POST'])
def reset_game():
    global current_board_state, taken_pieces, game_moves, current_move_number, pieces_moved

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
    taken_pieces = {'white': [], 'black': []}
    game_moves = []
    current_move_number = 1

    pieces_moved = {
        'wk': False, 'wr1': False, 'wr2': False,
        'bk': False, 'br1': False, 'br2': False
    }
    last_move = None
    print("Game reset")  # For debugging
    return jsonify({'success': True, 'message': 'Game reset', 'newBoardState': current_board_state, 'gameMoves': ' '.join(game_moves)})


@app.route('/attempt_castle', methods=['POST'])
def attempt_castle():
    global current_board_state, game_moves, current_move_number
    data = request.json
    from_position = data.get('from')
    to_position = data.get('to')
    piece_code = data.get('piece')

    # Convert positions from algebraic notation to row and column indices
    from_row, from_col = convert_position(from_position)
    to_row, to_col = convert_position(to_position)

    # Determine if the castling is kingside or queenside
    is_kingside = to_col > from_col

    # Determine the rook involved in castling based on the direction of the king's move
    rook_col = 7 if is_kingside else 0
    rook_position = (from_row, rook_col)

    try:
        # Perform the castling move
        updated_board_state = perform_castling((from_row, from_col), rook_position, current_board_state, is_kingside)

        # Update the board state after successful castling
        current_board_state = updated_board_state

        # Construct PGN notation for the castling move
        castling_notation = 'O-O' if is_kingside else 'O-O-O'
        pgn_move = f"{castling_notation}"

        # Record the move
        if piece_code.startswith('w'):
            game_moves.append(f"{current_move_number}. {pgn_move}")
        else:
            game_moves[-1] += f" {pgn_move}"
            current_move_number += 1

        return jsonify({'success': True, 'newBoardState': current_board_state, 'gameMoves': ' '.join(game_moves)})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/get_current_board', methods=['GET'])
def get_current_board():
    return jsonify(current_board_state)

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')
