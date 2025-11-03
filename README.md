# ChessBot

A Pygame-based chess game with clean algebraic move history, smart disambiguation, check/checkmate detection, material tracking, pawn promotion UI, and a board flip option so you can play from White or Black's perspective.

## ✨ Features

- Standard chess rules: legal move validation, check, checkmate, stalemate
- Castling, en passant, and pawn promotion (Q/R/B/N)
- Promotion UI appears on the promotion square (forced selection)
- Algebraic notation move history (e.g., `1. e4 e5 2. Nf3 Nc6`)
  - Includes captures (x), checks (+), checkmates (#), castling (O-O/O-O-O), and promotion (`=Q`)
  - Smart disambiguation (e.g., `Nbd2` vs `Nfd2`)
- Material tracking with captured pieces and relative advantage (e.g., `White +3`)
- Visual indicator when a king is in check (red square)
- Settings gear with “Flip Board” to play from either side
- Modular code structure for easier maintenance

## 🖼️ UI Overview

- Left: 8x8 board (60px squares) with labels
- Top/Bottom: Material advantage bars
- Right: Move history panel
- Top-right: Settings gear → Flip Board
- Promotion: A dropdown appears on the promotion square; select Q/R/B/N

## 🚀 Getting Started

### Requirements

- Python 3.9+
- Pygame

Install Pygame:

```powershell
python -m pip install pygame
```

### Run the game

From the project folder:

```powershell
cd "c:\Users\dpdor\VScode Projects\ChessBot"
python main.py
```

## 🎮 How to Play

- Click a piece to select it. Legal destination squares are highlighted.
- Click a highlighted square to move.
- Captures, checks, and checkmates are tracked in the move history.
- Promotion: When a pawn reaches the last rank, a dropdown appears on that square. Click a piece (Q/R/B/N) to promote (you must choose to continue the game).
- Flip Board: Click the gear icon (top-right) → Flip Board. This flips the view only; rules and turns remain unchanged.

## 📁 Project Structure

```
ChessBot/
├─ main.py                    # Game loop, rendering, input, UI (gear, promotion)
├─ legal_moves.py             # Move generation, rules (check, mate, stalemate, castling, en passant)
├─ move_history.py            # Algebraic notation and history panel
├─ disambiguation.py          # Smart disambiguation for notation
├─ material_tracker.py        # Captures and relative material advantage
├─ chess_pieces/              # PNG assets for all pieces
│  ├─ white_*.png
│  └─ black_*.png
└─ README.md                  # This file
```

## 🧠 Design Notes

- Display orientation is decoupled from rules. Internally:
  - White pawns move toward row 0; Black toward row 7.
  - Castling uses fixed king/rook squares by color.
- The view layer handles flipping (drawing and click mapping), so gameplay logic is consistent regardless of orientation.

## 🧪 Troubleshooting

- "ModuleNotFoundError: No module named 'pygame'"
  - Install pygame: `python -m pip install pygame`
  - Ensure you’re using the same Python interpreter in VS Code as in your terminal.
- Window doesn’t fit screen
  - The window is 680x560. If it’s clipped, try maximizing or adjusting display scaling.
- Promotion dropdown off-screen
  - The dropdown auto-adjusts based on square position and board orientation. If you see a layout issue, please open an issue with a screenshot.

## 🗺️ Roadmap Ideas

- Player vs. Engine (Stockfish/UCI integration)
- Move undo/redo
- Timers and move clocks
- PGN export/import
- Per-square move hints and last move highlight

## 📸 Screenshots

You can add screenshots to the repo and link them here:

```
/docs/screenshot-1.png
/docs/screenshot-2.png
```

Then reference with:

```md
![Game](docs/screenshot-1.png)
```

## 📜 License

Choose a license (MIT is common for small projects). Add a `LICENSE` file and update this section.

---

Contributions and suggestions welcome. Enjoy playing and hacking on ChessBot! 🎉
