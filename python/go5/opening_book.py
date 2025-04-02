# -*- coding: utf-8 -*-

# Renju/Gomoku Opening Book Data
# Key: Tuple representing the sequence of previous moves ((r1, c1), (r2, c2), ...)
# Value: Tuple representing the next move (r_next, c_next) to play by the current player.
# Coordinates: 0-indexed (row, col), where (0, 0) is top-left, (7, 7) is Tengen.

# NOTE: This is still a *sample* opening book and needs significant expansion
#       to be competitive. Many variations and deeper lines are missing.
#       Consider standard Renju openings like Flower Moon (花月), Pauchard Moon (浦月),
#       Slope Moon (斜月), Star openings (寒星), etc., and their common variations.

OPENING_BOOK = {
    # === Black's 1st move: Tengen (7, 7) ===
    # --- White's 2nd move responses ---
    ((7, 7),): (7, 8),              # Flower Moon (花月) - Direct adjacent response (most common for White)
    # ((7, 7),): (6, 7),            # Pauchard Moon (浦月) - Diagonal response (alternative)
    # ((7, 7),): (6, 8),            # Slope Moon (斜月) - Another diagonal (alternative)
    # ((7, 7),): (5, 7),            # Cold Star (寒星) - Indirect (alternative)

    # --- After Black (7,7), White (7,8) --- [Flower Moon Start]
    ((7, 7), (7, 8)): (6, 8),         # Black 3rd move - Common continuation

    # --- After Black (7,7), White (6,7) --- [Pauchard Moon Start]
    ((7, 7), (6, 7)): (6, 8),         # Black 3rd move - Common continuation

    # --- After Black (7,7), White (6,8) --- [Slope Moon Start]
    ((7, 7), (6, 8)): (7, 8),         # Black 3rd move - Common continuation

    # --- Deeper Lines (Examples) ---
    # Flower Moon continuation: B(7,7), W(7,8), B(6,8) -> White's 4th move
    ((7, 7), (7, 8), (6, 8)): (6, 7),

    # Pauchard Moon continuation: B(7,7), W(6,7), B(6,8) -> White's 4th move
    ((7, 7), (6, 7), (6, 8)): (7, 8),

    # Slope Moon continuation: B(7,7), W(6,8), B(7,8) -> White's 4th move
    ((7, 7), (6, 8), (7, 8)): (8, 7),

    # Example 5th move for Black in Flower Moon line:
    # B(7,7), W(7,8), B(6,8), W(6,7) -> Black's 5th move
    ((7, 7), (7, 8), (6, 8), (6, 7)): (5, 7),

    # Example 5th move for Black in Pauchard Moon line:
    # B(7,7), W(6,7), B(6,8), W(7,8) -> Black's 5th move
    ((7, 7), (6, 7), (6, 8), (7, 8)): (8, 8),

    # Example 5th move for Black in Slope Moon line:
    # B(7,7), W(6,8), B(7,8), W(8,7) -> Black's 5th move
    ((7, 7), (6, 8), (7, 8), (8, 7)): (8, 6),

    # --- Add many more lines and variations here ---
    # Consider using online resources or databases for Renju/Gomoku openings.
    # Remember to handle symmetrical positions if needed, or rely on the game
    # engine potentially normalizing positions (though this simple AI doesn't).

}

# You can add functions here later if needed, e.g., to load from a file
# def load_book_from_file(filepath):
#     # ... implementation ...
#     pass