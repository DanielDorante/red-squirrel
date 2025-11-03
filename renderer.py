import pygame
from legal_moves import is_in_check

SQUARE_SIZE = 60
BOARD_OFFSET_Y = 40


def draw_board(screen, board_state, light_color, dark_color, white_on_bottom):
    for row in range(8):
        for col in range(8):
            # Visual square coordinates based on orientation
            if white_on_bottom:
                display_row, display_col = row, col
            else:
                display_row, display_col = 7 - row, 7 - col

            color = light_color if (row + col) % 2 == 0 else dark_color

            # Highlight king in check
            piece = board_state[row][col]
            if (piece == "K" and is_in_check("white", board_state, white_on_bottom)) or (
                piece == "k" and is_in_check("black", board_state, white_on_bottom)
            ):
                color = (255, 100, 100)

            pygame.draw.rect(
                screen,
                color,
                (display_col * SQUARE_SIZE, BOARD_OFFSET_Y + display_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
            )


def draw_pieces(screen, board_state, piece_images, white_on_bottom):
    for r in range(8):
        for c in range(8):
            piece = board_state[r][c]
            if piece == ".":
                continue
            if white_on_bottom:
                display_row, display_col = r, c
            else:
                display_row, display_col = 7 - r, 7 - c
            img = pygame.transform.scale(piece_images[piece], (SQUARE_SIZE, SQUARE_SIZE))
            screen.blit(img, (display_col * SQUARE_SIZE, BOARD_OFFSET_Y + display_row * SQUARE_SIZE))


def draw_labels(screen, font, label_color, white_on_bottom):
    letters = "abcdefgh"
    numbers = "87654321"

    if white_on_bottom:
        # Files along bottom
        for col, letter in enumerate(letters):
            text = font.render(letter, True, label_color)
            text_width, text_height = font.size(letter)
            x = (col + 1) * SQUARE_SIZE - text_width - 5
            y = BOARD_OFFSET_Y + 8 * SQUARE_SIZE - text_height - 5
            screen.blit(text, (x, y))
        # Ranks along left
        for row, number in enumerate(numbers):
            text = font.render(number, True, label_color)
            x = 5
            y = BOARD_OFFSET_Y + row * SQUARE_SIZE + 5
            screen.blit(text, (x, y))
    else:
        reversed_letters = letters[::-1]
        reversed_numbers = numbers[::-1]
        # Files along top
        for col, letter in enumerate(reversed_letters):
            text = font.render(letter, True, label_color)
            text_width, text_height = font.size(letter)
            x = (col + 1) * SQUARE_SIZE - text_width - 5
            y = BOARD_OFFSET_Y + 5
            screen.blit(text, (x, y))
        # Ranks along right
        for row, number in enumerate(reversed_numbers):
            text = font.render(number, True, label_color)
            text_width, text_height = font.size(number)
            x = (8 * SQUARE_SIZE) - text_width - 5
            y = BOARD_OFFSET_Y + row * SQUARE_SIZE + 5
            screen.blit(text, (x, y))


def highlight_moves(screen, moves, white_on_bottom):
    highlight_color = (0, 255, 0, 128)
    for (r, c) in moves:
        if not white_on_bottom:
            display_row, display_col = 7 - r, 7 - c
        else:
            display_row, display_col = r, c
        surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        surface.fill(highlight_color)
        screen.blit(surface, (display_col * SQUARE_SIZE, BOARD_OFFSET_Y + display_row * SQUARE_SIZE))


def draw_captured_pieces_display(screen, piece_images, material_tracker, player, start_x, start_y):
    captured_pieces = material_tracker.get_captured_pieces_display(player)
    x_offset = start_x + 150
    piece_size = 12
    spacing = 15
    for i, piece in enumerate(captured_pieces):
        if piece in piece_images:
            small_piece = pygame.transform.scale(piece_images[piece], (piece_size, piece_size))
            screen.blit(small_piece, (x_offset + i * spacing, start_y))


def draw_material_displays(screen, font, white_on_bottom, material_tracker, piece_images):
    material_bg_color = (240, 240, 240)
    border_color = (100, 100, 100)

    top_player = "black" if white_on_bottom else "white"
    bottom_player = "white" if white_on_bottom else "black"

    top_rect = pygame.Rect(0, 0, 480, 35)
    pygame.draw.rect(screen, material_bg_color, top_rect)
    pygame.draw.rect(screen, border_color, top_rect, 2)

    bottom_rect = pygame.Rect(0, 525, 480, 35)
    pygame.draw.rect(screen, material_bg_color, bottom_rect)
    pygame.draw.rect(screen, border_color, bottom_rect, 2)

    top_advantage = material_tracker.get_display_text(top_player)
    bottom_advantage = material_tracker.get_display_text(bottom_player)

    top_text = f"{top_player.title()} {top_advantage}".strip()
    bottom_text = f"{bottom_player.title()} {bottom_advantage}".strip()

    top_surface = font.render(top_text, True, (0, 0, 0))
    bottom_surface = font.render(bottom_text, True, (0, 0, 0))

    screen.blit(top_surface, (10, 8))
    screen.blit(bottom_surface, (10, 533))

    draw_captured_pieces_display(screen, piece_images, material_tracker, top_player, 10, 20)
    draw_captured_pieces_display(screen, piece_images, material_tracker, bottom_player, 10, 545)
