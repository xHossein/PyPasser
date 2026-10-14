"""Engine-agnostic reCaptcha V2 solve flow."""

from __future__ import annotations

import tempfile
import time
from typing import TYPE_CHECKING, Callable, Optional

from pypasser.captcha.recaptcha.v2 import audio
from pypasser.exceptions import IpBlock, RecaptchaResponseNotFound
from pypasser.structs import SolverResult

if TYPE_CHECKING:  # pragma: no cover
    from pypasser.browsers import BrowserAdapter

CHECKBOX_FRAME = "iframe[name^='a-']"
AUDIO_FRAME = "iframe[title^='recaptcha challenge']"

CHECKBOX_SELECTOR = "#recaptcha-anchor"
AUDIO_BUTTON_SELECTOR = "#recaptcha-audio-button"
DOWNLOAD_SELECTOR = ".rc-audiochallenge-tdownload-link"
PLAY_BUTTON_SELECTOR = ".rc-audiochallenge-play-button > button"
RESPONSE_SELECTOR = "#audio-response"

CHECKED_SELECTORS = (
    "#recaptcha-anchor[aria-checked='true']",
    "#recaptcha-anchor.recaptcha-checkbox-checked",
    ".recaptcha-checkbox-checked .recaptcha-checkbox-checkmark",
)

IP_BLOCK_MARKERS = (
    "rc-doscaptcha-header",
    "sending automated queries",
    "network may be sending automated queries",
)

MULTI_SOLVE_MARKERS = (
    "multiple correct solutions required",
    "please solve more",
)

GOOGLE_FRAME_URL = "google.com/recaptcha"
POLL_INTERVAL = 0.1
TOKEN_SELECTORS = ("#g-recaptcha-response", ".g-recaptcha-response")


def _default_audio_step(link: str, dest_dir: str) -> str:
    mp3 = audio.download_audio(link, dest_dir)
    wav = audio.convert_to_wav(mp3)
    return audio.speech_to_text(wav)


class V2Solver:
    """Synchronous reCaptcha V2 solver (audio challenge)."""

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

    def solve(self, adapter: "BrowserAdapter") -> SolverResult:
        try:
            self._raise_if_ip_blocked(adapter)
            self._click_checkbox(adapter)
            if self._is_checked(
                adapter, wait=min(self.timeout, 2.0), until_challenge=True
            ):
                return self._result(adapter)

            self._click_audio_button(adapter)

            remaining = self.attempts
            previous_link: Optional[str] = None
            while remaining:
                grace = 0.5 if previous_link is None else 1.0
                if self._is_checked(adapter, wait=min(self.timeout, grace)):
                    return self._result(adapter)
                remaining -= 1
                with tempfile.TemporaryDirectory(prefix="pypasser_") as dest_dir:
                    link = self._get_audio_link(adapter, previous_link)
                    previous_link = link
                    try:
                        text = self.audio_step(link, dest_dir)
                    except IpBlock:
                        raise
                    except Exception as exc:
                        if self._is_ip_blocked(adapter):
                            raise IpBlock() from exc
                        if remaining:
                            time.sleep(0.5)
                            continue
                        raise
                self._submit_answer(adapter, text)
                if self._is_checked(adapter, fail_fast=True):
                    return self._result(adapter)
                if remaining:
                    time.sleep(0.3)

            if self._is_checked(adapter, wait=min(self.timeout, 5.0)):
                return self._result(adapter)

            return SolverResult(is_solved=False, response_token=None)
        except Exception as exc:
            if self._is_ip_blocked(adapter):
                raise IpBlock() from exc
            raise

    def _click_checkbox(self, adapter: "BrowserAdapter") -> bool:
        if not self._checkbox_available(adapter):
            return False
        adapter.click(CHECKBOX_SELECTOR, frame=CHECKBOX_FRAME, timeout=self.timeout)
        return True

    def _checkbox_available(self, adapter: "BrowserAdapter") -> bool:
        deadline = time.monotonic() + self.timeout
        while True:
            if adapter.exists(CHECKBOX_SELECTOR, frame=CHECKBOX_FRAME):
                return True
            if adapter.visible(AUDIO_BUTTON_SELECTOR, frame=AUDIO_FRAME):
                return False
            if time.monotonic() >= deadline:
                return False
            time.sleep(POLL_INTERVAL)

    def _click_audio_button(self, adapter: "BrowserAdapter") -> None:
        self._poll_until(
            adapter, lambda: adapter.visible(AUDIO_BUTTON_SELECTOR, frame=AUDIO_FRAME), 0
        )
        self._poll_until(
            adapter,
            lambda: self._is_enabled(adapter, AUDIO_BUTTON_SELECTOR, AUDIO_FRAME),
            wait=min(self.timeout, 12.0),
        )
        try:
            self._guarded_click(adapter, AUDIO_BUTTON_SELECTOR, AUDIO_FRAME)
        except Exception:
            if not adapter.visible(AUDIO_BUTTON_SELECTOR, frame=AUDIO_FRAME):
                raise
            adapter.click(
                AUDIO_BUTTON_SELECTOR,
                frame=AUDIO_FRAME,
                timeout=self.timeout,
                force=True,
            )

    def _poll_until(
        self, adapter: "BrowserAdapter", check: Callable[[], bool], wait: float
    ) -> bool:
        deadline = time.monotonic() + (self.timeout if wait <= 0 else wait)
        while time.monotonic() < deadline:
            if check():
                return True
            self._raise_if_ip_blocked(adapter)
            time.sleep(POLL_INTERVAL)
        return False

    def _guarded_click(self, adapter: "BrowserAdapter", css: str, frame: str) -> None:
        deadline = time.monotonic() + self.timeout
        slice_timeout = min(1.0, self.timeout)
        while True:
            try:
                return adapter.click(css, frame=frame, timeout=slice_timeout)
            except Exception as exc:
                if self._is_ip_blocked(adapter):
                    raise IpBlock() from exc
                if time.monotonic() >= deadline:
                    raise

    def _guarded_attr(
        self, adapter: "BrowserAdapter", css: str, attribute: str, frame: str
    ) -> Optional[str]:
        deadline = time.monotonic() + self.timeout
        slice_timeout = min(1.0, self.timeout)
        while True:
            value = adapter.attr(css, attribute, frame=frame, timeout=slice_timeout)
            if value:
                return value
            if self._is_ip_blocked(adapter):
                raise IpBlock()
            if time.monotonic() >= deadline:
                return None

    def _get_audio_link(
        self, adapter: "BrowserAdapter", previous_link: Optional[str] = None
    ) -> str:
        if self.play:
            self._poll_until(
                adapter,
                lambda: adapter.visible(PLAY_BUTTON_SELECTOR, frame=AUDIO_FRAME),
                wait=min(self.timeout, 3.0),
            )
            self._guarded_click(adapter, PLAY_BUTTON_SELECTOR, AUDIO_FRAME)

        link = self._guarded_attr(adapter, DOWNLOAD_SELECTOR, "href", AUDIO_FRAME)
        if not link:
            self._raise_if_ip_blocked(adapter)
            raise RecaptchaResponseNotFound("Audio download link not found.")

        if previous_link and link == previous_link:
            link = self._wait_for_new_link(adapter, previous_link) or link
        return link

    def _wait_for_new_link(self, adapter: "BrowserAdapter", previous_link: str) -> Optional[str]:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            link = adapter.attr(DOWNLOAD_SELECTOR, "href", frame=AUDIO_FRAME, timeout=1)
            if link and link != previous_link:
                return link
            time.sleep(POLL_INTERVAL)
        return None

    def _is_multi_solve_required(self, adapter: "BrowserAdapter") -> bool:
        try:
            source = adapter.frames_html(GOOGLE_FRAME_URL).lower()
        except Exception:
            return False
        return any(marker in source for marker in MULTI_SOLVE_MARKERS)

    def _submit_answer(self, adapter: "BrowserAdapter", text: str) -> bool:
        try:
            if self._poll_until(
                adapter,
                lambda: self._is_enabled(adapter, RESPONSE_SELECTOR, AUDIO_FRAME),
                wait=min(self.timeout, 6.0),
            ):
                adapter.type(
                    RESPONSE_SELECTOR, text, frame=AUDIO_FRAME, timeout=self.timeout, submit=True
                )
                return True
        except Exception:
            pass
        return False

    def _is_enabled(self, adapter: "BrowserAdapter", css: str, frame: str) -> bool:
        try:
            if adapter.attr(css, "disabled", frame=frame, timeout=0) is not None:
                return False
            classes = adapter.attr(css, "class", frame=frame, timeout=1) or ""
            return "rc-button-disabled" not in classes
        except Exception:
            return True

    def _is_checked(
        self,
        adapter: "BrowserAdapter",
        wait: Optional[float] = None,
        fail_fast: bool = False,
        until_challenge: bool = False,
    ) -> bool:
        deadline = time.monotonic() + (self.timeout if wait is None else wait)
        next_scan = time.monotonic() + 1.0
        while True:
            if self._looks_solved(adapter):
                return True
            now = time.monotonic()
            if fail_fast and now >= next_scan:
                if self._is_enabled(
                    adapter, RESPONSE_SELECTOR, AUDIO_FRAME
                ) and self._is_multi_solve_required(adapter):
                    return False
                next_scan = now + 0.5
            if until_challenge and adapter.visible(
                AUDIO_BUTTON_SELECTOR, frame=AUDIO_FRAME
            ):
                return False
            if now >= deadline:
                return False
            time.sleep(POLL_INTERVAL)

    def _looks_solved(self, adapter: "BrowserAdapter") -> bool:
        if any(adapter.exists(sel, frame=CHECKBOX_FRAME) for sel in CHECKED_SELECTORS):
            return True
        if (
            adapter.attr(
                CHECKBOX_SELECTOR, "aria-checked", frame=CHECKBOX_FRAME, timeout=1
            )
            or ""
        ).lower() == "true":
            return True
        classes = (
            adapter.attr(CHECKBOX_SELECTOR, "class", frame=CHECKBOX_FRAME, timeout=1)
            or ""
        )
        if "recaptcha-checkbox-checked" in classes:
            return True
        return self._read_token(adapter, timeout=0) is not None

    def _read_token(self, adapter: "BrowserAdapter", timeout: float = 10) -> Optional[str]:
        for selector in TOKEN_SELECTORS:
            token = adapter.attr(selector, "value", timeout=timeout)
            if token:
                return token
        return None

    def _result(self, adapter: "BrowserAdapter") -> SolverResult:
        token = self._read_token(adapter, timeout=self.timeout)
        return SolverResult(is_solved=True, response_token=token)

    def _raise_if_ip_blocked(self, adapter: "BrowserAdapter") -> None:
        if self._is_ip_blocked(adapter):
            raise IpBlock()

    def _is_ip_blocked(self, adapter: "BrowserAdapter") -> bool:
        try:
            source = adapter.frames_html(GOOGLE_FRAME_URL).lower()
        except Exception:
            return False
        return any(marker in source for marker in IP_BLOCK_MARKERS)
