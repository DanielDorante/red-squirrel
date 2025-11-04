"""
Evaluation module for chess positions.

- evaluate(board, side_to_move) -> int
  Returns centipawn score from White's perspective (>0 = good for White).

The evaluation currently includes:
- Material term
- Piece-square term (knights only for now)
- Pawn structure term (doubled, isolated, passed)
- King safety term (simple heuristic)

Board representation:
- board is an 8x8 list of lists with single-character strings
  '.' empty, uppercase = White piece, lowercase = Black piece
  'P','N','B','R','Q','K' / 'p','n','b','r','q','k'

This module is self-contained and does not depend on Pygame.
"""
from typing import List, Tuple, Optional

Board = List[List[str]]

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

# Piece-square tables (from White's perspective: row 0 = 8th rank)
PAWN_TABLE: List[List[int]] = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [ 50,  50,  50,  50,  50,  50,  50,  50],
    [ 10,  10,  20,  30,  30,  20,  10,  10],
    [  5,   5,  10,  25,  25,  10,   5,   5],
    [  0,   0,   0,  20,  20,   0,   0,   0],
    [  5,  -5, -10,   0,   0, -10,  -5,   5],
    [  5,  10,  10, -20, -20,  10,  10,   5],
    [  0,   0,   0,   0,   0,   0,   0,   0],
]

KNIGHT_TABLE: List[List[int]] = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

BISHOP_TABLE: List[List[int]] = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

ROOK_TABLE: List[List[int]] = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [  5,  10,  10,  10,  10,  10,  10,   5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   5,   5,   0,   0,  -5],
    [  0,   0,   0,   0,   0,   0,   0,   0],
]

QUEEN_TABLE: List[List[int]] = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   5,   0,   0,   0,   0, -10],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [  0,   0,   5,   5,   5,   5,   0,  -5],
    [ -5,   0,   5,   5,   5,   5,   0,  -5],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
]

KING_TABLE: List[List[int]] = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [ 20,  20,   0,   0,   0,   0,  20,  20],
    [ 20,  30,  10,   0,   0,  10,  30,  20],
]


def material_term(board: Board) -> int:
    """Material balance: White material minus Black material in centipawns."""
    score = 0
    for r in range(8):
        for c in range(8):
            ch = board[r][c]
            if ch == ".":
                continue
            ptype = ch.upper()
            value = PIECE_VALUES.get(ptype, 0)
            if ch.isupper():  # white
                score += value
            else:  # black
                score -= value
    return score


def piece_square_term(board: Board) -> int:
    """Positional bonuses/penalties based on piece-square tables for all pieces."""
    score = 0
    for r in range(8):
        for c in range(8):
            ch = board[r][c]
            if ch == ".":
                continue
            ptype = ch.upper()
            if ptype == "P":
                if ch.isupper():  # white pawn
                    score += PAWN_TABLE[r][c]
                else:  # black pawn
                    score -= PAWN_TABLE[7 - r][c]
            elif ptype == "N":
                if ch.isupper():  # white knight
                    score += KNIGHT_TABLE[r][c]
                else:  # black knight (mirror vertically)
                    score -= KNIGHT_TABLE[7 - r][c]
            elif ptype == "B":
                if ch.isupper():
                    score += BISHOP_TABLE[r][c]
                else:
                    score -= BISHOP_TABLE[7 - r][c]
            elif ptype == "R":
                if ch.isupper():
                    score += ROOK_TABLE[r][c]
                else:
                    score -= ROOK_TABLE[7 - r][c]
            elif ptype == "Q":
                if ch.isupper():
                    score += QUEEN_TABLE[r][c]
                else:
                    score -= QUEEN_TABLE[7 - r][c]
            elif ptype == "K":
                if ch.isupper():
                    score += KING_TABLE[r][c]
                else:
                    score -= KING_TABLE[7 - r][c]
    return score


# ----- Pawn structure helpers -----

def doubled_pawn_penalty(board: Board) -> int:
    """Penalty for doubled pawns on the same file. Negative for White's doubled, positive for Black's doubled (since good for White)."""
    score = 0
    for file in range(8):
        white_count = 0
        black_count = 0
        for rank in range(8):
            ch = board[rank][file]
            if ch == "P":
                white_count += 1
            elif ch == "p":
                black_count += 1
        if white_count > 1:
            score -= 10 * (white_count - 1)
        if black_count > 1:
            score += 10 * (black_count - 1)
    return score


def isolated_pawn_penalty(board: Board) -> int:
    """Penalty for isolated pawns (no friendly pawn on adjacent files)."""
    score = 0
    for r in range(8):
        for c in range(8):
            ch = board[r][c]
            if ch not in ("P", "p"):
                continue
            is_white = ch == "P"
            has_neighbor = False
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < 8:
                    for rr in range(8):
                        neighbor = board[rr][nc]
                        if is_white and neighbor == "P":
                            has_neighbor = True
                            break
                        if not is_white and neighbor == "p":
                            has_neighbor = True
                            break
                    if has_neighbor:
                        break
            if not has_neighbor:
                if is_white:
                    score -= 15
                else:
                    score += 15
    return score


def is_white_passed(board: Board, r: int, c: int) -> bool:
    for rr in range(0, r):  # rows in front of white pawn (towards 0)
        for dc in (-1, 0, 1):
            cc = c + dc
            if 0 <= cc < 8:
                if board[rr][cc] == "p":
                    return False
    return True


def is_black_passed(board: Board, r: int, c: int) -> bool:
    for rr in range(r + 1, 8):  # rows in front of black pawn (towards 7)
        for dc in (-1, 0, 1):
            cc = c + dc
            if 0 <= cc < 8:
                if board[rr][cc] == "P":
                    return False
    return True


def passed_pawn_bonus(board: Board) -> int:
    score = 0
    for r in range(8):
        for c in range(8):
            ch = board[r][c]
            if ch == "P" and is_white_passed(board, r, c):
                score += (7 - r) * 10  # closer to promotion (row 0) => bigger bonus
            elif ch == "p" and is_black_passed(board, r, c):
                score -= r * 10
    return score


def pawn_structure_term(board: Board) -> int:
    return (
        doubled_pawn_penalty(board)
        + isolated_pawn_penalty(board)
        + passed_pawn_bonus(board)
    )


# ----- King safety -----

def queens_on_board(board: Board) -> bool:
    for r in range(8):
        for c in range(8):
            if board[r][c] in ("Q", "q"):
                return True
    return False


def find_kings(board: Board) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
    w_king = b_king = None
    for r in range(8):
        for c in range(8):
            if board[r][c] == "K":
                w_king = (r, c)
            elif board[r][c] == "k":
                b_king = (r, c)
    return w_king, b_king


def king_safety_term(board: Board) -> int:
    score = 0
    if queens_on_board(board):
        w_king, b_king = find_kings(board)
        # Assume white starts at (7,4), black at (0,4)
        if w_king == (7, 4):
            score -= 25
        if b_king == (0, 4):
            score += 25
    return score


def evaluate(board: Board, side_to_move: str) -> int:
    """
    Static evaluation from White's perspective (centipawns).

    Args:
        board: 8x8 matrix of '.', 'P','p', ... uppercase=White, lowercase=Black
        side_to_move: 'w' or 'b' (currently unused, but kept for future tweaks)
    Returns:
        int: score in centipawns (>0 better for White)
    """
    score = 0
    # 1) Material
    score += material_term(board)
    # 2) Piece-square
    score += piece_square_term(board)
    # 3) Pawn structure
    score += pawn_structure_term(board)
    # 4) King safety
    score += king_safety_term(board)

    # (optional) later tweaks: tempo bonus, phase blending, mobility, etc.
    return score


__all__ = [
    "evaluate",
    "material_term",
    "piece_square_term",
    "pawn_structure_term",
    "king_safety_term",
]
