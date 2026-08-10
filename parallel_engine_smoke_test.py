from engine.parallel_search import find_best_move_parallel, shutdown_parallel_search
from engine.search import SearchState, generate_legal_moves


BOARD = [
    ["r", "n", "b", "q", "k", "b", "n", "r"],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
]


def main():
    state = SearchState()
    move = find_best_move_parallel(
        [row[:] for row in BOARD],
        "white",
        max_depth=2,
        st=state,
        worker_count=2,
        verbose=True,
    )
    legal_moves = generate_legal_moves(BOARD, "white", state)
    assert move in legal_moves, f"Parallel search returned illegal move: {move}"
    print("Parallel best move (depth 2):", move)
    shutdown_parallel_search()


if __name__ == "__main__":
    main()
