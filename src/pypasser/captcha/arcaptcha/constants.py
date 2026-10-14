"""Wire constants for the ARCaptcha API."""

API_BASE = "https://api.arcaptcha.ir/arcaptcha/api"

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)

INSTANT_TYPES = ("cookie", "accept")

BLOCK_TYPE = "block"

VOICE_TYPES = ("question", "voice", "voice_question")
VOICE_ANSWER_TYPE = "voice_question"

TOKEN_INPUT_SELECTOR = "input[name='arcaptcha-token']"
