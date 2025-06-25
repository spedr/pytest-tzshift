from __future__ import annotations

import os
import locale
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest

# ---------------------------------------------------------------------------
# Helpers – kept local to avoid import‑time side‑effects and to stay in sync
#           with whatever the host really supports.
# ---------------------------------------------------------------------------

# Snapshot the process settings once so we can later prove we did not tamper
# with them when the SYSTEM sentinel is in play.
_ORIG_TZ: str | None = os.environ.get("TZ")
_ORIG_LOCALE: str = locale.setlocale(locale.LC_ALL)


def _available_locales(candidates: list[str]) -> list[str]:
    """Return only locales that can be set on this host."""
    available: list[str] = []
    original = locale.setlocale(locale.LC_ALL)
    try:
        for loc in candidates:
            try:
                locale.setlocale(locale.LC_ALL, loc)
                available.append(loc)
            except locale.Error:
                # Not installed – skip silently, the plug‑in will warn anyway.
                pass
    finally:
        locale.setlocale(locale.LC_ALL, original)
    return available


def _available_timezones(candidates: list[str]) -> list[str]:
    """Return the subset present in the local tzdb."""
    available: list[str] = []
    for tz in candidates:
        try:
            ZoneInfo(tz)
            available.append(tz)
        except ZoneInfoNotFoundError:
            pass
    return available


# ---------------------------------------------------------------------------
# 1. Sentinel semantics & environment preservation
# ---------------------------------------------------------------------------


@pytest.mark.tzshift(timezones=["SYSTEM"], locales=["SYSTEM"])
def test_system_sentinel_preserves_environment(tzshift):
    assert tzshift.as_tuple() == ("SYSTEM", "SYSTEM")
    assert os.environ.get("TZ") == _ORIG_TZ
    assert locale.setlocale(locale.LC_ALL) == _ORIG_LOCALE


@pytest.mark.tzshift(timezones=[" system "], locales=["\tSystem  "])
def test_sentinel_whitespace_and_case_insensitive(tzshift):
    """Leading/trailing whitespace and case differences should still match the sentinel."""
    assert tzshift.as_tuple() == ("SYSTEM", "SYSTEM")


# ---------------------------------------------------------------------------
# 2. Marker precedence – class‑level disable vs. function‑level overrides
# ---------------------------------------------------------------------------


@pytest.mark.tzshift(disable=True)
class TestDisablePrecedence:
    @pytest.mark.tzshift(timezones=["UTC"], locales=["C"])
    def test_disable_wins(self, tzshift):
        assert tzshift.as_tuple() == ("SYSTEM", "SYSTEM")


# ---------------------------------------------------------------------------
# 3. CLI de‑duplication and sentinel mixing
# ---------------------------------------------------------------------------


def test_cli_duplicates_and_sentinels_deduplicated(pytester):
    """Repeated values and sentinels on the CLI must yield unique combinations only."""

    pytester.makepyfile("def test_ok(tzshift): pass")

    res = pytester.runpytest(
        "--tz-timezones=UTC,SYSTEM,UTC,SYSTEM",
        "--tz-locales=C,SYSTEM,C",
        "-q",
    )

    # Compute the *expected* Cartesian product after the plug‑in filters & dedups.
    valid_tzs = _available_timezones(["UTC"])
    if not valid_tzs:
        pytest.skip("'UTC' timezone not present in the local tz database")
    valid_tzs.append("SYSTEM")  # sentinel always allowed

    valid_locs = _available_locales(["C"])
    if not valid_locs:
        pytest.skip("Locale 'C' unexpectedly missing on this platform")
    valid_locs.append("SYSTEM")  # sentinel

    expected_runs = len(set(valid_tzs)) * len(set(valid_locs))

    res.assert_outcomes(passed=expected_runs)


# ---------------------------------------------------------------------------
# 4. Graceful degradation when the user specifies invalid names
# ---------------------------------------------------------------------------


def test_invalid_timezone_and_locale_emit_warnings(pytester):
    pytester.makepyfile("def test_ok(tzshift): pass")

    res = pytester.runpytest(
        "--tz-timezones=Invalid/Zone,UTC",
        "--tz-locales=Nonexistent,C",
        "-q",
    )

    output = res.stdout.str()
    assert "ignoring unknown time-zones" in output
    assert "Invalid/Zone" in output
    assert "ignoring unavailable locales" in output
    assert "Nonexistent" in output

    valid_tzs = _available_timezones(["UTC"])
    if not valid_tzs:
        pytest.skip(
            "'UTC' timezone not present in the local tz database - cannot assess outcome count"
        )

    valid_locs = _available_locales(["C"])
    if not valid_locs:
        pytest.skip("Locale 'C' unexpectedly missing - cannot assess outcome count")

    expected_runs = len(valid_tzs) * len(valid_locs)
    res.assert_outcomes(passed=expected_runs)
