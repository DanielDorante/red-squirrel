"""
Chess Material Evaluation Module

This module handles material counting and advantage calculation in chess.
Tracks captured pieces and shows relative material advantage.
"""

class MaterialTracker:
    def __init__(self):
        # Piece values
        self.piece_values = {
            'P': 1, 'p': 1,  # Pawns
            'N': 3, 'n': 3,  # Knights
            'B': 3, 'b': 3,  # Bishops
            'R': 5, 'r': 5,  # Rooks
            'Q': 9, 'q': 9,  # Queens
            'K': 0, 'k': 0   # Kings (no material value)
        }
        
        # Track captured pieces
        self.white_captured = []  # Pieces captured by white (black pieces)
        self.black_captured = []  # Pieces captured by black (white pieces)
        
        # Current material advantage
        self.white_material_gained = 0
        self.black_material_gained = 0
    
    def capture_piece(self, captured_piece, capturing_player):
        """
        Record a piece capture and update material counts
        
        Args:
            captured_piece: The piece that was captured (e.g., 'q', 'R')
            capturing_player: 'white' or 'black'
        """
        if captured_piece == '.' or captured_piece in ['K', 'k']:
            return  # No capture or king (shouldn't happen)
        
        piece_value = self.piece_values.get(captured_piece, 0)
        
        if capturing_player == 'white':
            self.white_captured.append(captured_piece)
            self.white_material_gained += piece_value
        else:
            self.black_captured.append(captured_piece)
            self.black_material_gained += piece_value
        
        print(f"Debug: {capturing_player} captured {captured_piece} (value: {piece_value})")
        print(f"Debug: White material: {self.white_material_gained}, Black material: {self.black_material_gained}")
    
    def promote_pawn(self, promoted_to, promoting_player):
        """
        Record a pawn promotion and update material counts
        
        Args:
            promoted_to: The piece the pawn was promoted to (e.g., 'Q', 'q')
            promoting_player: 'white' or 'black'
        """
        # Promotion gives material advantage equal to: (new piece value - pawn value)
        pawn_value = 1
        promoted_piece_value = self.piece_values.get(promoted_to, 0)
        material_gain = promoted_piece_value - pawn_value
        
        if promoting_player == 'white':
            self.white_material_gained += material_gain
        else:
            self.black_material_gained += material_gain
        
        print(f"Debug: {promoting_player} promoted to {promoted_to} (material gain: +{material_gain})")
        print(f"Debug: White material: {self.white_material_gained}, Black material: {self.black_material_gained}")
    
    def get_material_advantage(self):
        """
        Calculate who has the material advantage and by how much
        
        Returns:
            tuple: (player_with_advantage, advantage_amount)
                   player_with_advantage: 'white', 'black', or 'equal'
                   advantage_amount: positive integer or 0
        """
        advantage = self.white_material_gained - self.black_material_gained
        
        if advantage > 0:
            return 'white', advantage
        elif advantage < 0:
            return 'black', abs(advantage)
        else:
            return 'equal', 0
    
    def get_display_text(self, player):
        """
        Get the display text for a player's material advantage
        
        Args:
            player: 'white' or 'black'
            
        Returns:
            string: Empty string if no advantage, "+X" if advantage
        """
        advantage_player, advantage_amount = self.get_material_advantage()
        
        if advantage_player == player and advantage_amount > 0:
            return f"+{advantage_amount}"
        else:
            return ""
    
    def get_captured_pieces_display(self, player):
        """
        Get a list of captured pieces for display
        
        Args:
            player: 'white' or 'black' (who did the capturing)
            
        Returns:
            list: List of captured piece characters
        """
        if player == 'white':
            return self.white_captured.copy()
        else:
            return self.black_captured.copy()
    
    def reset(self):
        """Reset all material tracking"""
        self.white_captured = []
        self.black_captured = []
        self.white_material_gained = 0
        self.black_material_gained = 0
    
    def get_material_summary(self):
        """Get a summary of current material state for debugging"""
        white_advantage_text = self.get_display_text('white')
        black_advantage_text = self.get_display_text('black')
        
        return {
            'white_captured': self.white_captured,
            'black_captured': self.black_captured,
            'white_material_gained': self.white_material_gained,
            'black_material_gained': self.black_material_gained,
            'white_display': f"White {white_advantage_text}".strip(),
            'black_display': f"Black {black_advantage_text}".strip()
        }


def get_piece_display_name(piece):
    """Convert piece character to display name"""
    piece_names = {
        'P': 'Pawn', 'p': 'Pawn',
        'N': 'Knight', 'n': 'Knight', 
        'B': 'Bishop', 'b': 'Bishop',
        'R': 'Rook', 'r': 'Rook',
        'Q': 'Queen', 'q': 'Queen',
        'K': 'King', 'k': 'King'
    }
    return piece_names.get(piece, piece)


def test_material_tracker():
    """Test the material tracking system"""
    tracker = MaterialTracker()
    
    # Test some captures
    print("=== Testing Material Tracker ===")
    
    # White captures black queen
    tracker.capture_piece('q', 'white')
    print(f"After white captures black queen: {tracker.get_material_summary()}")
    
    # Black captures white rook
    tracker.capture_piece('R', 'black')
    print(f"After black captures white rook: {tracker.get_material_summary()}")
    
    # Black captures white bishop  
    tracker.capture_piece('B', 'black')
    print(f"After black captures white bishop: {tracker.get_material_summary()}")


if __name__ == "__main__":
    test_material_tracker()