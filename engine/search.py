"""
Alpha-beta Negamax search for ChessBot.

This module is UI-free and operates directly on the 8x8 board matrix used by main.py.
It uses evaluate(board) from evaluation.py and move generation from legal_moves.py.

Move representation: a lightweight dataclass carrying start, end, and optional promotion.
State: carries castling flags and last_pawn_move so special moves can be handled.

This version includes:
- Single legal-move generation per node (no duplicate work for terminal checks)
- Basic move ordering (captures, promotions, en passant first) to improve alpha-beta pruning
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple

from evaluation import evaluate
from legal_moves import (
    calculate_valid_moves,
    leaves_king_in_check,
    calculate_castling_moves,
    is_in_check,
    is_promotion_move,
    get_promoted_piece,
    en_passant,
    get_pawn_direction,
    get_pawn_start_row,  # currently unused, but kept in case you use it elsewhere
)

Board = List[List[str]]
Pos = Tuple[int, int]

INF = 10**9


@dataclass
class SearchState:
    white_on_bottom: bool = True
    # Castling flags
    white_king_moved: bool = False
    white_rook_left_moved: bool = False
    white_rook_right_moved: bool = False
    black_king_moved: bool = False
    black_rook_left_moved: bool = False
    black_rook_right_moved: bool = False
    # En passant tracking: coordinates of the pawn that moved two last turn
    last_pawn_move: Optional[Pos] = None


@dataclass
class Move:
    start: Pos
    end: Pos
    promotion: Optional[str] = None  # 'q','r','b','n' (lowercase for black, uppercase for white)
    is_castle: bool = False
    is_en_passant: bool = False


def side_str(colour: int) -> str:
    return 'white' if colour == 1 else 'black'


def generate_legal_moves(board: Board, side_to_move: str, st: SearchState) -> List[Move]:
    moves: List[Move] = []
    # 1) Normal piece moves
    for r in range(8):
        for c in range(8):
            ch = board[r][c]
            if ch == '.':
                continue
            if (side_to_move == 'white' and ch.isupper()) or (side_to_move == 'black' and ch.islower()):
                dests = calculate_valid_moves((r, c), board, st.white_on_bottom, st.last_pawn_move)
                for (er, ec) in dests:
                    # Filter illegal (king-in-check) moves
                    if leaves_king_in_check((r, c), (er, ec), board, side_to_move, st.white_on_bottom, st.last_pawn_move):
                        continue
                    # Prevent illegal diagonal pawn moves into empty squares unless en passant is legal
                    if ch in 'Pp' and board[er][ec] == '.' and abs(ec - c) == 1 and abs(er - r) == 1:
                        if not en_passant((r, c), (er, ec), ch, board, st.last_pawn_move, st.white_on_bottom):
                            continue
                    # Promotions: if pawn and promotion square
                    if is_promotion_move((r, c), (er, ec), board, st.white_on_bottom):
                        # Generate four promotion choices
                        is_white = ch.isupper()
                        for p in ('q', 'r', 'b', 'n'):
                            prom_piece = get_promoted_piece(p, is_white)
                            moves.append(Move(start=(r, c), end=(er, ec), promotion=prom_piece))
                    else:
                        # En passant hint (for make/undo)
                        is_ep = False
                        if ch in 'Pp' and board[er][ec] == '.':
                            # diagonal move into empty square could be en passant; defer exact check to make_move
                            if abs(ec - c) == 1 and abs(er - r) == 1:
                                is_ep = True
                        moves.append(Move(start=(r, c), end=(er, ec), is_en_passant=is_ep))

    # 2) Castling moves
    # Find the king square and ask for castling squares using flags.
    for r in range(8):
        for c in range(8):
            ch = board[r][c]
            if ch == '.':
                continue
            if side_to_move == 'white' and ch == 'K':
                castles = calculate_castling_moves(
                    r, c, ch, board, st.white_on_bottom,
                    st.white_king_moved, st.white_rook_left_moved, st.white_rook_right_moved,
                    st.black_king_moved, st.black_rook_left_moved, st.black_rook_right_moved,
                )
                for (er, ec) in castles:
                    if not leaves_king_in_check((r, c), (er, ec), board, 'white', st.white_on_bottom, st.last_pawn_move):
                        moves.append(Move(start=(r, c), end=(er, ec), is_castle=True))
            elif side_to_move == 'black' and ch == 'k':
                castles = calculate_castling_moves(
                    r, c, ch, board, st.white_on_bottom,
                    st.white_king_moved, st.white_rook_left_moved, st.white_rook_right_moved,
                    st.black_king_moved, st.black_rook_left_moved, st.black_rook_right_moved,
                )
                for (er, ec) in castles:
                    if not leaves_king_in_check((r, c), (er, ec), board, 'black', st.white_on_bottom, st.last_pawn_move):
                        moves.append(Move(start=(r, c), end=(er, ec), is_castle=True))
    return moves


@dataclass
class Undo:
    captured: Optional[str]
    ep_captured_pos: Optional[Pos]
    prev_last_pawn_move: Optional[Pos]
    prev_flags: Tuple[bool, bool, bool, bool, bool, bool]
    moved_piece: str
    start: Pos
    end: Pos
    was_en_passant: bool


def make_move(board: Board, mv: Move, st: SearchState) -> Undo:
    sr, sc = mv.start
    er, ec = mv.end
    piece = board[sr][sc]
    captured = board[er][ec]

    prev_last_pawn_move = st.last_pawn_move
    prev_flags = (
        st.white_king_moved, st.white_rook_left_moved, st.white_rook_right_moved,
        st.black_king_moved, st.black_rook_left_moved, st.black_rook_right_moved,
    )

    ep_captured_pos: Optional[Pos] = None
    was_en_passant = False

    # Move the piece
    board[sr][sc] = '.'

    # En passant capture (only if truly legal per last_pawn_move)
    if mv.is_en_passant and piece in 'Pp' and captured == '.':
        direction = get_pawn_direction(piece, st.white_on_bottom)
        cap_r = er - direction
        # EP is legal only if the pawn being captured is exactly last_pawn_move
        if st.last_pawn_move == (cap_r, ec) and board[cap_r][ec] in ('p' if piece == 'P' else 'P'):
            ep_captured_pos = (cap_r, ec)
            captured = board[cap_r][ec]
            board[cap_r][ec] = '.'
            was_en_passant = True

    # Place the moving piece (handle promotion)
    place_piece = mv.promotion if mv.promotion else piece
    board[er][ec] = place_piece

    # Handle castling rook movement and flags
    if piece == 'K':
        st.white_king_moved = True
        if mv.is_castle:
            if ec == sc + 2:  # king-side
                board[7][7] = '.'
                board[7][5] = 'R'
            elif ec == sc - 2:  # queen-side
                board[7][0] = '.'
                board[7][3] = 'R'
    elif piece == 'k':
        st.black_king_moved = True
        if mv.is_castle:
            if ec == sc + 2:
                board[0][7] = '.'
                board[0][5] = 'r'
            elif ec == sc - 2:
                board[0][0] = '.'
                board[0][3] = 'r'
    elif piece == 'R' and (sr, sc) == (7, 0):
        st.white_rook_left_moved = True
    elif piece == 'R' and (sr, sc) == (7, 7):
        st.white_rook_right_moved = True
    elif piece == 'r' and (sr, sc) == (0, 0):
        st.black_rook_left_moved = True
    elif piece == 'r' and (sr, sc) == (0, 7):
        st.black_rook_right_moved = True

    # Update last_pawn_move for double-step pawn pushes
    if piece in 'Pp' and mv.promotion is None:
        if abs(er - sr) == 2 and sc == ec:
            st.last_pawn_move = (er, ec)
        else:
            st.last_pawn_move = None
    else:
        st.last_pawn_move = None

    return Undo(
        captured=captured,
        ep_captured_pos=ep_captured_pos,
        prev_last_pawn_move=prev_last_pawn_move,
        prev_flags=prev_flags,
        moved_piece=piece,
        start=mv.start,
        end=mv.end,
        was_en_passant=was_en_passant,
    )


def undo_move(board: Board, undo: Undo, st: SearchState):
    sr, sc = undo.start
    er, ec = undo.end
    moved = board[er][ec]

    # Undo special rook moves if castling
    if moved in ('K', 'k') and abs(ec - sc) == 2:
        if moved == 'K':
            if ec == sc + 2:
                board[7][5] = '.'
                board[7][7] = 'R'
            elif ec == sc - 2:
                board[7][3] = '.'
                board[7][0] = 'R'
        else:
            if ec == sc + 2:
                board[0][5] = '.'
                board[0][7] = 'r'
            elif ec == sc - 2:
                board[0][3] = '.'
                board[0][0] = 'r'

    # Restore destination square
    if undo.was_en_passant:
        # For EP, destination was empty prior to move
        board[er][ec] = '.'
    else:
        board[er][ec] = undo.captured if undo.captured is not None else '.'
    board[sr][sc] = undo.moved_piece

    # Restore en passant-captured pawn if any
    if undo.ep_captured_pos is not None and undo.captured is not None:
        cr, cc = undo.ep_captured_pos
        board[cr][cc] = undo.captured

    # Restore flags and last pawn move
    (
        st.white_king_moved, st.white_rook_left_moved, st.white_rook_right_moved,
        st.black_king_moved, st.black_rook_left_moved, st.black_rook_right_moved,
    ) = undo.prev_flags
    st.last_pawn_move = undo.prev_last_pawn_move


def _move_order_key(board: Board, mv: Move) -> int:
    """
    Heuristic for move ordering:
    - Captures, promotions, and en-passant first.
    Higher returned value = searched earlier.
    """
    er, ec = mv.end
    dest_piece = board[er][ec]
    score = 0

    # Captures (including en passant)
    if dest_piece != '.':
        score += 1000
    if mv.is_en_passant:
        score += 1000

    # Promotions
    if mv.promotion is not None:
        score += 900

    # You can add more heuristics later (e.g., checks, killer moves, history)

    return score


def nega_max(board: Board, depth: int, alpha: int, beta: int, colour: int, st: SearchState) -> int:
    """
    Negamax with alpha-beta pruning.
    colour = +1 for white to move, -1 for black to move.
    """
    side = side_str(colour)
    moves = generate_legal_moves(board, side, st)

    # Terminal node: no legal moves
    if not moves:
        if is_in_check(side, board, st.white_on_bottom):
            return -INF + 1  # checkmate is terrible for side to move
        else:
            return 0  # stalemate

    # Depth cutoff (only after verifying it's not terminal)
    if depth == 0:
        # evaluate(board, 'w') should return from White's POV,
        # so multiply by colour to flip for Black.
        return colour * evaluate(board, 'w')

    # Move ordering: good moves first → more pruning
    moves.sort(key=lambda mv: _move_order_key(board, mv), reverse=True)

    value = -INF

    for mv in moves:
        undo = make_move(board, mv, st)
        score = -nega_max(board, depth - 1, -beta, -alpha, -colour, st)
        undo_move(board, undo, st)

        if score > value:
            value = score
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break  # beta cutoff

    return value


def find_best_move(board: Board, side_to_move: str, depth: int, st: Optional[SearchState] = None) -> Optional[Move]:
    """
    Root search: returns the best Move for side_to_move at given depth.
    """
    if st is None:
        st = SearchState()

    colour = 1 if side_to_move == 'white' else -1
    best_move: Optional[Move] = None
    best_score = -INF

    moves = generate_legal_moves(board, side_to_move, st)
    if not moves:
        return None

    # Tactical shortcut: if any move is immediate checkmate, return it right away (mate-in-1)
    opponent = 'black' if side_to_move == 'white' else 'white'
    for mv in moves:
        undo = make_move(board, mv, st)
        opp_moves = generate_legal_moves(board, opponent, st)
        is_mate = (not opp_moves) and is_in_check(opponent, board, st.white_on_bottom)
        undo_move(board, undo, st)
        if is_mate:
            return mv

    # Same ordering as in nega_max
    moves.sort(key=lambda mv: _move_order_key(board, mv), reverse=True)

    for mv in moves:
        undo = make_move(board, mv, st)
        score = -nega_max(board, depth - 1, -INF, INF, -colour, st)
        undo_move(board, undo, st)

        if score > best_score:
            best_score = score
            best_move = mv

    return best_move


__all__ = [
    'SearchState',
    'Move',
    'find_best_move',
    'nega_max',
    'generate_legal_moves',
]
