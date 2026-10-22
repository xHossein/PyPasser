from __future__ import annotations


class PyPasserError(Exception):
    """Base class for all PyPasser exceptions."""


class RequestFailed(PyPasserError):
    """Raised when a solver's network request fails."""


class InvalidAnchorURL(PyPasserError):
    """Raised when a reCaptcha anchor URL cannot be parsed or built."""


class RecaptchaTokenNotFound(PyPasserError):
    """Raised when the recaptcha-token cannot be found in the anchor response."""


class RecaptchaResponseNotFound(PyPasserError):
    """Raised when the recaptcha response cannot be found (wrong URL or no reCaptcha on target)."""


class AudioDecodeError(PyPasserError):
    """Raised when a downloaded challenge clip cannot be decoded to PCM."""


class InvalidProxyURL(PyPasserError):
    """Raised when a proxy URL is malformed or uses an unsupported scheme."""


class UnknownBackend(PyPasserError):
    """Raised when ``backend="auto"`` cannot identify the given page/driver object."""


class BackendNotAsync(PyPasserError):
    """Raised when an async solve is requested for a backend that only supports sync."""


class IpBlock(PyPasserError):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message
            or (
                "Too many tries for solving reCaptchaV2 using speech to text, "
                "take a break or change your ip."
            )
        )


class ArvanChallengeError(PyPasserError):
    """Raised when an ArvanCloud challenge page cannot be parsed or decoded."""


class ArvanBypassError(PyPasserError):
    """Raised when the ArvanCloud challenge was not cleared within the attempt budget."""


class CloudflareError(PyPasserError):
    """Base class for Cloudflare clearance errors."""


class CloudflareClearanceError(CloudflareError):
    """The Cloudflare challenge passed but no ``cf_clearance`` cookie came back.

    Without that cookie there is nothing for an HTTP client to replay — the
    browser used cannot expose its cookies (no adapter support), or Cloudflare
    soft-blocked the session and cleared without issuing clearance.
    """


class ARCaptchaError(PyPasserError):
    """Base class for ARCaptcha solving errors."""


class ARCaptchaBlocked(ARCaptchaError):
    """The ARCaptcha server flagged the session (``captcha_type == "block"``)."""


class ARCaptchaSolveFailed(ARCaptchaError):
    """The challenge could not be solved within the attempt budget."""


class LeminError(PyPasserError):
    """Base class for Lemin solving errors."""


class LeminSolveFailed(LeminError):
    """The cropped challenge could not be solved within the attempt budget."""


class GeeTestError(PyPasserError):
    """Base class for GeeTest solving errors."""


class GeeTestSolveFailed(GeeTestError):
    """The GeeTest challenge could not be solved within the attempt budget."""


class RequestRateLimited(RequestFailed):
    """Every GeeTest mirror answered 429 or 5xx instead of serving the request."""
