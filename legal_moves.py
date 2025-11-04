"""
Chess Legal Move Validation Module

This module handles all the logic for determining legal chess moves,
including basic piece movement, check detection, and move validation.
"""

def is_promotion_move(from_pos, to_pos, board_state, white_on_bottom=True):
    """Check if a move results in pawn promotion.

    Note: Promotion is based on board coordinates, not display orientation.
    White promotes on row 0, Black promotes on row 7 regardless of white_on_bottom.
    """
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    piece = board_state[from_row][from_col]
    
    if piece not in "Pp":
        return False
    
    # Orientation-independent promotion rows
    if piece == "P" and to_row == 0:
        return True
    if piece == "p" and to_row == 7:
        return True
    
    return False

def get_promoted_piece(piece_type, is_white):
    """Convert piece type to proper case based on color"""
    if is_white:
        return piece_type.upper()
    else:
        return piece_type.lower()

def calculate_valid_moves(position, board_state, white_on_bottom=True, last_pawn_move=None):
    """Calculate all valid moves for a piece at the given position"""
    row, col = position
    piece = board_state[row][col]
    moves = []
    
    if piece in "Pp":
        moves = get_pawn_moves(position, board_state, white_on_bottom, last_pawn_move)
    elif piece in "Nn":
        moves = get_knight_moves(position, board_state)
    elif piece in "Rr":
        moves = get_rook_moves(position, board_state)
    elif piece in "Bb":
        moves = get_bishop_moves(position, board_state)
    elif piece in "Qq":
        moves = get_queen_moves(position, board_state)
    elif piece in "Kk":
        moves = get_king_moves(position, board_state)
    
    return moves


def get_pawn_moves(position, board_state, white_on_bottom=True, last_pawn_move=None):
    """Calculate valid pawn moves"""
    row, col = position
    piece = board_state[row][col]
    moves = []
    
    direction = get_pawn_direction(piece, white_on_bottom)
    start_r = get_pawn_start_row(piece, white_on_bottom)
    
    # Move forward
    if 0 <= row + direction < 8 and board_state[row + direction][col] == ".":
        moves.append((row + direction, col))
        # Initial double move
        if row == start_r and 0 <= row + 2 * direction < 8 and board_state[row + 2 * direction][col] == ".":
            moves.append((row + 2 * direction, col))
    
    # Captures
    if col > 0 and 0 <= row + direction < 8:
        target_piece = board_state[row + direction][col - 1]
        if target_piece != "." and (piece.isupper() != target_piece.isupper()):
            moves.append((row + direction, col - 1))
    
    if col < 7 and 0 <= row + direction < 8:
        target_piece = board_state[row + direction][col + 1]
        if target_piece != "." and (piece.isupper() != target_piece.isupper()):
            moves.append((row + direction, col + 1))

    # En passant captures (only on specific ranks and only if last_pawn_move matches neighbor)
    # White can capture EP when on internal row 3; Black when on internal row 4
    ep_row = 3 if piece.isupper() else 4
    if row == ep_row and last_pawn_move is not None:
        # Check left neighbor
        if col > 0:
            enemy_r, enemy_c = row, col - 1
            if 0 <= enemy_r < 8 and 0 <= enemy_c < 8:
                enemy = board_state[enemy_r][enemy_c]
                if enemy != "." and (piece.isupper() != enemy.isupper()) and last_pawn_move == (enemy_r, enemy_c):
                    capture_r, capture_c = row + direction, col - 1
                    if 0 <= capture_r < 8 and 0 <= capture_c < 8 and board_state[capture_r][capture_c] == ".":
                        moves.append((capture_r, capture_c))
        # Check right neighbor
        if col < 7:
            enemy_r, enemy_c = row, col + 1
            if 0 <= enemy_r < 8 and 0 <= enemy_c < 8:
                enemy = board_state[enemy_r][enemy_c]
                if enemy != "." and (piece.isupper() != enemy.isupper()) and last_pawn_move == (enemy_r, enemy_c):
                    capture_r, capture_c = row + direction, col + 1
                    if 0 <= capture_r < 8 and 0 <= capture_c < 8 and board_state[capture_r][capture_c] == ".":
                        moves.append((capture_r, capture_c))

    return moves


def get_knight_moves(position, board_state):
    """Calculate valid knight moves"""
    row, col = position
    piece = board_state[row][col]
    moves = []
    
    knight_moves = [
        (row - 2, col - 1), (row - 2, col + 1),
        (row - 1, col - 2), (row - 1, col + 2),
        (row + 1, col - 2), (row + 1, col + 2),
        (row + 2, col - 1), (row + 2, col + 1),
    ]
    
    for r, c in knight_moves:
        if 0 <= r < 8 and 0 <= c < 8:
            target_piece = board_state[r][c]
            if target_piece == "." or (piece.isupper() != target_piece.isupper()):
                moves.append((r, c))
    
    return moves


def get_rook_moves(position, board_state):
    """Calculate valid rook moves"""
    row, col = position
    piece = board_state[row][col]
    return get_linear_moves(row, col, [(0, 1), (1, 0), (0, -1), (-1, 0)], piece, board_state)


def get_bishop_moves(position, board_state):
    """Calculate valid bishop moves"""
    row, col = position
    piece = board_state[row][col]
    return get_linear_moves(row, col, [(1, 1), (1, -1), (-1, 1), (-1, -1)], piece, board_state)


def get_queen_moves(position, board_state):
    """Calculate valid queen moves"""
    row, col = position
    piece = board_state[row][col]
    return get_linear_moves(row, col, [
        (0, 1), (1, 0), (0, -1), (-1, 0),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ], piece, board_state)


def get_king_moves(position, board_state):
    """Calculate valid king moves"""
    row, col = position
    piece = board_state[row][col]
    moves = []
    
    king_moves = [
        (row - 1, col), (row + 1, col),
        (row, col - 1), (row, col + 1),
        (row - 1, col - 1), (row - 1, col + 1),
        (row + 1, col - 1), (row + 1, col + 1),
    ]
    
    for r, c in king_moves:
        if 0 <= r < 8 and 0 <= c < 8:
            target_piece = board_state[r][c]
            if target_piece == "." or (piece.isupper() != target_piece.isupper()):
                moves.append((r, c))
    
    return moves


def get_linear_moves(row, col, directions, piece, board_state):
    """Calculate moves for pieces that move in straight lines (rook, bishop, queen)"""
    moves = []
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            target_piece = board_state[r][c]
            if target_piece == ".":
                moves.append((r, c))
            elif piece.isupper() != target_piece.isupper():
                moves.append((r, c))
                break
            else:
                break
            r += dr
            c += dc
    return moves


def get_pawn_direction(piece, white_on_bottom=True):
    """Get the direction a pawn moves based on color.

    Direction is independent of display orientation. In internal board
    coordinates, white pawns move toward decreasing row indices (-1),
    black pawns move toward increasing row indices (+1).
    """
    return -1 if piece.isupper() else 1


def get_pawn_start_row(piece, white_on_bottom=True):
    """Get the starting row for a pawn based on color (orientation-independent)."""
    return 6 if piece.isupper() else 1


def get_pawn_promotion_row(piece, white_on_bottom=True):
    """Get the promotion row for a pawn based on color (orientation-independent)."""
    return 0 if piece.isupper() else 7


def is_in_check(player_color, board_state, white_on_bottom=True):
    """Check if the given player's king is in check"""
    king_position = None
    for row in range(8):
        for col in range(8):
            piece = board_state[row][col]
            if (player_color == "white" and piece == "K") or (player_color == "black" and piece == "k"):
                king_position = (row, col)
                break
        if king_position:
            break

    if not king_position:
        return False

    opponent_color = "black" if player_color == "white" else "white"
    for row in range(8):
        for col in range(8):
            piece = board_state[row][col]
            if (opponent_color == "white" and piece.isupper()) or (opponent_color == "black" and piece.islower()):
                possible_moves = calculate_valid_moves((row, col), board_state, white_on_bottom)
                if king_position in possible_moves:
                    return True
    return False


def is_checkmate(player_color, board_state, white_on_bottom=True):
    """Check if the given player is in checkmate"""
    # Must be in check to be checkmate
    if not is_in_check(player_color, board_state, white_on_bottom):
        return False
    
    # Check if any legal move can get out of check
    for row in range(8):
        for col in range(8):
            piece = board_state[row][col]
            # Check if this piece belongs to the player
            if piece != "." and ((player_color == "white" and piece.isupper()) or (player_color == "black" and piece.islower())):
                # Get all possible moves for this piece
                possible_moves = calculate_valid_moves((row, col), board_state, white_on_bottom)
                
                # Test each move to see if it gets out of check
                for move_row, move_col in possible_moves:
                    # Simulate the move
                    original_piece_at_start = board_state[row][col]
                    original_piece_at_end = board_state[move_row][move_col]
                    
                    # Make the move temporarily
                    board_state[row][col] = "."
                    board_state[move_row][move_col] = piece
                    
                    # Check if player is still in check after this move
                    still_in_check = is_in_check(player_color, board_state, white_on_bottom)
                    
                    # Undo the move
                    board_state[row][col] = original_piece_at_start
                    board_state[move_row][move_col] = original_piece_at_end
                    
                    # If this move gets out of check, it's not checkmate
                    if not still_in_check:
                        return False
    
    return True


def is_stalemate(player_color, board_state, white_on_bottom=True):
    """Check if the given player is in stalemate (no legal moves but not in check)"""
    # Must NOT be in check to be stalemate
    if is_in_check(player_color, board_state, white_on_bottom):
        return False
    
    # Check if any legal move exists
    for row in range(8):
        for col in range(8):
            piece = board_state[row][col]
            # Check if this piece belongs to the player
            if piece != "." and ((player_color == "white" and piece.isupper()) or (player_color == "black" and piece.islower())):
                # Get all possible moves for this piece
                possible_moves = calculate_valid_moves((row, col), board_state, white_on_bottom)
                
                # Test each move to see if it's legal (doesn't put own king in check)
                for move_row, move_col in possible_moves:
                    # Simulate the move
                    original_piece_at_start = board_state[row][col]
                    original_piece_at_end = board_state[move_row][move_col]
                    
                    # Make the move temporarily
                    board_state[row][col] = "."
                    board_state[move_row][move_col] = piece
                    
                    # Check if this move puts own king in check
                    puts_king_in_check = is_in_check(player_color, board_state, white_on_bottom)
                    
                    # Undo the move
                    board_state[row][col] = original_piece_at_start
                    board_state[move_row][move_col] = original_piece_at_end
                    
                    # If this move doesn't put king in check, there's a legal move
                    if not puts_king_in_check:
                        return False
    
    return True


def leaves_king_in_check(start, end, board_state, current_turn, white_on_bottom=True, last_pawn_move=None):
    """Check if a move would leave the player's own king in check"""
    original_piece_at_start = board_state[start[0]][start[1]]
    original_piece_at_end = board_state[end[0]][end[1]]

    piece = board_state[start[0]][start[1]]
    board_state[start[0]][start[1]] = "."
    board_state[end[0]][end[1]] = piece

    # Handle en passant capture simulation
    is_en_passant_capture = en_passant(start, end, piece, board_state, last_pawn_move, white_on_bottom)
    captured_pawn_pos = None
    if is_en_passant_capture:
        direction = get_pawn_direction(piece, white_on_bottom)
        captured_pawn_row = end[0] - direction
        captured_pawn_pos = (captured_pawn_row, end[1])
        board_state[captured_pawn_row][end[1]] = "."

    in_check = is_in_check(current_turn, board_state, white_on_bottom)

    # Undo the move
    board_state[start[0]][start[1]] = original_piece_at_start
    board_state[end[0]][end[1]] = original_piece_at_end

    if is_en_passant_capture and captured_pawn_pos:
        enemy_piece = "p" if piece == "P" else "P"
        board_state[captured_pawn_pos[0]][captured_pawn_pos[1]] = enemy_piece

    return in_check


def en_passant(start, end, piece, board_state, last_pawn_move=None, white_on_bottom=True):
    """Check if a move is an en passant capture"""
    start_row, start_col = start
    end_row, end_col = end

    if piece.isupper():
        # White pawn
        if abs(start_col - end_col) == 1 and board_state[end_row][end_col] == ".":
            direction = get_pawn_direction(piece, white_on_bottom)
            enemy_row = end_row - direction
            if 0 <= enemy_row < 8:
                if last_pawn_move == (enemy_row, end_col) and board_state[enemy_row][end_col] == "p":
                    return True
    else:
        # Black pawn
        if abs(start_col - end_col) == 1 and board_state[end_row][end_col] == ".":
            direction = get_pawn_direction(piece, white_on_bottom)
            enemy_row = end_row - direction
            if 0 <= enemy_row < 8:
                if last_pawn_move == (enemy_row, end_col) and board_state[enemy_row][end_col] == "P":
                    return True
    return False


def squares_under_attack(squares, player_color, board_state, white_on_bottom=True):
    """Check if squares are under attack by the opponent"""
    opponent_color = 'black' if player_color == 'white' else 'white'
    for (r, c) in squares:
        original_piece = board_state[r][c]
        # Temporarily place a king of player_color here
        board_state[r][c] = 'K' if player_color == 'white' else 'k'
        if is_in_check(player_color, board_state, white_on_bottom):
            board_state[r][c] = original_piece
            return True
        board_state[r][c] = original_piece
    return False


def calculate_castling_moves(row, col, piece, board_state, white_on_bottom=True, 
                           white_king_moved=False, white_rook_left_moved=False, white_rook_right_moved=False,
                           black_king_moved=False, black_rook_left_moved=False, black_rook_right_moved=False):
    """Calculate valid castling moves for a king.

    Castling squares are based on board coordinates, independent of display
    orientation. White king starts at (7,4), Black king at (0,4).
    """
    moves = []
    player_color = 'white' if piece.isupper() else 'black'

    if player_color == 'white':
        king_row, king_col = 7, 4
        left_rook_pos = (7, 0)
        right_rook_pos = (7, 7)
        king_moved = white_king_moved
        rook_left_moved = white_rook_left_moved
        rook_right_moved = white_rook_right_moved
        expected_left_rook = "R"
        expected_right_rook = "R"
    else:
        king_row, king_col = 0, 4
        left_rook_pos = (0, 0)
        right_rook_pos = (0, 7)
        king_moved = black_king_moved
        rook_left_moved = black_rook_left_moved
        rook_right_moved = black_rook_right_moved
        expected_left_rook = "r"
        expected_right_rook = "r"

    # If king not in correct position, no castling moves
    if (row, col) != (king_row, king_col):
        return moves

    def path_clear(path_positions):
        for (r, c) in path_positions:
            if board_state[r][c] != ".":
                return False
        return True

    def path_safe(squares, color):
        return not squares_under_attack(squares, color, board_state, white_on_bottom)

    player_color_str = player_color

    # Attempt queenside castling
    if not king_moved and not rook_left_moved and board_state[left_rook_pos[0]][left_rook_pos[1]] == expected_left_rook:
        path_cols = range(left_rook_pos[1] + 1, king_col)
        path_positions = [(king_row, c) for c in path_cols]
        if path_clear(path_positions):
            if not is_in_check(player_color_str, board_state, white_on_bottom):
                if path_safe([(king_row, king_col - 1), (king_row, king_col - 2)], player_color_str):
                    moves.append((king_row, king_col - 2))

    # Attempt kingside castling
    if not king_moved and not rook_right_moved and board_state[right_rook_pos[0]][right_rook_pos[1]] == expected_right_rook:
        path_cols = range(king_col + 1, right_rook_pos[1])
        path_positions = [(king_row, c) for c in path_cols]
        if path_clear(path_positions):
            if not is_in_check(player_color_str, board_state, white_on_bottom):
                if path_safe([(king_row, king_col + 1), (king_row, king_col + 2)], player_color_str):
                    moves.append((king_row, king_col + 2))

    return moves