from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Tuple


@dataclass(frozen=True, slots=True)
class TzShift:
    """
    An immutable data object holding the active timezone and locale.

    This object is yielded by the `tzshift` fixture to give tests read-only
    access to the environment settings for the current parametrized run.

    It behaves like a 2-element tuple, supporting unpacking, indexing, and `len()`.

    Attributes:
        timezone: The IANA timezone name (e.g., "America/New_York") or the
                  "SYSTEM" sentinel string.
        locale: The locale identifier (e.g., "en_US.UTF-8") or the
                "SYSTEM" sentinel string.
    """

    timezone: str
    locale: str

    def __iter__(self) -> Iterator[str]:  # allows:  tz, loc = tzshift
        return iter((self.timezone, self.locale))

    def __len__(self) -> int:  # len(tzshift) → 2
        return 2

    def __getitem__(self, idx: int) -> str:  # tzshift[0] / tzshift[1]
        if idx == 0:
            return self.timezone
        elif idx == 1:
            return self.locale
        raise IndexError(idx)

    def as_tuple(self) -> Tuple[str, str]:  # helper for explicit tuple
        return (self.timezone, self.locale)
