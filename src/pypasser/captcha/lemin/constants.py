"""Constants for the Lemin cropped captcha (v1)."""

API_BASE = "https://api.leminnow.com/captcha/v1/cropped"

# From /js file
SECRET = "e8269cb1-56c9-4f39-99ce-94f986c9e933"
VERSION = 3
ENC = "SHA256"

BASE_PIECE = 120
PIECE_MARGIN = 5
GRID = 10
HOME = (5, 405)

# Answer tokens kept in the history window by the widget.
HISTORY = 300

B32_ALPHABET = "0123456789abcdefghijklmnopqrstuv"

WHITE_THRESHOLD = 220
SCENE_WIDTH = 400

# Minimum number of points in an answer path. Fewer are rejected outright;
# the first point's position is not checked.
MIN_POINTS = 12

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)
