"""
Chess Move Disambiguation Module

This module handles the logic for determining when disambiguation is needed
in chess algebraic notation (e.g., Nbd2 vs Nd2 when multiple knights can reach d2).
"""

def get_disambiguation(start_pos, end_pos, piece, board_state):
    """
    Determine if disambiguation is needed for a chess move and return the appropriate notation.
    
    Args:
        start_pos: (row, col) where the piece is moving from
        end_pos: (row, col) where the piece is moving to
        piece: The piece character (e.g., 'N', 'R', 'Q', 'B')
        board_state: 8x8 board array
    
    Returns:
        String: Empty string if no disambiguation needed, or file/rank/full square if needed
    """
    start_row, start_col = start_pos
    end_row, end_col = end_pos
    files = "abcdefgh"
    ranks = "87654321"
    
    print(f"\n=== DISAMBIGUATION DEBUG ===")
    print(f"Piece: {piece}, From: {files[start_col]}{ranks[start_row]} ({start_row},{start_col})")
    print(f"To: {files[end_col]}{ranks[end_row]} ({end_row},{end_col})")
    
    # Find all other pieces of the same type and color
    same_pieces = []
    for row in range(8):
        for col in range(8):
            if board_state[row][col] == piece and (row, col) != start_pos:
                same_pieces.append((row, col))
                print(f"Found same piece {piece} at {files[col]}{ranks[row]} ({row},{col})")
    
    if not same_pieces:
        print("No other pieces of same type found - no disambiguation needed")
        return ""
    
    # Check which of these pieces can actually reach the target square
    pieces_that_can_reach_target = []
    
    for other_row, other_col in same_pieces:
        print(f"\nChecking if {piece} at {files[other_col]}{ranks[other_row]} can reach {files[end_col]}{ranks[end_row]}...")
        
        if can_piece_reach_square(piece, (other_row, other_col), (end_row, end_col), board_state):
            pieces_that_can_reach_target.append((other_row, other_col))
            print(f"  YES - {piece} at {files[other_col]}{ranks[other_row]} CAN reach target")
        else:
            print(f"  NO - {piece} at {files[other_col]}{ranks[other_row]} CANNOT reach target")
    
    print(f"\nPieces that can reach target: {len(pieces_that_can_reach_target)}")
    for row, col in pieces_that_can_reach_target:
        print(f"  - {files[col]}{ranks[row]} ({row},{col})")
    
    # If no other pieces can reach the target, no disambiguation needed
    if not pieces_that_can_reach_target:
        print("No disambiguation needed - no other pieces can reach target")
        return ""
    
    # Determine what type of disambiguation is needed
    same_file_pieces = [pos for pos in pieces_that_can_reach_target if pos[1] == start_col]
    same_rank_pieces = [pos for pos in pieces_that_can_reach_target if pos[0] == start_row]
    
    print(f"\nDisambiguation analysis:")
    print(f"  Same file conflicts: {len(same_file_pieces)} pieces")
    print(f"  Same rank conflicts: {len(same_rank_pieces)} pieces")
    
    if same_file_pieces and same_rank_pieces:
        # Need full square disambiguation (both file and rank conflicts)
        result = files[start_col] + ranks[start_row]
        print(f"  FULL SQUARE disambiguation needed: {result}")
        return result
    elif same_file_pieces:
        # Need rank disambiguation (file conflicts)
        result = ranks[start_row]
        print(f"  RANK disambiguation needed: {result}")
        return result
    else:
        # Need file disambiguation (no file conflicts or rank conflicts)
        result = files[start_col]
        print(f"  FILE disambiguation needed: {result}")
        return result


def can_piece_reach_square(piece, from_pos, to_pos, board_state):
    """
    Check if a specific piece at from_pos can legally reach to_pos.
    
    Args:
        piece: The piece character (e.g., 'N', 'R', 'Q', 'B')
        from_pos: (row, col) starting position
        to_pos: (row, col) target position
        board_state: 8x8 board array
    
    Returns:
        bool: True if the piece can reach the target square
    """
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    piece_type = piece.upper()
    
    if piece_type == 'N':  # Knight
        return can_knight_reach(from_pos, to_pos)
    elif piece_type == 'R':  # Rook
        return can_rook_reach(from_pos, to_pos, board_state)
    elif piece_type == 'B':  # Bishop
        return can_bishop_reach(from_pos, to_pos, board_state)
    elif piece_type == 'Q':  # Queen
        return can_queen_reach(from_pos, to_pos, board_state)
    elif piece_type == 'K':  # King
        return can_king_reach(from_pos, to_pos)
    elif piece_type == 'P':  # Pawn
        return can_pawn_reach(from_pos, to_pos, piece, board_state)
    
    return False


def can_knight_reach(from_pos, to_pos):
    """Check if a knight can reach the target square"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    row_diff = abs(to_row - from_row)
    col_diff = abs(to_col - from_col)
    
    # Knight moves in L-shape: 2+1 or 1+2
    return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)


def can_rook_reach(from_pos, to_pos, board_state):
    """Check if a rook can reach the target square (straight line, no obstructions)"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    # Rook moves horizontally or vertically
    if from_row != to_row and from_col != to_col:
        return False
    
    # Check for obstructions in the path
    if from_row == to_row:  # Horizontal movement
        start_col = min(from_col, to_col)
        end_col = max(from_col, to_col)
        for col in range(start_col + 1, end_col):
            if board_state[from_row][col] != ".":
                return False
    else:  # Vertical movement
        start_row = min(from_row, to_row)
        end_row = max(from_row, to_row)
        for row in range(start_row + 1, end_row):
            if board_state[row][from_col] != ".":
                return False
    
    return True


def can_bishop_reach(from_pos, to_pos, board_state):
    """Check if a bishop can reach the target square (diagonal line, no obstructions)"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    row_diff = abs(to_row - from_row)
    col_diff = abs(to_col - from_col)
    
    # Bishop moves diagonally
    if row_diff != col_diff:
        return False
    
    # Check for obstructions in the diagonal path
    row_direction = 1 if to_row > from_row else -1
    col_direction = 1 if to_col > from_col else -1
    
    current_row = from_row + row_direction
    current_col = from_col + col_direction
    
    while current_row != to_row and current_col != to_col:
        if board_state[current_row][current_col] != ".":
            return False
        current_row += row_direction
        current_col += col_direction
    
    return True


def can_queen_reach(from_pos, to_pos, board_state):
    """Check if a queen can reach the target square (rook + bishop movement)"""
    return can_rook_reach(from_pos, to_pos, board_state) or can_bishop_reach(from_pos, to_pos, board_state)


def can_king_reach(from_pos, to_pos):
    """Check if a king can reach the target square (one square in any direction)"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    row_diff = abs(to_row - from_row)
    col_diff = abs(to_col - from_col)
    
    # King moves one square in any direction
    return row_diff <= 1 and col_diff <= 1 and (row_diff != 0 or col_diff != 0)


def can_pawn_reach(from_pos, to_pos, piece, board_state):
    """Check if a pawn can reach the target square"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    # This is a simplified version - for disambiguation, we mainly care about captures
    # and forward moves. The full pawn logic is complex with en passant, etc.
    
    # Determine pawn direction based on color
    if piece.isupper():  # White pawn
        direction = -1  # White moves up (decreasing row numbers)
    else:  # Black pawn
        direction = 1   # Black moves down (increasing row numbers)
    
    row_diff = to_row - from_row
    col_diff = abs(to_col - from_col)
    
    # Forward move (1 or 2 squares)
    if from_col == to_col:
        if row_diff == direction:  # One square forward
            return board_state[to_row][to_col] == "."
        elif row_diff == 2 * direction:  # Two squares forward (initial move)
            start_row = 6 if piece.isupper() else 1  # Assuming white on bottom
            return from_row == start_row and board_state[to_row][to_col] == "." and board_state[from_row + direction][from_col] == "."
    
    # Diagonal capture
    elif col_diff == 1 and row_diff == direction:
        target_piece = board_state[to_row][to_col]
        if target_piece != "." and (piece.isupper() != target_piece.isupper()):
            return True
        # TODO: Add en passant logic here if needed for disambiguation
    
    return False


def test_disambiguation():
    """Test function to verify disambiguation logic"""
    # Create a test board position
    test_board = [
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", "N", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", "N", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
    ]
    
    # Test knight disambiguation
    result = get_disambiguation((6, 1), (4, 2), 'N', test_board)
    print(f"Knight disambiguation result: '{result}'")


if __name__ == "__main__":
    test_disambiguation()