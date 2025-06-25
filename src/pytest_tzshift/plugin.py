from __future__ import annotations

import os
import time
import locale
import warnings
from itertools import product
from typing import List, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import functools
import pytest
from pytest_tzshift import TzShift

SYSTEM_TZ = "SYSTEM"
SYSTEM_LOCALE = "SYSTEM"


def _is_system_sentinel(val: str | None, sentinel: str) -> bool:
    """
    True if *val* represents the "leave-as-is" sentinel, regardless of case
    or leading/trailing spaces, or if it is the empty string.
    """
    if val is None:
        return False
    stripped = val.strip()
    return stripped == "" or stripped.upper() == sentinel


DEFAULT_TIMEZONES: List[str] = [
    "UTC",
    "America/New_York",
    "Europe/London",
    "Asia/Kolkata",
    "Australia/Sydney",
    "Asia/Tokyo",
]

# "C" is guaranteed; the others are common on Linux/macOS.
# On Windows or minimal containers they may be absent – the fixture will skip.
DEFAULT_LOCALES: List[str] = [
    "C",
    "en_US.UTF-8",
    "de_DE.UTF-8",
    "fr_FR.UTF-8",
    "ja_JP.UTF-8",
]


def pytest_configure(config: pytest.Config) -> None:
    """
    A pytest hook that registers the 'tzshift' marker.

    This allows tests to be marked with `@pytest.mark.tzshift(...)` to
    customize parametrization for a specific test, class, or module.

    The marker signature is:
        tzshift(timezones=None, locales=None, disable=False)

    Args:
        timezones: A list of timezone names to use for this scope.
        locales: A list of locale identifiers to use for this scope.
        disable: If True, disables tzshift parametrization for this scope.
    """

    config.addinivalue_line(
        "markers",
        "tzshift(timezones=None, locales=None, disable=False): "
        "override the default timezone / locale sweep for this test or "
        "scope.  Pass disable=True to opt-out completely.",
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    A pytest hook that adds command-line and ini-file options.

    This function defines the configuration interface for the plugin,
    allowing users to specify default timezones, locales, and other
    settings globally for the test suite.

    Options Added:
        --tz-timezones: Comma-separated list of timezones.
        --tz-locales: Comma-separated list of locales.
        --tzshift-max: Integer cap on the number of generated tests.
        --no-tzshift: A flag to disable the plugin entirely.
    """
    group = parser.getgroup("tzshift", description="Timezone / locale shifting")

    group.addoption(
        "--tz-timezones",
        action="store",
        dest="tz_timezones",
        default=None,
        help="Comma-separated list of time-zones to test with "
        "(overrides [pytest] tz_timezones).",
    )

    group.addoption(
        "--tz-locales",
        action="store",
        dest="tz_locales",
        default=None,
        help="Comma-separated list of locale identifiers to test with "
        "(overrides [pytest] tz_locales).",
    )

    group.addoption(
        "--tzshift-max",
        action="store",
        dest="tzshift_max",
        default=None,
        type=int,
        help="Maximum number of (timezone, locale) combinations to generate. ",
    )

    group.addoption(
        "--no-tzshift",
        action="store_true",
        default=False,
        help="Disable all timezone/locale parametrisation.",
    )

    parser.addini(
        "tzshift_max",
        type="int",
        help="Cap the total number of (tz, locale) combinations. ",
        default=0,
    )

    parser.addini(
        "tz_timezones",
        type="linelist",
        help="List of time-zones (one per line).",
        default=DEFAULT_TIMEZONES,
    )

    parser.addini(
        "tz_locales",
        type="linelist",
        help="List of locale identifiers (one per line).",
        default=DEFAULT_LOCALES,
    )


def _filter_valid_timezones(tzs: List[str]) -> List[str]:
    """
    Return only zones that are present in the local tzdb, plus our sentinel.
    Unknown names are warned once and skipped.
    """
    valid: List[str] = []
    bad: List[str] = []

    for tz in tzs:
        if _is_system_sentinel(tz, SYSTEM_TZ):
            valid.append(SYSTEM_TZ)
            continue
        try:
            ZoneInfo(tz)
            valid.append(tz)
        except ZoneInfoNotFoundError:
            bad.append(tz)

    if bad:
        warnings.warn(
            "tzshift: ignoring unknown time-zones: " + ", ".join(repr(z) for z in bad),
            stacklevel=2,
        )
    return valid


def _as_list(value: Any | None) -> list[str]:
    """str → [str], sequence → list, None → []  (makes downstream simpler)."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)  # type: ignore[arg-type]


def _collect_marker_overrides(node) -> tuple[bool, list[str] | None, list[str] | None]:
    """
    Walk up the node hierarchy (function -> class -> module) and return the
    innermost tzshift marker's directives.  Precedence: function >
    class > module.  Returns (disable, timezones, locales) where any element
    may be 'None' meaning 'no override here'.
    """
    disable: bool | None = None
    timezones: list[str] | None = None
    locales: list[str] | None = None

    # pytest guarantees the list is ordered: node itself first, then parents.
    for m in node.iter_markers(name="tzshift"):
        if disable is None and m.kwargs.get("disable", False):
            disable = True
        # keep the first occurrence; skip outer ones after
        if timezones is None and "timezones" in m.kwargs:
            timezones = _as_list(m.kwargs["timezones"])
        if locales is None and "locales" in m.kwargs:
            locales = _as_list(m.kwargs["locales"])

    return bool(disable), timezones, locales


@functools.lru_cache(maxsize=None)
def _locale_is_available(loc: str) -> bool:
    """
    Return True if loc can be set on this host.
    """
    if _is_system_sentinel(loc, SYSTEM_LOCALE):
        return True

    # Snapshot current locale
    original_locale = locale.setlocale(locale.LC_ALL)

    try:
        locale.setlocale(locale.LC_ALL, loc)
    except locale.Error:
        return False
    finally:
        # Rollback
        locale.setlocale(locale.LC_ALL, original_locale)

    return True


def _filter_valid_locales(locs: List[str]) -> List[str]:
    """
    Keep only locales that can actually be set on this host, plus the sentinel.
    The expensive system call is executed *once per distinct locale* thanks to
    the `_locale_is_available` LRU cache.
    """
    valid: List[str] = []
    bad: List[str] = []

    for loc in locs:
        if _locale_is_available(loc):
            # Normalise the sentinel so downstream code sees a single spelling
            valid.append(
                SYSTEM_LOCALE if _is_system_sentinel(loc, SYSTEM_LOCALE) else loc
            )
        else:
            bad.append(loc)

    if bad:
        warnings.warn(
            "tzshift: ignoring unavailable locales: "
            + ", ".join(repr(locale) for locale in bad),
            stacklevel=2,
        )
    return valid


def _get_max_combinations(config: pytest.Config) -> int | None:
    """
    Return an integer limit for tzshift_max CLI option.
    """
    val = config.getoption("tzshift_max")
    if val is None:
        val = config.getini("tzshift_max")
    try:
        max_val = int(val)
    except (TypeError, ValueError):
        raise pytest.UsageError("tzshift: --tzshift-max must be an integer")
    if max_val < 0:
        raise pytest.UsageError("tzshift: --tzshift-max cannot be negative")
    return None if max_val == 0 else max_val


def _cli_or_ini(config: pytest.Config, name: str) -> List[str]:
    """
    Return the value of name taken from the command line if present,
    otherwise from the ini file. Always normalises to a deduplicated list.
    """
    cli_val = config.getoption(name)
    if cli_val is not None:
        values = [x.strip() for x in cli_val.split(",") if x.strip()]
    else:
        values = list(config.getini(name))
    # preserve order but drop duplicates
    return list(dict.fromkeys(values))


def get_configured_timezones(config: pytest.Config) -> List[str]:
    return _cli_or_ini(config, "tz_timezones")


def get_configured_locales(config: pytest.Config) -> List[str]:
    return _cli_or_ini(config, "tz_locales")


def _pretty(val: str) -> str:
    """Human-friendly identifier for system-sentinel values."""
    if _is_system_sentinel(val, SYSTEM_TZ) or _is_system_sentinel(val, SYSTEM_LOCALE):
        return "sys"
    return val


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    A pytest hook that parametrizes tests requesting the 'tzshift' fixture.

    This is the core engine of the plugin. It performs the following steps:
    1.  Checks if a test function requests the `tzshift` fixture.
    2.  Gathers timezone and locale lists from CLI options or the pytest.ini file.
    3.  Filters these lists to include only those valid on the current system.
    4.  Checks for `@pytest.mark.tzshift` to apply test-specific overrides.
    5.  Generates the Cartesian product of the final timezone and locale lists.
    6.  Caps the number of combinations if `--tzshift-max` is set.
    7.  Injects the `(timezone, locale)` pairs into the test run.
    """
    if metafunc.config.getoption("no_tzshift"):
        return

    wanted = {"tzshift"}
    if not wanted.intersection(metafunc.fixturenames):
        return  # nothing to parametrize

    # read cli / ini first
    timezones = _filter_valid_timezones(get_configured_timezones(metafunc.config))
    locales = _filter_valid_locales(get_configured_locales(metafunc.config))

    # allow per test overrides
    disable, tz_override, loc_override = _collect_marker_overrides(metafunc.definition)
    if disable:
        return

    if tz_override is not None:  # explicit override
        timezones = _filter_valid_timezones(tz_override)
    if loc_override is not None:
        locales = _filter_valid_locales(loc_override)

    if not timezones:
        raise pytest.UsageError("tzshift: no valid time-zones to test with")
    if not locales:
        raise pytest.UsageError("tzshift: no valid locales to test with")

    combos = list(dict.fromkeys(product(timezones, locales)))

    # tzshift_max logic
    max_combos = _get_max_combinations(metafunc.config)
    if max_combos is not None and len(combos) > max_combos:
        warnings.warn(
            f"tzshift: limiting parameterisation to first {max_combos} of "
            f"{len(combos)} combinations (see --tzshift-max)",
            stacklevel=2,
        )
        combos = combos[:max_combos]

    w = max(1, len(str(len(combos) - 1)))

    ids = [
        f"{idx:{w}d}|{_pretty(tz)}|{_pretty(loc)}"
        for idx, (tz, loc) in enumerate(combos)
    ]

    metafunc.parametrize("tzshift", combos, ids=ids, indirect=True)


@pytest.fixture
def tzshift(request: pytest.FixtureRequest) -> TzShift:
    """
    A pytest fixture that sets the timezone and locale for a single test run.

    For each parametrized test case, this fixture:
    1.  Saves the original `TZ` environment variable and system locale.
    2.  Sets the `TZ` environment variable and the `LC_ALL` locale according
        to the current test's parameters. A special value of "SYSTEM" for
        either setting will leave the original system value untouched.
    3.  Calls `time.tzset()` to ensure the operating system recognizes the
        timezone change.
    4.  Yields a `TzShift` object containing the active `(timezone, locale)` pair.
    5.  After the test completes, it reliably restores the original timezone
        and locale settings.
    """
    if hasattr(request, "param"):
        tz, loc = request.param
    else:
        tz, loc = SYSTEM_TZ, SYSTEM_LOCALE

    original_tz = os.environ.get("TZ")
    original_locale = locale.setlocale(locale.LC_ALL)

    # apply locale first
    if not _is_system_sentinel(loc, SYSTEM_LOCALE):
        try:
            locale.setlocale(locale.LC_ALL, loc)
        except locale.Error:
            pytest.skip(f"Locale {loc!r} not installed on this platform")

    # then apply tz
    if not _is_system_sentinel(tz, SYSTEM_TZ):
        os.environ["TZ"] = tz

    if hasattr(time, "tzset"):
        time.tzset()

    try:
        yield TzShift(tz, loc)
    finally:
        # restore locale
        locale.setlocale(locale.LC_ALL, original_locale)
        # restore TZ
        if original_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original_tz
        if hasattr(time, "tzset"):
            time.tzset()
