"""Browser automation layer.

Adapters hide the differences between browser automation libraries behind a
single protocol. ``detect()`` picks the right adapter automatically from the
page/driver object the user provides; an explicit backend name can also be
given to the solvers.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BrowserAdapter(Protocol):
    """Sync browser operations used by the solvers."""

    def click(
        self, css: str, frame: str | None = None, timeout: float = 10, force: bool = False
    ) -> None:
        """Click an element. ``frame`` is a CSS selector of the iframe to focus into.

        ``force`` skips actionability (useful when Google keeps repainting the
        challenge popup and a normal click never sees it "stable").
        """
        ...

    def attr(
        self, css: str, attribute: str, frame: str | None = None, timeout: float = 10
    ) -> str | None:
        """Get an element attribute, or None if the element/attribute is missing."""
        ...

    def type(
        self, css: str, text: str, frame: str | None = None, submit: bool = True,
        timeout: float = 10,
    ) -> None:
        """Type text into an element, optionally pressing Enter."""
        ...

    def exists(self, css: str, frame: str | None = None) -> bool:
        """Whether an element currently exists in the page (no waiting)."""
        ...

    def visible(self, css: str, frame: str | None = None) -> bool:
        """Whether an element is rendered on screen (no waiting)."""
        ...

    def page_source(self) -> str:
        """Full page HTML."""
        ...

    def frames_html(self, url_contains: str | None = None) -> str:
        """HTML of the main document plus every frame (used for block-page detection).

        ``url_contains`` keeps only frames whose URL contains the substring —
        used to match text against Google's own frames only.
        """
        ...

    def cookies(self) -> dict[str, str]:
        """Cookies of the current page's context, as ``name -> value``.

        Used to hand the ``cf_clearance`` cookie to the caller after a
        Cloudflare challenge passes. An empty dict when there are none.
        """
        ...

    def user_agent(self) -> str | None:
        """The browser's ``navigator.userAgent``, or None when unavailable."""
        ...


@runtime_checkable
class AsyncBrowserAdapter(Protocol):
    """Async browser operations used by the async solvers."""

    async def click(
        self, css: str, frame: str | None = None, timeout: float = 10, force: bool = False
    ) -> None: ...

    async def attr(
        self, css: str, attribute: str, frame: str | None = None, timeout: float = 10
    ) -> str | None: ...

    async def type(
        self, css: str, text: str, frame: str | None = None, submit: bool = True,
        timeout: float = 10,
    ) -> None: ...

    async def exists(self, css: str, frame: str | None = None) -> bool: ...

    async def visible(self, css: str, frame: str | None = None) -> bool: ...

    async def page_source(self) -> str: ...

    async def frames_html(self, url_contains: str | None = None) -> str: ...

    async def cookies(self) -> dict[str, str]: ...

    async def user_agent(self) -> str | None: ...


def _class_module(obj: Any) -> str:
    cls = type(obj)
    module = getattr(cls, "__module__", "") or ""
    return f"{module}.{cls.__name__}".lower()


def _is_playwright_page(marker: str) -> bool:
    """Playwright pages and API-compatible stealth forks (Patchright, Camoufox)."""
    return any(name in marker for name in ("playwright", "patchright", "camoufox"))


def detect(obj: Any) -> BrowserAdapter:
    """Detect the browser backend of ``obj`` and return a sync adapter."""
    marker = _class_module(obj)

    if ".async_api" in marker and _is_playwright_page(marker):
        from pypasser.exceptions import BackendNotAsync

        raise BackendNotAsync(
            "Object is an async Playwright page. Use the async solver (asolve)."
        )

    if _is_playwright_page(marker):
        from pypasser.browsers.playwright import PlaywrightAdapter

        return PlaywrightAdapter(obj)

    from pypasser.exceptions import UnknownBackend

    raise UnknownBackend(
        f"Cannot detect browser backend of {type(obj).__name__}. "
        "Pass a Playwright Page."
    )


def adetect(obj: Any) -> AsyncBrowserAdapter:
    """Detect the browser backend of ``obj`` and return an async adapter."""
    marker = _class_module(obj)

    if (".async_api" in marker or "asyncio" in marker) and _is_playwright_page(marker):
        from pypasser.browsers.playwright import AsyncPlaywrightAdapter

        return AsyncPlaywrightAdapter(obj)

    if _is_playwright_page(marker):
        from pypasser.exceptions import BackendNotAsync

        raise BackendNotAsync(
            "Object is a sync Playwright page. Pass an async_playwright() page to asolve."
        )

    from pypasser.exceptions import UnknownBackend

    raise UnknownBackend(
        f"Cannot detect browser backend of {type(obj).__name__}. "
        "Pass an async Playwright Page."
    )


def get_adapter(backend: str, obj: Any) -> BrowserAdapter:
    """Return the sync adapter for an explicit backend name."""
    if backend not in ("auto", "playwright", "patchright", "camoufox"):
        from pypasser.exceptions import UnknownBackend

        raise UnknownBackend(
            f"Unknown backend {backend!r}. Use auto, playwright or patchright."
        )

    if backend == "auto":
        return detect(obj)

    from pypasser.browsers.playwright import PlaywrightAdapter

    return PlaywrightAdapter(obj)


def aget_adapter(backend: str, obj: Any) -> AsyncBrowserAdapter:
    """Return the async adapter for an explicit backend name."""
    if backend not in ("auto", "playwright", "patchright", "camoufox"):
        from pypasser.exceptions import UnknownBackend

        raise UnknownBackend(
            f"Unknown backend {backend!r} for async solving. "
            "Use auto, playwright or patchright."
        )

    if backend == "auto":
        return adetect(obj)

    from pypasser.browsers.playwright import AsyncPlaywrightAdapter

    return AsyncPlaywrightAdapter(obj)
