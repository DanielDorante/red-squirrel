"""
Alpha-beta Negamax search for ChessBot.

This module is UI-free and operates directly on the 8x8 board matrix used by main.py.
It uses evaluate(board) from evaluation.py and move generation from legal_moves.py.

Move representation: a lightweight dataclass carrying start, end, and optional promotion.
State: carries castling flags and last_pawn_move so special moves can be handled.

Features:
- Negamax + alpha-beta pruning
- Transposition table with Zobrist hashing
- Null move pruning (R=2, depth >= 3, with non-pawn material guard)
- MVV-LVA capture ordering (Most Valuable Victim / Least Valuable Attacker)
- Killer move heuristic (2 slots per ply)
- Quiescence search (captures / promotions / en passant only, bounded depth)
- Iterative deepening
- Optional time control per move
- Node counting for debugging / performance insight
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import time
import random

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
)

Board = List[List[str]]
Pos = Tuple[int, int]

INF = 10 ** 9

# --- Search configuration defaults ---

DEFAULT_MAX_DEPTH = 4          # search depth in plies (can be overridden per call)
DEFAULT_TIME_LIMIT = None      # seconds per move (None = no limit)

# --- Global search diagnostics / timing ---

NODES: int = 0
Q_NODES: int = 0
START_TIME: float = 0.0
TIME_LIMIT: Optional[float] = None  # set per search in find_best_move

# --- Transposition table & Zobrist hashing ---

_PIECES_ORDER = 'PNBRQKpnbrqk'
_PIECE_TO_IDX: dict = {p: i for i, p in enumerate(_PIECES_ORDER)}


def _make_zobrist():
    rng = random.Random(0x6A09E667F3BCC908)  # fixed seed for reproducibility
    pieces = [[rng.getrandbits(64) for _ in range(64)] for _ in range(12)]
    side   = rng.getrandbits(64)              # XOR in when black to move
    castle = [rng.getrandbits(64) for _ in range(4)]  # wK-side, wQ-side, bK-side, bQ-side
    ep     = [rng.getrandbits(64) for _ in range(8)]  # one entry per file
    return pieces, side, castle, ep


_Z_PIECES, _Z_SIDE, _Z_CASTLE, _Z_EP = _make_zobrist()


def _board_hash(board: Board, colour: int, st: 'SearchState') -> int:
    """Compute a Zobrist hash for the current position."""
    h = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p != '.':
                h ^= _Z_PIECES[_PIECE_TO_IDX[p]][r * 8 + c]
    if colour == -1:  # black to move
        h ^= _Z_SIDE
    # Castling availability (XOR key when castling is still legal)
    if not st.white_king_moved:
        if not st.white_rook_right_moved:
            h ^= _Z_CASTLE[0]
        if not st.white_rook_left_moved:
            h ^= _Z_CASTLE[1]
    if not st.black_king_moved:
        if not st.black_rook_right_moved:
            h ^= _Z_CASTLE[2]
        if not st.black_rook_left_moved:
            h ^= _Z_CASTLE[3]
    if st.last_pawn_move is not None:
        h ^= _Z_EP[st.last_pawn_move[1]]
    return h


_TT: dict = {}   # hash -> (depth, score, flag)
_TT_EXACT = 0    # score is exact
_TT_LOWER = 1    # score is a lower bound (fail-high / beta cutoff)
_TT_UPPER = 2    # score is an upper bound (fail-low / alpha cutoff)
_TT_MAX   = 1 << 20  # evict when TT exceeds ~1M entries

# --- Killer moves ---
_MAX_PLY = 64
_KILLERS: List[List] = [[None, None] for _ in range(_MAX_PLY)]

# --- Null move pruning ---
_NULL_R = 2  # depth reduction applied to the null-move search

# --- MVV-LVA piece values for capture ordering ---
_MVV_VALUES = {'P': 100, 'N': 300, 'B': 310, 'R': 500, 'Q': 900, 'K': 10000}

# --- Delta pruning for quiescence ---
_DELTA_MARGIN = 200   # safety margin: how much to add to a capture's gain before pruning
_BIG_DELTA    = 900   # maximum single-move gain (queen capture); used for bulk pruning


def _store_killer(ply: int, mv: 'Move') -> None:
    """Record a quiet move that caused a beta cutoff at this ply."""
    if ply >= _MAX_PLY:
        return
    k = _KILLERS[ply]
    # Don't store duplicates in slot 0
    if k[0] is None or k[0].start != mv.start or k[0].end != mv.end:
        k[1] = k[0]
        k[0] = mv


def _has_non_pawn_material(board: Board, side: str) -> bool:
    """Return True if side has at least one non-pawn, non-king piece.

    Used to guard null move pruning: skipping a move in a king-and-pawns-only
    endgame risks missing zugzwang positions.
    """
    targets = 'NBRQ' if side == 'white' else 'nbrq'
    for r in range(8):
        for c in range(8):
            if board[r][c] in targets:
                return True
    return False


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
    # En passant tracking: coordinates of the pawn that moved two squares last turn
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


def time_up() -> bool:
    """Return True if we've exceeded the per-move time limit."""
    if TIME_LIMIT is None:
        return False
    return (time.time() - START_TIME) >= TIME_LIMIT


def generate_legal_moves(
    board: Board,
    side_to_move: str,
    st: SearchState,
    tactical_only: bool = False,
) -> List[Move]:
    """
    Generate all legal moves for side_to_move.
    If tactical_only is True, only returns captures, promotions, and en-passant moves,
    and skips castling. This is used in quiescence search.
    """
    moves: List[Move] = []

    # 1) Normal piece moves (and promotions / en passant)
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
                        is_white = ch.isupper()
                        for p in ('q', 'r', 'b', 'n'):
                            prom_piece = get_promoted_piece(p, is_white)
                            mv = Move(start=(r, c), end=(er, ec), promotion=prom_piece)
                            # Promotions are always "tactical", so we don't filter them
                            moves.append(mv)
                    else:
                        # En passant hint
                        is_ep = False
                        if ch in 'Pp' and board[er][ec] == '.':
                            if abs(ec - c) == 1 and abs(er - r) == 1:
                                # Potential en passant capture; actual legality checked in make_move
                                is_ep = True

                        mv = Move(start=(r, c), end=(er, ec), is_en_passant=is_ep)

                        if tactical_only:
                            # Keep only captures or en-passant
                            if board[er][ec] == '.' and not mv.is_en_passant:
                                continue

                        moves.append(mv)

    # 2) Castling moves: skip if we're in tactical-only mode (quiescence)
    if not tactical_only:
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

    # Move the piece off its starting square
    board[sr][sc] = '.'

    # En passant capture (only if truly legal per last_pawn_move)
    if mv.is_en_passant and piece in 'Pp' and captured == '.':
        direction = get_pawn_direction(piece, st.white_on_bottom)
        cap_r = er - direction
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
        board[er][ec] = '.'
    else:
        board[er][ec] = undo.captured if undo.captured is not None else '.'

    # Restore piece to starting square
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


def _move_order_key(board: Board, mv: Move, killers: list = None) -> int:
    """
    Move ordering heuristic (higher score = searched earlier):
      1. Captures ordered by MVV-LVA (high-value victim, low-value attacker first)
      2. Promotions (queen promotion highest)
      3. Killer moves (quiet moves that caused cutoffs at this ply)
      4. Everything else at 0
    """
    er, ec = mv.end
    sr, sc = mv.start
    dest_piece = board[er][ec]
    score = 0

    if dest_piece != '.' or mv.is_en_passant:
        # MVV-LVA: big bonus, then victim value minus attacker value
        victim = _MVV_VALUES.get(dest_piece.upper(), 100) if dest_piece != '.' else 100  # ep = pawn capture
        attacker = _MVV_VALUES.get(board[sr][sc].upper(), 100)
        score += 20000 + victim - attacker

    if mv.promotion is not None:
        score += 15000 + _MVV_VALUES.get(mv.promotion.upper(), 0)

    # Killer moves: quiet moves that previously triggered a beta cutoff at this ply
    if killers and dest_piece == '.' and mv.promotion is None and not mv.is_en_passant:
        if killers[0] is not None and mv.start == killers[0].start and mv.end == killers[0].end:
            score += 10000
        elif killers[1] is not None and mv.start == killers[1].start and mv.end == killers[1].end:
            score += 9000

    return score


def quiescence(
    board: Board,
    alpha: int,
    beta: int,
    colour: int,
    st: SearchState,
    depth_q: int = 0,
    max_q_depth: int = 4,
) -> int:
    """
    Quiescence search with delta pruning.
    Extends tactical positions at leaves to avoid evaluating mid-capture positions.
    Searches captures, promotions, and en passant only.

    Delta pruning: skip captures whose maximum possible gain can't raise alpha,
    reducing node count significantly in complex tactical positions.

    colour = +1 for side 'white' to move, -1 for 'black'.
    """
    global Q_NODES
    Q_NODES += 1

    if time_up():
        return colour * evaluate(board, 'w')

    # Depth cap to avoid runaway capture trees
    if depth_q >= max_q_depth:
        return colour * evaluate(board, 'w')

    # Stand-pat evaluation
    stand_pat = colour * evaluate(board, 'w')
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    # Big-delta pruning: if even a queen capture can't raise alpha, bail early
    if stand_pat + _BIG_DELTA + _DELTA_MARGIN < alpha:
        return alpha

    side = side_str(colour)
    tactical_moves = generate_legal_moves(board, side, st, tactical_only=True)

    if not tactical_moves:
        return alpha

    tactical_moves.sort(key=lambda mv: _move_order_key(board, mv), reverse=True)

    for mv in tactical_moves:
        # Per-move delta pruning: skip captures whose gain can't possibly raise alpha
        # (always search promotions — they change material fundamentally)
        if mv.promotion is None:
            er, ec = mv.end
            dest = board[er][ec]
            gain = _MVV_VALUES.get(dest.upper(), 100) if dest != '.' else 100  # en passant = pawn
            if stand_pat + gain + _DELTA_MARGIN <= alpha:
                continue

        undo = make_move(board, mv, st)
        score = -quiescence(board, -beta, -alpha, -colour, st, depth_q + 1, max_q_depth)
        undo_move(board, undo, st)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def nega_max(
    board: Board,
    depth: int,
    alpha: int,
    beta: int,
    colour: int,
    st: SearchState,
    ply: int = 0,
    allow_null: bool = True,
) -> int:
    """
    Negamax with alpha-beta pruning, transposition table, null move pruning,
    MVV-LVA ordering, and killer move heuristic.
    colour = +1 for white to move, -1 for black to move.
    """
    global NODES
    NODES += 1

    if time_up():
        return colour * evaluate(board, 'w')

    alpha_orig = alpha

    # Transposition table lookup
    h = _board_hash(board, colour, st)
    tt_entry = _TT.get(h)
    if tt_entry is not None:
        tt_depth, tt_score, tt_flag = tt_entry
        if tt_depth >= depth:
            if tt_flag == _TT_EXACT:
                return tt_score
            elif tt_flag == _TT_LOWER:
                alpha = max(alpha, tt_score)
            elif tt_flag == _TT_UPPER:
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score

    side = side_str(colour)
    in_check = is_in_check(side, board, st.white_on_bottom)

    # Generate legal moves (also needed for terminal detection)
    moves = generate_legal_moves(board, side, st)

    # Terminal node: no legal moves
    if not moves:
        return -INF + 1 if in_check else 0

    # Depth cutoff (only after confirming position is non-terminal)
    if depth == 0:
        return quiescence(board, alpha, beta, colour, st)

    # --- Null move pruning ---
    # If we can hand the turn to the opponent and they still can't beat beta,
    # our position is so good we can cut without searching further.
    # Disabled in check, at low depths, and when only pawns remain (zugzwang risk).
    if (allow_null and not in_check and depth >= 3
            and _has_non_pawn_material(board, side)):
        prev_lpm = st.last_pawn_move
        st.last_pawn_move = None          # passing forfeits en passant rights
        null_score = -nega_max(
            board, depth - _NULL_R - 1, -beta, -beta + 1,
            -colour, st, ply + 1, allow_null=False,
        )
        st.last_pawn_move = prev_lpm
        if null_score >= beta:
            return beta  # fail-high: cut this branch

    # Move ordering: captures (MVV-LVA) → promotions → killers → quiet moves
    killers = _KILLERS[ply] if ply < _MAX_PLY else [None, None]
    moves.sort(key=lambda mv: _move_order_key(board, mv, killers), reverse=True)

    value = -INF

    for mv in moves:
        er, ec = mv.end
        is_quiet = board[er][ec] == '.' and mv.promotion is None and not mv.is_en_passant

        undo = make_move(board, mv, st)
        score = -nega_max(board, depth - 1, -beta, -alpha, -colour, st, ply + 1)
        undo_move(board, undo, st)

        if score > value:
            value = score
        if value > alpha:
            alpha = value
        if alpha >= beta:
            if is_quiet:           # only store quiet cutoffs as killers
                _store_killer(ply, mv)
            break  # beta cutoff

    # Store result in transposition table
    if not time_up():
        flag = _TT_EXACT
        if value <= alpha_orig:
            flag = _TT_UPPER
        elif value >= beta:
            flag = _TT_LOWER
        _TT[h] = (depth, value, flag)

    return value


def find_best_move(
    board: Board,
    side_to_move: str,
    max_depth: int = DEFAULT_MAX_DEPTH,
    st: Optional[SearchState] = None,
    time_limit_s: Optional[float] = DEFAULT_TIME_LIMIT,
    verbose: bool = True,
) -> Optional[Move]:
    """
    Root search: returns the best Move for side_to_move.

    Uses iterative deepening up to max_depth, optionally limited by time_limit_s.
    If time_limit_s is None, search is depth-limited only.
    """
    global NODES, Q_NODES, START_TIME, TIME_LIMIT

    if st is None:
        st = SearchState()

    colour = 1 if side_to_move == 'white' else -1
    opponent = 'black' if side_to_move == 'white' else 'white'

    # Reset diagnostics
    NODES = 0
    Q_NODES = 0
    START_TIME = time.time()
    TIME_LIMIT = time_limit_s

    # Evict transposition table if it's grown too large
    if len(_TT) > _TT_MAX:
        _TT.clear()

    # Reset killer table for this search
    for _i in range(_MAX_PLY):
        _KILLERS[_i][0] = None
        _KILLERS[_i][1] = None

    # Generate root moves once
    moves = generate_legal_moves(board, side_to_move, st)
    if not moves:
        return None

    # Order them once before iterative deepening
    moves.sort(key=lambda mv: _move_order_key(board, mv), reverse=True)

    best_move: Optional[Move] = None
    best_score = -INF

    # Iterative deepening: search depths 1..max_depth
    for depth in range(1, max_depth + 1):
        if time_up():
            break

        depth_best_move = None
        depth_best_score = -INF

        for mv in moves:
            if time_up():
                break

            undo = make_move(board, mv, st)
            score = -nega_max(board, depth - 1, -INF, INF, -colour, st, ply=1)
            undo_move(board, undo, st)

            if score > depth_best_score or depth_best_move is None:
                depth_best_score = score
                depth_best_move = mv

        if depth_best_move is not None:
            best_move = depth_best_move
            best_score = depth_best_score

        if verbose:
            elapsed = time.time() - START_TIME
            nps = int(NODES / elapsed) if elapsed > 0 else 0
            print(
                f"[search] side={side_to_move} depth={depth} "
                f"best_score={best_score} nodes={NODES} q_nodes={Q_NODES} "
                f"time={elapsed:.2f}s nps={nps}"
            )

        if time_up():
            break

    return best_move


__all__ = [
    'SearchState',
    'Move',
    'find_best_move',
    'nega_max',
    'generate_legal_moves',
    'make_move',
    'undo_move',
]
