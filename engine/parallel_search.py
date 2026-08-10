"""Process-based root parallelism for Red Squirrel.

The pool is created lazily and kept alive between engine moves.  Each worker
owns its own transposition table, avoiding the synchronization cost of a
shared Python dictionary.  Parallelism is applied at the root, where tasks are
large enough to amortize Windows process and IPC overhead.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
import os
import time
from typing import Optional

from engine import search
from engine.search import Board, INF, Move, SearchState


_EXECUTOR: Optional[ProcessPoolExecutor] = None
_EXECUTOR_WORKERS = 0


def _default_worker_count() -> int:
    """Conservative default for hybrid CPUs such as the i7-14700."""
    return max(1, min(8, os.cpu_count() or 1))


def _get_executor(worker_count: int) -> ProcessPoolExecutor:
    global _EXECUTOR, _EXECUTOR_WORKERS
    worker_count = max(1, int(worker_count))
    if _EXECUTOR is None or _EXECUTOR_WORKERS != worker_count:
        shutdown_parallel_search()
        _EXECUTOR = ProcessPoolExecutor(
            max_workers=worker_count,
            mp_context=get_context("spawn"),
        )
        _EXECUTOR_WORKERS = worker_count
    return _EXECUTOR


def shutdown_parallel_search() -> None:
    """Release worker processes. Safe to call when no search is running."""
    global _EXECUTOR, _EXECUTOR_WORKERS
    if _EXECUTOR is not None:
        _EXECUTOR.shutdown(wait=True, cancel_futures=True)
        _EXECUTOR = None
        _EXECUTOR_WORKERS = 0


def _search_root_move(
    board: Board,
    st: SearchState,
    mv: Move,
    colour: int,
    depth: int,
    time_limit_s: Optional[float],
) -> tuple[Move, int, int, int, bool]:
    """Worker entry point; must remain module-level for Windows spawning."""
    search.NODES = 0
    search.Q_NODES = 0
    search.START_TIME = time.time()
    search.TIME_LIMIT = time_limit_s

    undo = search.make_move(board, mv, st)
    score = -search.nega_max(
        board, depth - 1, -INF, INF, -colour, st, ply=1
    )
    search.undo_move(board, undo, st)
    return mv, score, search.NODES, search.Q_NODES, search.time_up()


def find_best_move_parallel(
    board: Board,
    side_to_move: str,
    max_depth: int = search.DEFAULT_MAX_DEPTH,
    st: Optional[SearchState] = None,
    time_limit_s: Optional[float] = search.DEFAULT_TIME_LIMIT,
    worker_count: Optional[int] = None,
    verbose: bool = True,
) -> Optional[Move]:
    """Find a move with iterative deepening and process-based root splitting.

    Only fully completed iterations replace the selected move.  Depth one is
    searched locally because dispatch overhead is larger than the work there.
    """
    if st is None:
        st = SearchState()

    moves = search.generate_legal_moves(board, side_to_move, st)
    if not moves:
        return None

    moves.sort(key=lambda mv: search._move_order_key(board, mv), reverse=True)
    colour = 1 if side_to_move == "white" else -1
    workers = min(worker_count or _default_worker_count(), len(moves))

    # For a single worker, retain the stronger sequential alpha-beta behaviour.
    if workers <= 1:
        return search.find_best_move(
            board, side_to_move, max_depth, st, time_limit_s, verbose
        )

    started = time.time()
    deadline = None if time_limit_s is None else started + time_limit_s
    best_move: Optional[Move] = None
    best_score = -INF

    for depth in range(1, max_depth + 1):
        remaining = None if deadline is None else deadline - time.time()
        if remaining is not None and remaining <= 0:
            break

        depth_results: list[tuple[Move, int]] = []
        total_nodes = 0
        total_q_nodes = 0
        iteration_complete = True

        if depth == 1:
            # Avoid paying IPC costs for a one-ply iteration.
            search.NODES = 0
            search.Q_NODES = 0
            search.START_TIME = time.time()
            search.TIME_LIMIT = remaining
            for mv in moves:
                undo = search.make_move(board, mv, st)
                score = -search.nega_max(
                    board, 0, -INF, INF, -colour, st, ply=1
                )
                search.undo_move(board, undo, st)
                depth_results.append((mv, score))
                if deadline is not None and time.time() >= deadline:
                    iteration_complete = False
                    break
            total_nodes = search.NODES
            total_q_nodes = search.Q_NODES
        else:
            executor = _get_executor(workers)
            futures = [
                executor.submit(
                    _search_root_move,
                    [row[:] for row in board],
                    st,
                    mv,
                    colour,
                    depth,
                    remaining,
                )
                for mv in moves
            ]
            for future in as_completed(futures):
                mv, score, nodes, q_nodes, timed_out = future.result()
                depth_results.append((mv, score))
                total_nodes += nodes
                total_q_nodes += q_nodes
                if timed_out:
                    iteration_complete = False

            if len(depth_results) != len(moves):
                iteration_complete = False

        if not iteration_complete or not depth_results:
            break

        depth_results.sort(key=lambda item: item[1], reverse=True)
        best_move, best_score = depth_results[0]
        score_by_move = {move_key(mv): score for mv, score in depth_results}
        moves.sort(key=lambda mv: score_by_move[move_key(mv)], reverse=True)

        if verbose:
            elapsed = time.time() - started
            nodes = total_nodes + total_q_nodes
            nps = int(nodes / elapsed) if elapsed > 0 else 0
            print(
                f"[parallel search] side={side_to_move} depth={depth} "
                f"best_score={best_score} workers={workers} nodes={total_nodes} "
                f"q_nodes={total_q_nodes} time={elapsed:.2f}s nps={nps}"
            )

    # A very short time limit can interrupt depth one; always return a legal move.
    return best_move if best_move is not None else moves[0]


def move_key(mv: Move) -> tuple:
    return (
        mv.start,
        mv.end,
        mv.promotion,
        mv.is_castle,
        mv.is_en_passant,
    )


__all__ = ["find_best_move_parallel", "shutdown_parallel_search"]
