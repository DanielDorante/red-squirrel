import pygame
import renderer
from promotion import PromotionController
from move_history import MoveHistory
from material_tracker import MaterialTracker
from legal_moves import (
    calculate_valid_moves, is_in_check, is_checkmate, is_stalemate, 
    leaves_king_in_check, en_passant, calculate_castling_moves,
    get_pawn_direction, get_pawn_start_row, get_pawn_promotion_row,
    is_promotion_move, get_promoted_piece
)

pygame.init()
screen = pygame.display.set_mode((680,560))  # Expanded height for material displays
pygame.display.set_caption("Chess Bot")

# ==============================
# Configuration
# ==============================
white_on_bottom = True

# Engine hook (example):
# from evaluation import evaluate
# score_cp = evaluate(board_state, 'w')  # + = good for White

# Colors
light_color = (240,217,181)
dark_color = (181,136,99)
label_color = (0,0,0)

font = pygame.font.Font(None,24)
move_history = MoveHistory(font)
material_tracker = MaterialTracker()
selected_square = None
valid_moves = []  
current_turn = "white" 
last_pawn_move = None 

# Promotion controller
promotion = PromotionController()

# Settings state
settings_dropdown_open = False 

# Castling rules
white_king_moved = False
white_rook_left_moved = False
white_rook_right_moved = False
black_king_moved = False
black_rook_left_moved = False
black_rook_right_moved = False

# Piece declaration
piece_images = {
    "P": pygame.image.load("chess_pieces/white_pawn.png"),
    "B": pygame.image.load("chess_pieces/white_bishop.png"),
    "R": pygame.image.load("chess_pieces/white_rook.png"),
    "Q": pygame.image.load("chess_pieces/white_queen.png"),
    "K": pygame.image.load("chess_pieces/white_king.png"),
    "N": pygame.image.load("chess_pieces/white_knight.png"),
    "p": pygame.image.load("chess_pieces/black_pawn.png"),
    "b": pygame.image.load("chess_pieces/black_bishop.png"),
    "r": pygame.image.load("chess_pieces/black_rook.png"),
    "q": pygame.image.load("chess_pieces/black_queen.png"),
    "k": pygame.image.load("chess_pieces/black_king.png"),
    "n": pygame.image.load("chess_pieces/black_knight.png"),
}

# Define the board_state depending on orientation
if white_on_bottom:
    # White at bottom (original arrangement)
    board_state = [
        ["r", "n", "b", "q", "k", "b", "n", "r"],
        ["p", "p", "p", "p", "p", "p", "p", "p"],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        ["P", "P", "P", "P", "P", "P", "P", "P"],
        ["R", "N", "B", "Q", "K", "B", "N", "R"],
    ]
else:
    # White at top, Black at bottom (flipped)
    board_state = [
        ["R", "N", "B", "Q", "K", "B", "N", "R"],
        ["P", "P", "P", "P", "P", "P", "P", "P"],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        ["p", "p", "p", "p", "p", "p", "p", "p"],
        ["r", "n", "b", "q", "k", "b", "n", "r"],
    ]

## moved to renderer.draw_board

## moved to renderer.draw_pieces

## moved to renderer.draw_labels

def get_square_from_mouse(pos):
    x, y = pos
    board_offset_y = 40  # Offset for material display at top
    
    # Make sure click is within board bounds (480x480 board area, offset by 40px)
    if x < 0 or x >= 480 or y < board_offset_y or y >= board_offset_y + 480:
        return -1, -1  # Invalid position
    
    # Get the display coordinates (what square was visually clicked)
    display_row = (y - board_offset_y) // 60  
    display_col = x // 60  
    
    # Convert display coordinates to internal board coordinates
    if white_on_bottom:
        # Normal orientation: display matches internal
        row, col = display_row, display_col
    else:
        # Flipped orientation: convert display back to internal
        row, col = 7 - display_row, 7 - display_col
    
    return row, col

## Promotion UI moved to promotion.PromotionController

def draw_settings_gear():
    """Draw the settings gear icon in the top-right corner"""
    gear_size = 30
    gear_x = 680 - gear_size - 10  # 10px from right edge
    gear_y = 10  # 10px from top
    
    # Draw gear background
    gear_color = (150, 150, 150) if not settings_dropdown_open else (100, 100, 100)
    pygame.draw.circle(screen, gear_color, (gear_x + gear_size//2, gear_y + gear_size//2), gear_size//2)
    pygame.draw.circle(screen, (50, 50, 50), (gear_x + gear_size//2, gear_y + gear_size//2), gear_size//2, 2)
    
    # Draw simple gear teeth (8 small rectangles around the circle)
    center_x, center_y = gear_x + gear_size//2, gear_y + gear_size//2
    import math
    for i in range(8):
        angle = i * (2 * math.pi / 8)
        tooth_x = center_x + math.cos(angle) * (gear_size//2 - 3)
        tooth_y = center_y + math.sin(angle) * (gear_size//2 - 3)
        pygame.draw.circle(screen, (80, 80, 80), (int(tooth_x), int(tooth_y)), 3)
    
    # Draw center hole
    pygame.draw.circle(screen, (200, 200, 200), (center_x, center_y), 6)
    pygame.draw.circle(screen, (50, 50, 50), (center_x, center_y), 6, 2)
    
    return (gear_x, gear_y, gear_size, gear_size)  # Return gear bounds for click detection

def draw_settings_dropdown():
    """Draw the settings dropdown menu"""
    if not settings_dropdown_open:
        return None
    
    dropdown_width = 120
    dropdown_height = 50
    dropdown_x = 680 - dropdown_width - 10  # Align with gear
    dropdown_y = 50  # Below the gear
    
    # Draw dropdown background
    pygame.draw.rect(screen, (240, 240, 240), (dropdown_x, dropdown_y, dropdown_width, dropdown_height))
    pygame.draw.rect(screen, (100, 100, 100), (dropdown_x, dropdown_y, dropdown_width, dropdown_height), 2)
    
    # Draw "Flip Board" option
    option_height = dropdown_height
    option_rect = (dropdown_x, dropdown_y, dropdown_width, option_height)
    
    # Check if mouse is hovering over option
    mouse_x, mouse_y = pygame.mouse.get_pos()
    is_hovering = (dropdown_x <= mouse_x <= dropdown_x + dropdown_width and 
                   dropdown_y <= mouse_y <= dropdown_y + option_height)
    
    if is_hovering:
        pygame.draw.rect(screen, (200, 220, 255), option_rect)  # Light blue hover
    
    # Draw option text
    font_small = pygame.font.Font(None, 18)
    text = font_small.render("Flip Board", True, (0, 0, 0))
    text_rect = text.get_rect()
    text_x = dropdown_x + (dropdown_width - text_rect.width) // 2
    text_y = dropdown_y + (option_height - text_rect.height) // 2
    screen.blit(text, (text_x, text_y))
    
    return option_rect  # Return bounds for click detection

def handle_settings_click(pos):
    """Handle clicks on settings gear and dropdown"""
    global settings_dropdown_open, white_on_bottom
    
    x, y = pos
    
    # Check gear click
    gear_bounds = draw_settings_gear()  # This returns the bounds
    gear_x, gear_y, gear_width, gear_height = gear_bounds
    
    if gear_x <= x <= gear_x + gear_width and gear_y <= y <= gear_y + gear_height:
        settings_dropdown_open = not settings_dropdown_open
        return True  # Consumed the click
    
    # Check dropdown click if open
    if settings_dropdown_open:
        dropdown_bounds = draw_settings_dropdown()
        if dropdown_bounds:
            dropdown_x, dropdown_y, dropdown_width, dropdown_height = dropdown_bounds
            if dropdown_x <= x <= dropdown_x + dropdown_width and dropdown_y <= y <= dropdown_y + dropdown_height:
                # Flip board option clicked
                white_on_bottom = not white_on_bottom
                settings_dropdown_open = False  # Close dropdown after selection
                print(f"Board flipped! white_on_bottom = {white_on_bottom}")
                return True  # Consumed the click
        else:
            # Click outside dropdown, close it
            settings_dropdown_open = False
            return True
    
    return False  # Click not consumed

## Promotion logic moved to promotion.PromotionController

def handle_click(pos):
    global selected_square, valid_moves, last_pawn_move, current_turn
    
    # Check settings clicks first
    if handle_settings_click(pos):
        return  # Settings click was handled
    
    # If promotion is pending, handle promotion selection
    if promotion.pending:
        selected_piece = promotion.handle_click(pos, white_on_bottom)
        if selected_piece:
            if promotion.complete(selected_piece, board_state, current_turn, move_history, material_tracker, white_on_bottom):
                switch_turn()
        return
    
    row, col = get_square_from_mouse(pos)
    
    # Check for invalid position (clicked outside board)
    if row == -1 or col == -1 or not (0 <= row < 8 and 0 <= col < 8):
        return

    if selected_square:
        if (row, col) == selected_square:
            deselect()
        elif (row, col) in valid_moves:
            piece = board_state[selected_square[0]][selected_square[1]]
            end_row, end_col = row, col

            original_piece_at_start = board_state[selected_square[0]][selected_square[1]]
            original_piece_at_end = board_state[end_row][end_col]
            last_pawn_move_backup = last_pawn_move

            # Check if this is a capture and track material
            is_capture = board_state[end_row][end_col] != "."
            captured_piece = board_state[end_row][end_col] if is_capture else None
            
            is_en_passant_capture = en_passant(selected_square, (end_row, end_col), piece, board_state, last_pawn_move, white_on_bottom)
            if is_en_passant_capture:
                is_capture = True
                # For en passant, the captured piece is the pawn that moved two squares
                direction = get_pawn_direction(piece, white_on_bottom)
                captured_pawn_row = end_row - direction
                captured_piece = board_state[captured_pawn_row][end_col]

            # Check if this is castling
            is_castling = piece in "Kk" and abs(selected_square[1] - end_col) == 2
            castle_side = None
            if is_castling:
                castle_side = "kingside" if end_col > selected_square[1] else "queenside"

            # Check for pawn promotion BEFORE making the move
            is_promotion = is_promotion_move(selected_square, (end_row, end_col), board_state, white_on_bottom)
            if piece in "Pp":  # Debug: Only log for pawn moves
                print(f"Debug: Pawn move from {selected_square} to {(end_row, end_col)}, is_promotion: {is_promotion}")
                print(f"Debug: Piece: {piece}, end_row: {end_row}")
                if piece == "P":
                    print(f"Debug: White pawn moving to row {end_row} (promotion if row 0)")
                else:
                    print(f"Debug: Black pawn moving to row {end_row} (promotion if row 7)")

            move_piece(selected_square, (end_row, end_col))

            if is_en_passant_capture:
                direction = get_pawn_direction(piece, white_on_bottom)
                captured_pawn_row = end_row - direction
                board_state[captured_pawn_row][end_col] = "."

            if not is_in_check(current_turn, board_state, white_on_bottom):
                if piece in "Kk" and abs(selected_square[1] - end_col) == 2:
                    move_king_and_rook(selected_square, (end_row, end_col), piece)

                # Handle pawn promotion
                if is_promotion:
                    promotion.start(selected_square, (end_row, end_col), piece.isupper(), is_capture, captured_piece)
                    deselect()
                    return  # Exit early, wait for promotion selection

                if piece in "Pp":
                    direction = get_pawn_direction(piece)
                    start_r = get_pawn_start_row(piece)
                    if abs(end_row - selected_square[0]) == 2:
                        last_pawn_move = (end_row, end_col)
                    else:
                        last_pawn_move = None
                else:
                    last_pawn_move = None

                # Track material capture
                if is_capture and captured_piece:
                    material_tracker.capture_piece(captured_piece, current_turn)
                
                # Check if the move puts opponent in check or checkmate
                opponent_color = "black" if current_turn == "white" else "white"
                is_check = is_in_check(opponent_color, board_state, white_on_bottom)
                is_checkmate_result = False
                is_stalemate_result = False
                
                if is_check:
                    is_checkmate_result = is_checkmate(opponent_color, board_state, white_on_bottom)
                    # Debug: print to console when checkmate is detected
                    if is_checkmate_result:
                        print(f"CHECKMATE DETECTED! {opponent_color} is in checkmate")
                else:
                    # Check for stalemate only if not in check
                    is_stalemate_result = is_stalemate(opponent_color, board_state, white_on_bottom)
                    if is_stalemate_result:
                        print(f"STALEMATE DETECTED! {opponent_color} has no legal moves")
                
                # Generate move notation and add to history
                move_notation = move_history.convert_to_algebraic_notation(
                    selected_square, (end_row, end_col), piece, board_state,
                    is_capture=is_capture, is_check=is_check, is_checkmate=is_checkmate_result,
                    is_castling=is_castling, castle_side=castle_side
                )
                
                # Debug: print the move notation
                print(f"Move notation: {move_notation}")
                
                is_white_move = current_turn == "white"
                move_history.add_move(move_notation, is_white_move)

                switch_turn()
            else:
                # Undo move
                board_state[selected_square[0]][selected_square[1]] = original_piece_at_start
                board_state[end_row][end_col] = original_piece_at_end
                last_pawn_move = last_pawn_move_backup

                if is_en_passant_capture:
                    direction = get_pawn_direction(piece, white_on_bottom)
                    captured_pawn_row = end_row - direction
                    enemy_piece = "p" if piece == "P" else "P"
                    board_state[captured_pawn_row][end_col] = enemy_piece

            deselect()
        else:
            deselect()
    else:
        selected_square = (row, col)
        piece = board_state[row][col]
        if piece != "." and ((piece.isupper() and current_turn == "white") or (piece.islower() and current_turn == "black")):
            valid_moves = calculate_valid_moves(selected_square, board_state, white_on_bottom)
            valid_moves = [
                move for move in valid_moves
                if not leaves_king_in_check(selected_square, move, board_state, current_turn, white_on_bottom, last_pawn_move)
            ]
            valid_moves.extend(calculate_castling_moves(row, col, piece, board_state, white_on_bottom,
                                                      white_king_moved, white_rook_left_moved, white_rook_right_moved,
                                                      black_king_moved, black_rook_left_moved, black_rook_right_moved))
        else:
            deselect()

def move_piece(start, end):
    global board_state
    piece = board_state[start[0]][start[1]]
    board_state[start[0]][start[1]] = "."
    board_state[end[0]][end[1]] = piece
    update_castling_flags(piece, start, end)

def move_king_and_rook(start, end, piece):
    global board_state
    row, col = start
    target_row, target_col = end

    board_state[row][col] = "."
    board_state[target_row][target_col] = piece

    if piece == "K":
        if target_col == col + 2:
            board_state[7][7] = "."
            board_state[7][5] = "R"
        elif target_col == col - 2:
            board_state[7][0] = "."
            board_state[7][3] = "R"
    elif piece == "k":
        if target_col == col + 2:
            board_state[0][7] = "."
            board_state[0][5] = "r"
        elif target_col == col - 2:
            board_state[0][0] = "."
            board_state[0][3] = "r"

    update_castling_flags(piece, start, end)

def update_castling_flags(piece, start, end):
    global white_king_moved, white_rook_left_moved, white_rook_right_moved
    global black_king_moved, black_rook_left_moved, black_rook_right_moved

    if piece == "K":
        white_king_moved = True
    elif piece == "k":
        black_king_moved = True
    elif piece == "R":
        if start == (7, 0):
            white_rook_left_moved = True
        elif start == (7, 7):
            white_rook_right_moved = True
    elif piece == "r":
        if start == (0, 0):
            black_rook_left_moved = True
        elif start == (0, 7):
            black_rook_right_moved = True

def highlight_moves(moves):
    square_size = 60
    board_offset_y = 40  # Offset for material display at top
    highlight_color = (0, 255, 0, 128)

    for move in moves:
        r, c = move
        # Calculate display position based on board orientation
        if white_on_bottom:
            display_row, display_col = r, c
        else:
            display_row, display_col = 7 - r, 7 - c
        
        surface = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
        surface.fill(highlight_color)
        screen.blit(surface, (display_col * square_size, board_offset_y + display_row * square_size))

def draw_material_displays():
    """Draw material advantage displays at top and bottom of screen"""
    # Background colors
    material_bg_color = (240, 240, 240)
    border_color = (100, 100, 100)
    
    # Top display (black player in standard orientation)
    top_player = "black" if white_on_bottom else "white"
    bottom_player = "white" if white_on_bottom else "black"
    
    # Draw top material display
    top_rect = pygame.Rect(0, 0, 480, 35)
    pygame.draw.rect(screen, material_bg_color, top_rect)
    pygame.draw.rect(screen, border_color, top_rect, 2)
    
    # Draw bottom material display  
    bottom_rect = pygame.Rect(0, 525, 480, 35)
    pygame.draw.rect(screen, material_bg_color, bottom_rect)
    pygame.draw.rect(screen, border_color, bottom_rect, 2)
    
    # Get material advantage text
    top_advantage = material_tracker.get_display_text(top_player)
    bottom_advantage = material_tracker.get_display_text(bottom_player)
    
    # Draw player names and advantages
    top_text = f"{top_player.title()} {top_advantage}".strip()
    bottom_text = f"{bottom_player.title()} {bottom_advantage}".strip()
    
    # Render and draw text
    top_surface = font.render(top_text, True, (0, 0, 0))
    bottom_surface = font.render(bottom_text, True, (0, 0, 0))
    
    screen.blit(top_surface, (10, 8))
    screen.blit(bottom_surface, (10, 533))
    
    # Draw captured pieces (small icons)
    draw_captured_pieces_display(top_player, 10, 20)
    draw_captured_pieces_display(bottom_player, 10, 545)

def draw_captured_pieces_display(player, start_x, start_y):
    """Draw small icons of captured pieces"""
    captured_pieces = material_tracker.get_captured_pieces_display(player)
    
    x_offset = start_x + 150  # Start after player name
    piece_size = 12
    spacing = 15
    
    for i, piece in enumerate(captured_pieces):
        if piece in piece_images:
            # Create small version of piece image
            small_piece = pygame.transform.scale(piece_images[piece], (piece_size, piece_size))
            screen.blit(small_piece, (x_offset + i * spacing, start_y))

def deselect():
    global selected_square, valid_moves
    selected_square = None  
    valid_moves = []  

def switch_turn():
    global current_turn
    current_turn = "black" if current_turn == "white" else "white"


#####  game loop #####
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            handle_click(mouse_pos)
    
    # Clear screen
    screen.fill((50, 50, 50))  # Dark background
    
    # Draw material displays at top and bottom
    renderer.draw_material_displays(screen, font, white_on_bottom, material_tracker, piece_images)
    
    # Draw game elements (board stays in original position)
    renderer.draw_board(screen, board_state, light_color, dark_color, white_on_bottom)
    
    # Only highlight moves if not in promotion mode
    if not promotion.pending:
        renderer.highlight_moves(screen, valid_moves, white_on_bottom)
    
    renderer.draw_pieces(screen, board_state, piece_images, white_on_bottom)
    renderer.draw_labels(screen, font, label_color, white_on_bottom)
    
    # Draw move history panel (always visible on the right)
    move_history.draw(screen)
    
    # Draw settings gear and dropdown
    draw_settings_gear()
    draw_settings_dropdown()
    
    # Draw promotion UI if needed
    if promotion.pending:
        promotion.draw(screen, piece_images, white_on_bottom)
    
    pygame.display.flip()
pygame.quit()
