import pygame
from legal_moves import is_in_check, is_checkmate, is_stalemate, get_promoted_piece

class PromotionController:
    """
    Handles pawn promotion state, UI, and completion.
    Internal board coordinates are used; display orientation is handled via
    white_on_bottom when drawing and hit-testing.
    """
    def __init__(self):
        self.pending = False
        self.from_pos = None
        self.to_pos = None
        self.is_white_pawn = None
        self.is_capture = False
        self.captured_piece = None

    def start(self, from_pos, to_pos, is_white_pawn, is_capture=False, captured_piece=None):
        self.pending = True
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.is_white_pawn = is_white_pawn
        self.is_capture = is_capture
        self.captured_piece = captured_piece

    def reset(self):
        self.pending = False
        self.from_pos = None
        self.to_pos = None
        self.is_white_pawn = None
        self.is_capture = False
        self.captured_piece = None

    # ---------- UI ----------
    def _promotion_square_screen_pos(self, white_on_bottom, square_size=60, board_offset_y=40):
        end_row, end_col = self.to_pos
        # Convert to display coordinates
        if white_on_bottom:
            display_row, display_col = end_row, end_col
        else:
            display_row, display_col = 7 - end_row, 7 - end_col
        square_x = display_col * square_size
        square_y = board_offset_y + display_row * square_size
        return square_x, square_y, display_row

    def draw(self, screen, piece_images, white_on_bottom, square_size=60, board_offset_y=40):
        if not self.pending:
            return

        square_x, square_y, display_row = self._promotion_square_screen_pos(white_on_bottom, square_size, board_offset_y)

        # Highlight the square
        promotion_rect = (square_x, square_y, square_size, square_size)
        pygame.draw.rect(screen, (255, 215, 0), promotion_rect)
        pygame.draw.rect(screen, (255, 165, 0), promotion_rect, 4)

        # Dropdown config
        dropdown_width = square_size
        dropdown_height = square_size * 4
        dropdown_x = square_x
        # Open up if visually in lower half; else open down
        if display_row >= 4:
            dropdown_y = square_y - dropdown_height + square_size
        else:
            dropdown_y = square_y

        # Background
        pygame.draw.rect(screen, (255, 255, 255), (dropdown_x, dropdown_y, dropdown_width, dropdown_height))
        pygame.draw.rect(screen, (0, 0, 0), (dropdown_x, dropdown_y, dropdown_width, dropdown_height), 3)

        # Options (Q, R, B, N)
        promotion_pieces = ['Q', 'R', 'B', 'N']
        for i, piece_type in enumerate(promotion_pieces):
            option_y = dropdown_y + i * square_size
            # Proper case by color
            piece_key = piece_type if self.is_white_pawn else piece_type.lower()
            option_rect = (dropdown_x, option_y, dropdown_width, square_size)
            pygame.draw.rect(screen, (240, 240, 240), option_rect)
            pygame.draw.rect(screen, (100, 100, 100), option_rect, 2)
            piece_image = pygame.transform.scale(piece_images[piece_key], (square_size - 10, square_size - 10))
            screen.blit(piece_image, (dropdown_x + 5, option_y + 5))

            # Hover
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if dropdown_x <= mouse_x <= dropdown_x + dropdown_width and option_y <= mouse_y <= option_y + square_size:
                pygame.draw.rect(screen, (200, 200, 255), option_rect, 3)

        # Instruction
        font_small = pygame.font.Font(None, 20)
        text = font_small.render("PROMOTION REQUIRED", True, (255, 255, 255))
        text_rect = text.get_rect()
        text_x = dropdown_x + dropdown_width + 10
        text_y = dropdown_y + dropdown_height // 2 - text_rect.height // 2
        padding = 5
        text_bg_rect = (text_x - padding, text_y - padding, text_rect.width + padding * 2, text_rect.height + padding * 2)
        pygame.draw.rect(screen, (255, 0, 0), text_bg_rect)
        pygame.draw.rect(screen, (255, 255, 255), text_bg_rect, 2)
        screen.blit(text, (text_x, text_y))
        arrow_points = [
            (text_x - 15, text_y + text_rect.height // 2),
            (text_x - 5, text_y + text_rect.height // 2 - 5),
            (text_x - 5, text_y + text_rect.height // 2 + 5)
        ]
        pygame.draw.polygon(screen, (255, 255, 255), arrow_points)

    def handle_click(self, pos, white_on_bottom, square_size=60, board_offset_y=40):
        if not self.pending:
            return None
        x, y = pos
        square_x, square_y, display_row = self._promotion_square_screen_pos(white_on_bottom, square_size, board_offset_y)

        dropdown_width = square_size
        dropdown_height = square_size * 4
        dropdown_x = square_x
        if display_row >= 4:
            dropdown_y = square_y - dropdown_height + square_size
        else:
            dropdown_y = square_y

        # Hit test
        if not (dropdown_x <= x <= dropdown_x + dropdown_width and dropdown_y <= y <= dropdown_y + dropdown_height):
            return None
        relative_y = y - dropdown_y
        option_index = relative_y // square_size
        if 0 <= option_index < 4:
            return ['Q', 'R', 'B', 'N'][int(option_index)]
        return None

    def complete(self, selected_piece_type, board_state, current_turn, move_history, material_tracker, white_on_bottom):
        """Apply the promotion to the board, update material and notation.
        Returns True when completed so the caller can switch turns.
        """
        end_row, end_col = self.to_pos
        promoted_piece = get_promoted_piece(selected_piece_type, self.is_white_pawn)
        board_state[end_row][end_col] = promoted_piece

        # Material adjustments
        if self.is_capture and self.captured_piece:
            material_tracker.capture_piece(self.captured_piece, current_turn)
        material_tracker.promote_pawn(promoted_piece, current_turn)

        # Check/checkmate state
        opponent_color = "black" if current_turn == "white" else "white"
        is_check = is_in_check(opponent_color, board_state, white_on_bottom)
        is_checkmate_result = False
        is_stalemate_result = False
        if is_check:
            is_checkmate_result = is_checkmate(opponent_color, board_state, white_on_bottom)
        else:
            is_stalemate_result = is_stalemate(opponent_color, board_state, white_on_bottom)

        # Notation with promotion
        piece_char = 'P' if self.is_white_pawn else 'p'
        move_notation = move_history.convert_to_algebraic_notation(
            self.from_pos, self.to_pos, piece_char, board_state,
            is_capture=self.is_capture, is_check=is_check, is_checkmate=is_checkmate_result,
            promotion_piece=selected_piece_type
        )
        move_history.add_move(move_notation, current_turn == "white")

        # Reset state
        self.reset()
        return True
