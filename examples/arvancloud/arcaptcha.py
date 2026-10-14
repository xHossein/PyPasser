"""ARCaptcha — the widget is an HTTP client behind the scenes (obfuscated
POSTs to api.arcaptcha.ir), so it is solved over HTTP from the site key alone:
puzzle with CV, 9-image grid falls back to the API's voice variant, voice is
transcribed with Persian vosk.

    python examples/arvancloud/arcaptcha.py

Public demo keys — puzzle (arcaptcha.co), puzzle (demo.arcaptcha.co),
9-image→voice (arcaptcha.co):

    jqz10q84eu / d6ggpvy684 / vm6spkx59m

Requires: pip install "PyPasser[vision,speech]"   (puzzle / voice challenges)
"""

from pypasser.captcha import arcaptcha

SITE_KEY = "jqz10q84eu"
DOMAIN = "arcaptcha.co"

result = arcaptcha.solve(SITE_KEY, domain=DOMAIN)

print("solved:", result.is_solved)
print("token:", result.response_token)
