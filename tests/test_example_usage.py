"""
Smoke-tests for the public fixtures exposed by the plug-in.

These do **not** hard-code the number of parametrisations; we only rely on
whatever the plug-in decides to generate.
"""
import os
import time
import locale
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest
from pytest_tzshift import TzShift

# helper
def _has_tzdb_entry(zone: str) -> bool:
    try:
        ZoneInfo(zone)
        return True
    except ZoneInfoNotFoundError:
        return False


# tests
def test_time_module_reflects_change(tzshift: TzShift) -> None:
    """
    `TZ` is a process-global variable; after the fixture runs we expect the
    C library to reflect the new zone.
    """
    tz_name = tzshift.timezone
    print(f"[tzshift] running in TZ={tz_name!r}, tzname={time.tzname}")

    if os.name == "nt":
        pytest.skip("time.tzset() is a no-op for IANA zones on Windows/MSVC")

    assert tz_name is not None

    if not _has_tzdb_entry(tz_name):
        pytest.skip(f"{tz_name!r} not present in local tzdb")

    z = ZoneInfo(tz_name)
    abbrevs = {
        datetime(2025, 1, 15, 12, tzinfo=z).tzname(),   # winter
        datetime(2025, 7, 15, 12, tzinfo=z).tzname(),   # summer
    } - {None}

    assert abbrevs & set(time.tzname)


def test_locale_module_reflects_change(tzshift: TzShift) -> None:
    """
    `locale.setlocale(LC_ALL)` should now report the requested locale (or an
    OS-specific alias ).
    """
    requested_locale = tzshift.locale
    current = locale.setlocale(locale.LC_ALL)
    print(f"[tzshift] running with locale={current!r}")

    # Use prefix match to survive platform alias diff
    assert current.lower().startswith(requested_locale.split('.')[0].lower())


def test_zoneinfo_respects_change(tzshift: TzShift) -> None:
    """
    Modern tzdb-aware libraries must still work under the shifted TZ.
    """
    tz_name = tzshift.timezone
    if not _has_tzdb_entry(tz_name):
        pytest.skip(f"IANA zone {tz_name!r} unavailable in this runtime")

    tz = ZoneInfo(tz_name)
    dt = datetime(2025, 1, 15, 12, tzinfo=tz)
    print(f"[tzshift] successfully built datetime in {tz_name}: {dt!r}")
    assert dt.tzinfo is not None
