"""Asynchronous reCaptcha V2 solve flow."""

from __future__ import annotations

import asyncio
import tempfile
import time
from typing import TYPE_CHECKING, Awaitable, Callable, Optional

from pypasser.captcha.recaptcha.v2.flow import (
    AUDIO_BUTTON_SELECTOR,
    AUDIO_FRAME,
    CHECKBOX_FRAME,
    CHECKBOX_SELECTOR,
    CHECKED_SELECTORS,
    DOWNLOAD_SELECTOR,
    GOOGLE_FRAME_URL,
    IP_BLOCK_MARKERS,
    MULTI_SOLVE_MARKERS,
    PLAY_BUTTON_SELECTOR,
    POLL_INTERVAL,
    RESPONSE_SELECTOR,
    TOKEN_SELECTORS,
    _default_audio_step,
)
from pypasser.exceptions import IpBlock, RecaptchaResponseNotFound
from pypasser.structs import SolverResult

if TYPE_CHECKING:  # pragma: no cover
    from pypasser.browsers import AsyncBrowserAdapter


class AsyncV2Solver:
    """Asynchronous reCaptcha V2 solver (audio challenge)."""

    def __init__(
        self,
        play: bool = True,
        attempts: int = 3,
        timeout: float = 10,
        audio_step: Optional[Callable[[str, str], str]] = None,
    ) -> None:
        self.play = play
        self.attempts = attempts
        self.timeout = timeout
        self.audio_step = audio_step or _default_audio_step

    async def solve(self, adapter: "AsyncBrowserAdapter") -> SolverResult:
        try:
            await self._raise_if_ip_blocked(adapter)
            await self._click_checkbox(adapter)
            if await self._is_checked(
                adapter, wait=min(self.timeout, 2.0), until_challenge=True
            ):
                return await self._result(adapter)

            await self._click_audio_button(adapter)

            remaining = self.attempts
            previous_link: Optional[str] = None
            while remaining:
                grace = 0.5 if previous_link is None else 1.0
                if await self._is_checked(adapter, wait=min(self.timeout, grace)):
                    return await self._result(adapter)
                remaining -= 1
                link = await self._get_audio_link(adapter, previous_link)
                previous_link = link
                with tempfile.TemporaryDirectory(prefix="pypasser_") as dest_dir:
                    try:
                        text = await asyncio.to_thread(self.audio_step, link, dest_dir)
                    except IpBlock:
                        raise
                    except Exception as exc:
                        if await self._is_ip_blocked(adapter):
                            raise IpBlock() from exc
                        if remaining:
                            await asyncio.sleep(0.5)
                            continue
                        raise
                await self._submit_answer(adapter, text)
                if await self._is_checked(adapter, fail_fast=True):
                    return await self._result(adapter)
                if remaining:
                    await asyncio.sleep(0.3)

            if await self._is_checked(adapter, wait=min(self.timeout, 5.0)):
                return await self._result(adapter)

            return SolverResult(is_solved=False, response_token=None)
        except Exception as exc:
            if await self._is_ip_blocked(adapter):
                raise IpBlock() from exc
            raise

    async def _click_checkbox(self, adapter: "AsyncBrowserAdapter") -> bool:
        if not await self._checkbox_available(adapter):
            return False
        await adapter.click(CHECKBOX_SELECTOR, frame=CHECKBOX_FRAME, timeout=self.timeout)
        return True

    async def _checkbox_available(self, adapter: "AsyncBrowserAdapter") -> bool:
        deadline = time.monotonic() + self.timeout
        while True:
            if await adapter.exists(CHECKBOX_SELECTOR, frame=CHECKBOX_FRAME):
                return True
            if await adapter.visible(AUDIO_BUTTON_SELECTOR, frame=AUDIO_FRAME):
                return False
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(POLL_INTERVAL)

    async def _click_audio_button(self, adapter: "AsyncBrowserAdapter") -> None:
        await self._poll_until(
            adapter,
            lambda: adapter.visible(AUDIO_BUTTON_SELECTOR, frame=AUDIO_FRAME),
            0,
        )
        await self._poll_until(
            adapter,
            lambda: self._is_enabled(adapter, AUDIO_BUTTON_SELECTOR, AUDIO_FRAME),
            wait=min(self.timeout, 12.0),
        )
        try:
            await self._guarded_click(adapter, AUDIO_BUTTON_SELECTOR, AUDIO_FRAME)
        except Exception:
            if not await adapter.visible(AUDIO_BUTTON_SELECTOR, frame=AUDIO_FRAME):
                raise
            await adapter.click(
                AUDIO_BUTTON_SELECTOR,
                frame=AUDIO_FRAME,
                timeout=self.timeout,
                force=True,
            )

    async def _poll_until(
        self,
        adapter: "AsyncBrowserAdapter",
        check: Callable[[], Awaitable[bool]],
        wait: float,
    ) -> bool:
        deadline = time.monotonic() + (self.timeout if wait <= 0 else wait)
        while time.monotonic() < deadline:
            if await check():
                return True
            await self._raise_if_ip_blocked(adapter)
            await asyncio.sleep(POLL_INTERVAL)
        return False

    async def _guarded_click(
        self, adapter: "AsyncBrowserAdapter", css: str, frame: str
    ) -> None:
        deadline = time.monotonic() + self.timeout
        slice_timeout = min(1.0, self.timeout)
        while True:
            try:
                return await adapter.click(css, frame=frame, timeout=slice_timeout)
            except Exception as exc:
                if await self._is_ip_blocked(adapter):
                    raise IpBlock() from exc
                if time.monotonic() >= deadline:
                    raise

    async def _guarded_attr(
        self, adapter: "AsyncBrowserAdapter", css: str, attribute: str, frame: str
    ) -> Optional[str]:
        deadline = time.monotonic() + self.timeout
        slice_timeout = min(1.0, self.timeout)
        while True:
            value = await adapter.attr(
                css, attribute, frame=frame, timeout=slice_timeout
            )
            if value:
                return value
            if await self._is_ip_blocked(adapter):
                raise IpBlock()
            if time.monotonic() >= deadline:
                return None

    async def _get_audio_link(
        self, adapter: "AsyncBrowserAdapter", previous_link: Optional[str] = None
    ) -> str:
        if self.play:
            await self._poll_until(
                adapter,
                lambda: adapter.visible(PLAY_BUTTON_SELECTOR, frame=AUDIO_FRAME),
                wait=min(self.timeout, 3.0),
            )
            await self._guarded_click(adapter, PLAY_BUTTON_SELECTOR, AUDIO_FRAME)

        link = await self._guarded_attr(
            adapter, DOWNLOAD_SELECTOR, "href", AUDIO_FRAME
        )
        if not link:
            await self._raise_if_ip_blocked(adapter)
            raise RecaptchaResponseNotFound("Audio download link not found.")

        if previous_link and link == previous_link:
            link = await self._wait_for_new_link(adapter, previous_link) or link
        return link

    async def _wait_for_new_link(
        self, adapter: "AsyncBrowserAdapter", previous_link: str
    ) -> Optional[str]:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            link = await adapter.attr(
                DOWNLOAD_SELECTOR, "href", frame=AUDIO_FRAME, timeout=1
            )
            if link and link != previous_link:
                return link
            await asyncio.sleep(POLL_INTERVAL)
        return None

    async def _is_multi_solve_required(self, adapter: "AsyncBrowserAdapter") -> bool:
        try:
            source = (await adapter.frames_html(GOOGLE_FRAME_URL)).lower()
        except Exception:
            return False
        return any(marker in source for marker in MULTI_SOLVE_MARKERS)

    async def _submit_answer(self, adapter: "AsyncBrowserAdapter", text: str) -> bool:
        try:
            if await self._poll_until(
                adapter,
                lambda: self._is_enabled(adapter, RESPONSE_SELECTOR, AUDIO_FRAME),
                wait=min(self.timeout, 6.0),
            ):
                await adapter.type(
                    RESPONSE_SELECTOR,
                    text,
                    frame=AUDIO_FRAME,
                    timeout=self.timeout,
                    submit=True,
                )
                return True
        except Exception:
            pass
        return False

    async def _is_enabled(
        self, adapter: "AsyncBrowserAdapter", css: str, frame: str
    ) -> bool:
        try:
            if (
                await adapter.attr(css, "disabled", frame=frame, timeout=0)
            ) is not None:
                return False
            classes = (
                await adapter.attr(css, "class", frame=frame, timeout=1)
            ) or ""
            return "rc-button-disabled" not in classes
        except Exception:
            return True

    async def _is_checked(
        self,
        adapter: "AsyncBrowserAdapter",
        wait: Optional[float] = None,
        fail_fast: bool = False,
        until_challenge: bool = False,
    ) -> bool:
        deadline = time.monotonic() + (self.timeout if wait is None else wait)
        next_scan = time.monotonic() + 1.0
        while True:
            if await self._looks_solved(adapter):
                return True
            now = time.monotonic()
            if fail_fast and now >= next_scan:
                if await self._is_enabled(
                    adapter, RESPONSE_SELECTOR, AUDIO_FRAME
                ) and await self._is_multi_solve_required(adapter):
                    return False
                next_scan = now + 0.5
            if until_challenge and await adapter.visible(
                AUDIO_BUTTON_SELECTOR, frame=AUDIO_FRAME
            ):
                return False
            if now >= deadline:
                return False
            await asyncio.sleep(POLL_INTERVAL)

    async def _looks_solved(self, adapter: "AsyncBrowserAdapter") -> bool:
        for selector in CHECKED_SELECTORS:
            if await adapter.exists(selector, frame=CHECKBOX_FRAME):
                return True
        if (
            await adapter.attr(
                CHECKBOX_SELECTOR, "aria-checked", frame=CHECKBOX_FRAME, timeout=1
            )
            or ""
        ).lower() == "true":
            return True
        classes = (
            await adapter.attr(
                CHECKBOX_SELECTOR, "class", frame=CHECKBOX_FRAME, timeout=1
            )
            or ""
        )
        if "recaptcha-checkbox-checked" in classes:
            return True
        return await self._read_token(adapter, timeout=0) is not None

    async def _read_token(
        self, adapter: "AsyncBrowserAdapter", timeout: float = 10
    ) -> Optional[str]:
        for selector in TOKEN_SELECTORS:
            token = await adapter.attr(selector, "value", timeout=timeout)
            if token:
                return token
        return None

    async def _result(self, adapter: "AsyncBrowserAdapter") -> SolverResult:
        token = await self._read_token(adapter, timeout=self.timeout)
        return SolverResult(is_solved=True, response_token=token)

    async def _raise_if_ip_blocked(self, adapter: "AsyncBrowserAdapter") -> None:
        if await self._is_ip_blocked(adapter):
            raise IpBlock()

    async def _is_ip_blocked(self, adapter: "AsyncBrowserAdapter") -> bool:
        try:
            source = (await adapter.frames_html(GOOGLE_FRAME_URL)).lower()
        except Exception:
            return False
        return any(marker in source for marker in IP_BLOCK_MARKERS)
