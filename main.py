import pygame
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

# Promotion state
promotion_pending = False
promotion_from = None
promotion_to = None
promotion_piece_color = None
promotion_is_capture = False
promotion_captured_piece = None

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

def draw_board():
    square_size = 60
    board_offset_y = 40  # Offset for material display at top
    for row in range(8):
        for col in range(8):
            # Calculate display position based on board orientation
            if white_on_bottom:
                display_row, display_col = row, col
            else:
                display_row, display_col = 7 - row, 7 - col
            
            color = light_color if (row+col) % 2 == 0 else dark_color
            
            # Check if this square has a king that's in check
            piece = board_state[row][col]
            king_in_check = False
            if piece == "K" and is_in_check("white", board_state, white_on_bottom):
                king_in_check = True
            elif piece == "k" and is_in_check("black", board_state, white_on_bottom):
                king_in_check = True
            
            # If king is in check, make the square red
            if king_in_check:
                color = (255, 100, 100)  # Red color for check
            
            pygame.draw.rect(screen, color, (display_col * square_size, board_offset_y + display_row * square_size, square_size, square_size))

def draw_pieces(board):
    square_size = 60
    board_offset_y = 40  # Offset for material display at top
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != ".":
                # Calculate display position based on board orientation
                if white_on_bottom:
                    display_row, display_col = r, c
                else:
                    display_row, display_col = 7 - r, 7 - c
                
                piece_image = pygame.transform.scale(piece_images[piece], (square_size, square_size))
                screen.blit(piece_image, (display_col * square_size, board_offset_y + display_row * square_size))

def draw_labels():
    letters = "abcdefgh"
    numbers = "87654321"  
    square_size = 60
    board_offset_y = 40  # Offset for material display at top

    if white_on_bottom:
        for col, letter in enumerate(letters):
            text = font.render(letter, True, label_color)
            text_width, text_height = font.size(letter)
            x = (col + 1) * square_size - text_width - 5
            y = board_offset_y + 8 * square_size - text_height - 5
            screen.blit(text, (x, y))

        for row, number in enumerate(numbers):
            text = font.render(number, True, label_color)
            x = 5
            y = board_offset_y + row * square_size + 5
            screen.blit(text, (x, y))
    else:
        reversed_letters = letters[::-1]  # h to a
        reversed_numbers = numbers[::-1]  # 1 to 8
        for col, letter in enumerate(reversed_letters):
            text = font.render(letter, True, label_color)
            text_width, text_height = font.size(letter)
            # Letters at top now (row 0 area)
            x = (col + 1) * square_size - text_width - 5
            y = board_offset_y + 5  # top edge now
            screen.blit(text, (x, y))

        # Numbers along the right side now:
        for row, number in enumerate(reversed_numbers):
            text = font.render(number, True, label_color)
            text_width, text_height = font.size(number)
            x = (8 * square_size) - text_width - 5
            y = board_offset_y + row * square_size + 5
            screen.blit(text, (x, y))

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

def draw_promotion_dialog():
    """Draw the promotion piece selection dropdown on the promotion square"""
    if not promotion_pending:
        return
    
    # Get the promotion square position
    end_row, end_col = promotion_to
    square_size = 60
    board_offset_y = 40
    
    # Calculate display position based on board orientation
    if white_on_bottom:
        display_row, display_col = end_row, end_col
    else:
        display_row, display_col = 7 - end_row, 7 - end_col
    
    # Calculate screen position of the promotion square
    square_x = display_col * square_size
    square_y = board_offset_y + display_row * square_size
    
    # Dropdown configuration
    dropdown_width = square_size
    dropdown_height = square_size * 4  # 4 pieces stacked vertically
    
    # Position dropdown relative to display position so it stays on-screen
    # If the square is visually near the bottom half, open upwards; otherwise open downwards
    if display_row >= 4:
        dropdown_y = square_y - dropdown_height + square_size  # open up
    else:
        dropdown_y = square_y  # open down
    
    dropdown_x = square_x
    
    # Draw dropdown background with border
    pygame.draw.rect(screen, (255, 255, 255), (dropdown_x, dropdown_y, dropdown_width, dropdown_height))
    pygame.draw.rect(screen, (0, 0, 0), (dropdown_x, dropdown_y, dropdown_width, dropdown_height), 3)
    
    # Draw promotion piece options (Queen, Rook, Bishop, Knight)
    promotion_pieces = ['Q', 'R', 'B', 'N']
    
    for i, piece_type in enumerate(promotion_pieces):
        option_y = dropdown_y + i * square_size
        
        # Get the correct piece based on color
        if promotion_piece_color:  # White
            piece = piece_type
        else:  # Black
            piece = piece_type.lower()
        
        # Draw piece option background
        option_rect = (dropdown_x, option_y, dropdown_width, square_size)
        pygame.draw.rect(screen, (240, 240, 240), option_rect)
        pygame.draw.rect(screen, (100, 100, 100), option_rect, 2)
        
        # Draw piece image
        piece_image = pygame.transform.scale(piece_images[piece], (square_size - 10, square_size - 10))
        screen.blit(piece_image, (dropdown_x + 5, option_y + 5))
        
        # Highlight on hover (optional enhancement)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if dropdown_x <= mouse_x <= dropdown_x + dropdown_width and option_y <= mouse_y <= option_y + square_size:
            pygame.draw.rect(screen, (200, 200, 255), option_rect, 3)
    
    # Draw instruction text
    font_small = pygame.font.Font(None, 20)
    text = font_small.render("PROMOTION REQUIRED", True, (255, 255, 255))
    text_rect = text.get_rect()
    text_x = dropdown_x + dropdown_width + 10
    text_y = dropdown_y + dropdown_height // 2 - text_rect.height // 2
    
    # Draw text background
    padding = 5
    text_bg_rect = (text_x - padding, text_y - padding, 
                   text_rect.width + padding * 2, text_rect.height + padding * 2)
    pygame.draw.rect(screen, (255, 0, 0), text_bg_rect)  # Red background for urgency
    pygame.draw.rect(screen, (255, 255, 255), text_bg_rect, 2)
    
    screen.blit(text, (text_x, text_y))
    
    # Add an arrow pointing to the dropdown
    arrow_points = [
        (text_x - 15, text_y + text_rect.height // 2),
        (text_x - 5, text_y + text_rect.height // 2 - 5),
        (text_x - 5, text_y + text_rect.height // 2 + 5)
    ]
    pygame.draw.polygon(screen, (255, 255, 255), arrow_points)

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

def handle_promotion_click(pos):
    """Handle click during promotion selection on the dropdown"""
    if not promotion_pending:
        return None
    
    x, y = pos
    
    # Get the promotion square position
    end_row, end_col = promotion_to
    square_size = 60
    board_offset_y = 40
    
    # Calculate display position based on board orientation
    if white_on_bottom:
        display_row, display_col = end_row, end_col
    else:
        display_row, display_col = 7 - end_row, 7 - end_col
    
    # Calculate dropdown position
    square_x = display_col * square_size
    square_y = board_offset_y + display_row * square_size
    
    dropdown_width = square_size
    dropdown_height = square_size * 4
    
    # Position dropdown relative to display position so it stays on-screen
    if display_row >= 4:
        dropdown_y = square_y - dropdown_height + square_size  # open up
    else:
        dropdown_y = square_y  # open down
    
    dropdown_x = square_x
    
    # Check if click is within dropdown
    if not (dropdown_x <= x <= dropdown_x + dropdown_width and 
            dropdown_y <= y <= dropdown_y + dropdown_height):
        return None  # Click outside dropdown, ignore
    
    # Calculate which piece option was clicked
    relative_y = y - dropdown_y
    option_index = relative_y // square_size
    
    # Make sure the click is within valid bounds
    if 0 <= option_index < 4:
        promotion_pieces = ['Q', 'R', 'B', 'N']
        return promotion_pieces[option_index]
    
    return None

def complete_promotion(selected_piece_type):
    """Complete the pawn promotion"""
    global promotion_pending, promotion_from, promotion_to, promotion_piece_color
    global promotion_is_capture, promotion_captured_piece
    global current_turn, last_pawn_move
    
    # Get the promoted piece
    promoted_piece = get_promoted_piece(selected_piece_type, promotion_piece_color)
    
    # Place the promoted piece on the board
    end_row, end_col = promotion_to
    board_state[end_row][end_col] = promoted_piece
    
    # Track material capture if there was one
    if promotion_is_capture and promotion_captured_piece:
        material_tracker.capture_piece(promotion_captured_piece, current_turn)
    
    # Track material gain from promotion
    material_tracker.promote_pawn(promoted_piece, current_turn)
    
    # Continue with the rest of move processing
    piece = "P" if promotion_piece_color else "p"  # Original pawn
    selected_square = promotion_from
    
    # Check if the move puts opponent in check or checkmate
    opponent_color = "black" if current_turn == "white" else "white"
    is_check = is_in_check(opponent_color, board_state, white_on_bottom)
    is_checkmate_result = False
    is_stalemate_result = False
    
    if is_check:
        is_checkmate_result = is_checkmate(opponent_color, board_state, white_on_bottom)
        if is_checkmate_result:
            print(f"CHECKMATE DETECTED! {opponent_color} is in checkmate")
    else:
        is_stalemate_result = is_stalemate(opponent_color, board_state, white_on_bottom)
        if is_stalemate_result:
            print(f"STALEMATE DETECTED! {opponent_color} has no legal moves")
    
    # Generate move notation (with promotion)
    move_notation = move_history.convert_to_algebraic_notation(
        selected_square, promotion_to, piece, board_state,
        is_capture=promotion_is_capture, is_check=is_check, is_checkmate=is_checkmate_result,
        promotion_piece=selected_piece_type
    )
    
    print(f"Promotion move notation: {move_notation}")
    
    is_white_move = current_turn == "white"
    move_history.add_move(move_notation, is_white_move)
    
    # Reset promotion state
    promotion_pending = False
    promotion_from = None
    promotion_to = None
    promotion_piece_color = None
    promotion_is_capture = False
    promotion_captured_piece = None
    
    switch_turn()

def handle_click(pos):
    global selected_square, valid_moves, last_pawn_move, current_turn
    global promotion_pending, promotion_from, promotion_to, promotion_piece_color
    global promotion_is_capture, promotion_captured_piece
    
    # Check settings clicks first
    if handle_settings_click(pos):
        return  # Settings click was handled
    
    # If promotion is pending, handle promotion selection
    if promotion_pending:
        selected_piece = handle_promotion_click(pos)
        if selected_piece:
            complete_promotion(selected_piece)
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
                    promotion_pending = True
                    promotion_from = selected_square
                    promotion_to = (end_row, end_col)
                    promotion_piece_color = piece.isupper()
                    promotion_is_capture = is_capture
                    promotion_captured_piece = captured_piece
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
    draw_material_displays()
    
    # Draw game elements (board stays in original position)
    draw_board()
    
    # Only highlight moves if not in promotion mode
    if not promotion_pending:
        highlight_moves(valid_moves)
    else:
        # Highlight the promotion square in a special color
        end_row, end_col = promotion_to
        square_size = 60
        board_offset_y = 40
        
        # Calculate display position based on board orientation
        if white_on_bottom:
            display_row, display_col = end_row, end_col
        else:
            display_row, display_col = 7 - end_row, 7 - end_col
        
        promotion_rect = (display_col * square_size, board_offset_y + display_row * square_size, square_size, square_size)
        pygame.draw.rect(screen, (255, 215, 0), promotion_rect)  # Gold highlight for promotion
        pygame.draw.rect(screen, (255, 165, 0), promotion_rect, 4)  # Orange border
    
    draw_pieces(board_state)
    draw_labels()
    
    # Draw move history panel (always visible on the right)
    move_history.draw(screen)
    
    # Draw settings gear and dropdown
    draw_settings_gear()
    draw_settings_dropdown()
    
    # Draw promotion dialog if needed
    if promotion_pending:
        draw_promotion_dialog()
    
    pygame.display.flip()
pygame.quit()
