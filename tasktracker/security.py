"""Validation and a thread-safe, process-wide sliding-window limiter."""
import math
import time
import unicodedata
from collections import deque
from threading import Lock
from typing import Callable


class RateLimitError(ValueError):
    pass


class RateLimiter:
    def __init__(self, calls: int, seconds: int, clock: Callable[[], float] = time.monotonic):
        if calls < 1 or seconds <= 0:
            raise ValueError("Rate limits must be positive.")
        self.calls, self.seconds, self.clock = calls, seconds, clock
        self.events: deque[float] = deque()
        self.lock = Lock()

    def check(self) -> None:
        with self.lock:
            now = self.clock()
            while self.events and self.events[0] <= now - self.seconds:
                self.events.popleft()
            if len(self.events) >= self.calls:
                retry = max(1, math.ceil(self.seconds - (now - self.events[0])))
                raise RateLimitError(f"Rate limit exceeded. Retry in {retry} seconds.")
            self.events.append(now)


def clean_text(value: str, name: str, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError(f"{name} must be text with at most {maximum} characters.")
    if any(unicodedata.category(char).startswith("C") for char in value):
        raise ValueError(f"{name} cannot contain control characters.")
    value = value.strip()
    if not value and not allow_empty:
        raise ValueError(f"{name} cannot be empty.")
    return value
