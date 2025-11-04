"""
Quick smoke tests for evaluation.py. Run directly with Python.

Expected (approximate) outcomes:
- Kings only: ~0
- Kings + white pawn only: ~+95 (material +100 with small pawn-structure adjustments)
- Kings + black rook only: about -500
- Knight PSQT: center should be ~70 cp better than corner
"""
from evaluation import evaluate


def empty_board():
    return [["."] * 8 for _ in range(8)]


def print_board(board):
    for r in range(8):
        print(" ".join(board[r]))
    print()


def main():
    # 1) Baseline: only kings, no queens -> 0
    b1 = empty_board()
    b1[7][4] = 'K'
    b1[0][4] = 'k'
    v1 = evaluate(b1, 'w')
    print('baseline kings only:', v1)

    # 2) Extra white pawn (material ~ +100), aware pawn structure adds small terms
    b2 = [row[:] for row in b1]
    b2[6][0] = 'P'
    v2 = evaluate(b2, 'w')
    print('white pawn only:', v2)

    # 3) Extra black rook -> about -500
    b3 = [row[:] for row in b1]
    b3[0][0] = 'r'
    v3 = evaluate(b3, 'w')
    print('black rook only:', v3)

    # 4) Knight PSQT: center vs corner
    b4_corner = [row[:] for row in b1]
    b4_corner[7][0] = 'N'
    val_corner = evaluate(b4_corner, 'w')

    b4_center = [row[:] for row in b1]
    b4_center[3][3] = 'N'
    val_center = evaluate(b4_center, 'w')
    print('knight psqt corner:', val_corner, ' center:', val_center, ' diff:', val_center - val_corner)


if __name__ == '__main__':
    main()
