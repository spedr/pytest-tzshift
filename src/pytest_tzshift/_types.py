from __future__ import annotations

import sys
from dataclasses import dataclass as _dc
from typing import Iterator, Tuple

PY310_PLUS = sys.version_info >= (3, 10)

# small helper: returns a version-aware dataclass decorator
def _dataclass(**kwargs):          # kwargs contain frozen=True, slots=True
    if not PY310_PLUS:             # 3.9: remove the unsupported key
        kwargs.pop("slots", None)

    def wrap(cls):
        cls = _dc(**kwargs)(cls)   # apply the regular @dataclass
        if not PY310_PLUS:         # emulate slots
            cls.__slots__ = tuple(cls.__annotations__)
        return cls

    return wrap

@_dataclass(frozen=True, slots=True)
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

    def __iter__(self) -> Iterator[str]:
        return iter((self.timezone, self.locale))

    def __len__(self) -> int:
        return 2

    def __getitem__(self, idx: int) -> str:
        if idx == 0:
            return self.timezone
        if idx == 1:
            return self.locale
        raise IndexError(idx)

    def as_tuple(self) -> Tuple[str, str]:
        """Helper for explicit tuple."""
        return (self.timezone, self.locale)
