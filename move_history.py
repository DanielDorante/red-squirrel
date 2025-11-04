import pygame
from disambiguation import get_disambiguation

class MoveHistory:
    def __init__(self, font):
        self.moves = []  # List of tuples: (white_move, black_move or None)
        self.font = font
        self.panel_width = 200
        self.panel_height = 560  # Updated for new screen height
        self.panel_x = 480  # Always on the right side
        self.background_color = (240, 240, 240)
        self.text_color = (0, 0, 0)
        self.border_color = (100, 100, 100)
        self.scroll_y = 0  # pixels scrolled from top
        
    def toggle_visibility(self):
        """Toggle the move history panel visibility"""
        self.visible = not self.visible
        
    def add_move(self, move_notation, is_white_move):
        """Add a move to the history in algebraic notation"""
        if is_white_move:
            # Start a new move pair
            self.moves.append((move_notation, None))
        else:
            # Complete the current move pair
            if self.moves and self.moves[-1][1] is None:
                white_move = self.moves[-1][0]
                self.moves[-1] = (white_move, move_notation)
            else:
                # This shouldn't happen in normal play, but handle it
                self.moves.append((None, move_notation))
    
    def convert_to_algebraic_notation(self, start_pos, end_pos, piece, board_state, is_capture=False, 
                                    is_check=False, is_checkmate=False, is_castling=False, 
                                    castle_side=None, promotion_piece=None):
        """Convert a move to standard algebraic notation"""
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        
        # Handle castling
        if is_castling:
            if castle_side == "kingside":
                return "O-O"
            elif castle_side == "queenside":
                return "O-O-O"
        
        # Convert positions to algebraic notation
        files = "abcdefgh"
        ranks = "87654321" if True else "12345678"  # Assuming white_on_bottom = True
        
        end_square = files[end_col] + ranks[end_row]
        
        notation = ""
        
        # For pawns, just use the destination square (e.g., "e4") unless it's a capture
        if piece.upper() == "P":
            if is_capture:
                # For pawn captures, include the starting file (e.g., "exd5")
                notation += files[start_col] + "x" + end_square
            else:
                # Simple pawn move, just the destination (e.g., "e4")
                notation = end_square
        else:
            # Add piece letter for non-pawns
            notation += piece.upper()
            
            # Check for ambiguity using the dedicated disambiguation module
            disambiguation = get_disambiguation(start_pos, end_pos, piece, board_state)
            notation += disambiguation
            
            # Add capture notation
            if is_capture:
                notation += "x"
            
            # Add destination square
            notation += end_square
        
        # Add promotion
        if promotion_piece:
            notation += "=" + promotion_piece.upper()
        
        # Add check/checkmate notation
        # Important: If it's checkmate, use # instead of + (even though checkmate implies check)
        print(f"Debug: is_checkmate={is_checkmate}, is_check={is_check}")  # Debug line
        if is_checkmate:
            notation += "#"
            print(f"Debug: Added # to notation: {notation}")  # Debug line
        elif is_check:
            notation += "+"
            print(f"Debug: Added + to notation: {notation}")  # Debug line
            
        return notation
    
    def _get_disambiguation(self, start_pos, end_pos, piece, board_state, calculate_moves_func):
        """Determine if disambiguation is needed and return the appropriate notation"""
        if not calculate_moves_func:
            return ""  # Fallback if function not provided
            
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        files = "abcdefgh"
        ranks = "87654321"
        
        print(f"Debug disambiguation: piece={piece}, start=({start_row},{start_col}), end=({end_row},{end_col})")
        
        # Find all pieces of the same type and color that could move to the same square
        pieces_that_can_reach_target = []
        for row in range(8):
            for col in range(8):
                if board_state[row][col] == piece and (row, col) != start_pos:
                    print(f"Debug: Found same piece {piece} at ({row},{col})")
                    # Get valid moves for this piece and check if target square is reachable
                    try:
                        possible_moves = calculate_moves_func((row, col))
                        print(f"Debug: Piece at ({row},{col}) can move to: {possible_moves}")
                        if (end_row, end_col) in possible_moves:
                            pieces_that_can_reach_target.append((row, col))
                            print(f"Debug: Piece at ({row},{col}) CAN reach target ({end_row},{end_col})")
                        else:
                            print(f"Debug: Piece at ({row},{col}) CANNOT reach target ({end_row},{end_col})")
                    except Exception as e:
                        print(f"Debug: Error calculating moves for piece at ({row},{col}): {e}")
        
        print(f"Debug: Pieces that can reach target: {pieces_that_can_reach_target}")
        
        # If no other pieces can reach the target, no disambiguation needed
        if not pieces_that_can_reach_target:
            print("Debug: No disambiguation needed")
            return ""
        
        # Check what type of disambiguation is needed
        same_file_pieces = [pos for pos in pieces_that_can_reach_target if pos[1] == start_col]
        same_rank_pieces = [pos for pos in pieces_that_can_reach_target if pos[0] == start_row]
        
        print(f"Debug: same_file_pieces: {same_file_pieces}, same_rank_pieces: {same_rank_pieces}")
        
        if same_file_pieces and same_rank_pieces:
            # Need full square disambiguation (both file and rank conflicts)
            result = files[start_col] + ranks[start_row]
            print(f"Debug: Full disambiguation needed: {result}")
            return result
        elif same_file_pieces:
            # Need rank disambiguation (file conflicts)
            result = ranks[start_row]
            print(f"Debug: Rank disambiguation needed: {result}")
            return result
        else:
            # Need file disambiguation (rank conflicts or no conflicts)
            result = files[start_col]
            print(f"Debug: File disambiguation needed: {result}")
            return result
    
    def draw(self, screen):
        """Draw the move history panel with scrolling support"""
        # Draw background panel
        panel_rect = pygame.Rect(self.panel_x, 0, self.panel_width, self.panel_height)
        pygame.draw.rect(screen, self.background_color, panel_rect)
        pygame.draw.rect(screen, self.border_color, panel_rect, 2)
        
        # Draw title
        title_text = self.font.render("Move History", True, self.text_color)
        screen.blit(title_text, (self.panel_x + 10, 10))
        
        # Draw moves with scrolling
        start_y = 50 - self.scroll_y
        line_height = 25
        content_height = 50 + len(self.moves) * line_height + 10
        visible_top = 0
        visible_bottom = self.panel_height

        for i, (white_move, black_move) in enumerate(self.moves):
            y = start_y + i * line_height
            if y < visible_top - line_height or y > visible_bottom - 20:
                continue

            move_number = i + 1
            move_text = f"{move_number}. "
            if white_move:
                move_text += white_move
            if black_move:
                move_text += f" {black_move}"
            text_surface = self.font.render(move_text, True, self.text_color)
            screen.blit(text_surface, (self.panel_x + 10, y))

        # Scrollbar
        if content_height > self.panel_height:
            track_margin = 8
            track_x = self.panel_x + self.panel_width - track_margin - 6
            track_y = 10
            track_w = 6
            track_h = self.panel_height - 20
            pygame.draw.rect(screen, (210, 210, 210), (track_x, track_y, track_w, track_h))
            pygame.draw.rect(screen, (160, 160, 160), (track_x, track_y, track_w, track_h), 1)

            visible_ratio = self.panel_height / content_height
            thumb_h = max(20, int(track_h * visible_ratio))
            max_scroll = max(0, content_height - self.panel_height)
            scroll_ratio = 0 if max_scroll == 0 else min(1, max(0, self.scroll_y / max_scroll))
            thumb_y = track_y + int((track_h - thumb_h) * scroll_ratio)
            pygame.draw.rect(screen, (120, 120, 120), (track_x, thumb_y, track_w, thumb_h))

    def scroll_lines(self, lines: int):
        line_height = 25
        self.scroll_pixels(lines * line_height)

    def scroll_pixels(self, pixels: int):
        self.scroll_y = max(0, self.scroll_y + pixels)
        # Clamp to content height
        line_height = 25
        content_height = 50 + len(self.moves) * line_height + 10
        max_scroll = max(0, content_height - self.panel_height)
        if self.scroll_y > max_scroll:
            self.scroll_y = max_scroll

    def handle_wheel(self, mouse_pos, wheel_y):
        """wheel_y: positive when scrolled up in Pygame.
        Scroll only if mouse is over the move history panel.
        """
        mx, my = mouse_pos
        if self.panel_x <= mx <= self.panel_x + self.panel_width and 0 <= my <= self.panel_height:
            # Scroll 3 lines per notch for a snappy feel; invert so wheel up moves content up
            self.scroll_lines(-3 * wheel_y)
    
    def clear_history(self):
        """Clear all moves from history"""
        self.moves = []
    
    def get_last_move(self):
        """Get the last move made"""
        if not self.moves:
            return None
        last_move = self.moves[-1]
        if last_move[1] is not None:  # Black move exists
            return last_move[1]
        elif last_move[0] is not None:  # Only white move
            return last_move[0]
        return None
    
    def export_pgn_moves(self):
        """Export moves in PGN format"""
        pgn_moves = []
        for i, (white_move, black_move) in enumerate(self.moves):
            move_number = i + 1
            move_pair = f"{move_number}."
            if white_move:
                move_pair += f" {white_move}"
            if black_move:
                move_pair += f" {black_move}"
            pgn_moves.append(move_pair)
        return " ".join(pgn_moves)
    
    def toggle_visibility(self):
        """Removed - panel is always visible"""
        pass