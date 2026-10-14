from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from playwright.async_api import Locator as AsyncLocator
    from playwright.async_api import Page as AsyncPage
    from playwright.sync_api import Locator as SyncLocator
    from playwright.sync_api import Page as SyncPage


def _ms(timeout: float) -> int:
    return int(timeout * 1000)


def _is_click_geometry_error(exc: Exception) -> bool:
    """Whether a click failed for engine-popup geometry reasons."""
    if "timeout" in type(exc).__name__.lower():
        return True
    message = str(exc).lower()
    return (
        "outside of the viewport" in message or "intercepts pointer events" in message
    )


class PlaywrightAdapter:
    """Sync adapter for Playwright (and playwright-compatible) pages."""

    def __init__(self, page: "SyncPage") -> None:
        self.page = page

    def _locator(self, css: str, frame: str | None) -> "SyncLocator":
        if frame:
            return self.page.frame_locator(frame).locator(css)
        return self.page.locator(css)

    def click(
        self, css: str, frame: str | None = None, timeout: float = 10, force: bool = False
    ) -> None:
        locator = self._locator(css, frame)
        try:
            locator.click(timeout=_ms(timeout), force=force)
        except Exception as exc:
            if _is_click_geometry_error(exc):
                locator.dispatch_event("click", timeout=_ms(timeout))
                return
            raise

    def attr(
        self, css: str, attribute: str, frame: str | None = None, timeout: float = 10
    ) -> str | None:
        locator = self._locator(css, frame)
        try:
            if attribute == "value":
                return locator.input_value(timeout=_ms(timeout))
            return locator.get_attribute(attribute, timeout=_ms(timeout))
        except Exception:
            return None

    def type(
        self, css: str, text: str, frame: str | None = None, submit: bool = True,
        timeout: float = 10,
    ) -> None:
        locator = self._locator(css, frame)
        locator.fill(text, timeout=_ms(timeout))
        if submit:
            locator.press("Enter")

    def exists(self, css: str, frame: str | None = None) -> bool:
        return self._locator(css, frame).count() > 0

    def visible(self, css: str, frame: str | None = None) -> bool:
        try:
            return self._locator(css, frame).first.is_visible()
        except Exception:
            return False

    def page_source(self) -> str:
        return self.page.content()

    def cookies(self) -> dict[str, str]:
        raw = self.page.context.cookies([self.page.url])
        return {c["name"]: c["value"] for c in raw}

    def user_agent(self) -> str | None:
        return self.page.evaluate("() => navigator.userAgent")

    def frames_html(self, url_contains: str | None = None) -> str:
        parts: list[str] = []
        for frame in self.page.frames:
            if url_contains and url_contains not in (frame.url or ""):
                continue
            try:
                parts.append(frame.content())
            except Exception:
                continue
        return "\n".join(parts)


class AsyncPlaywrightAdapter:
    """Async adapter for Playwright (and playwright-compatible) pages."""

    def __init__(self, page: "AsyncPage") -> None:
        self.page = page

    def _locator(self, css: str, frame: str | None) -> "AsyncLocator":
        if frame:
            return self.page.frame_locator(frame).locator(css)
        return self.page.locator(css)

    async def click(
        self, css: str, frame: str | None = None, timeout: float = 10, force: bool = False
    ) -> None:
        locator = self._locator(css, frame)
        try:
            await locator.click(timeout=_ms(timeout), force=force)
        except Exception as exc:
            if _is_click_geometry_error(exc):
                await locator.dispatch_event("click", timeout=_ms(timeout))
                return
            raise

    async def attr(
        self, css: str, attribute: str, frame: str | None = None, timeout: float = 10
    ) -> str | None:
        locator = self._locator(css, frame)
        try:
            if attribute == "value":
                return await locator.input_value(timeout=_ms(timeout))
            return await locator.get_attribute(attribute, timeout=_ms(timeout))
        except Exception:
            return None

    async def type(
        self, css: str, text: str, frame: str | None = None, submit: bool = True,
        timeout: float = 10,
    ) -> None:
        locator = self._locator(css, frame)
        await locator.fill(text, timeout=_ms(timeout))
        if submit:
            await locator.press("Enter")

    async def exists(self, css: str, frame: str | None = None) -> bool:
        return await self._locator(css, frame).count() > 0

    async def visible(self, css: str, frame: str | None = None) -> bool:
        try:
            return await self._locator(css, frame).first.is_visible()
        except Exception:
            return False

    async def page_source(self) -> str:
        return await self.page.content()

    async def cookies(self) -> dict[str, str]:
        raw = await self.page.context.cookies([self.page.url])
        return {c["name"]: c["value"] for c in raw}

    async def user_agent(self) -> str | None:
        return await self.page.evaluate("() => navigator.userAgent")

    async def frames_html(self, url_contains: str | None = None) -> str:
        parts: list[str] = []
        for frame in self.page.frames:
            if url_contains and url_contains not in (frame.url or ""):
                continue
            try:
                parts.append(await frame.content())
            except Exception:
                continue
        return "\n".join(parts)
