from textwrap import dedent
import importlib
import locale

# --------------------------------------------------------------------------- #
# Dynamically discover the current defaults from the freshly-loaded plug-in
plugin = importlib.import_module("pytest_tzshift.plugin")
DEF_TZS = plugin.DEFAULT_TIMEZONES
SYSTEM_LOCALE = plugin.SYSTEM_LOCALE
# --------------------------------------------------------------------------- #

TEST_CODE = dedent(
    """
    def test_timezone_and_locale_are_applied(tzshift):
        tz, loc = tzshift
        print(f"[inner] running in {tz}/{loc}")
        assert tz and loc
"""
)


def get_available_locales(candidates: list[str]) -> list[str]:
    """
    Filters a list of locale candidates, returning only those available on the
    current system. This makes tests robust across different environments.
    """
    available = []
    original = locale.setlocale(locale.LC_ALL)
    try:
        for loc in candidates:
            if loc.upper() == SYSTEM_LOCALE:
                available.append(loc)
                continue
            try:
                locale.setlocale(locale.LC_ALL, loc)
                available.append(loc)
            except locale.Error:
                pass  # Locale not available, skip it
    finally:
        locale.setlocale(locale.LC_ALL, original)
    return available


def test_plugin_default_configuration(pytester):
    """
    With no overrides, the plugin uses its default lists.
    We check against the available locales on the system to avoid flakiness.
    """
    pytester.makepyfile(TEST_CODE)

    available_locales = get_available_locales(plugin.DEFAULT_LOCALES)
    expected_runs = len(DEF_TZS) * len(available_locales)

    res = pytester.runpytest("-q")
    res.assert_outcomes(passed=expected_runs)


def test_plugin_cli_tz_override(pytester):
    """
    CLI must override ini/default timezones.
    """
    pytester.makepyfile(TEST_CODE)
    res = pytester.runpytest(
        "--tz-timezones=UTC,Pacific/Honolulu", "--tz-locales=C", "-q"
    )
    res.assert_outcomes(passed=2)  # 2 TZs * 1 Locale


def test_plugin_cli_locale_override(pytester):
    """Locale override alone (timezones default)."""
    pytester.makepyfile(TEST_CODE)

    test_locales = ["C", "de_DE.UTF-8"]
    available_locales = get_available_locales(test_locales)
    expected_runs = len(DEF_TZS) * len(available_locales)

    res = pytester.runpytest(f"--tz-locales={','.join(test_locales)}", "-q")
    res.assert_outcomes(passed=expected_runs)


def test_plugin_ini_configuration(pytester):
    """Values from pytest.ini are honoured when CLI is silent."""
    pytester.makeini(
        dedent(
            """
        [pytest]
        tz_timezones =
            Europe/Paris
            Africa/Cairo
        tz_locales = C
    """
        )
    )
    pytester.makepyfile(TEST_CODE)
    res = pytester.runpytest("-q")
    res.assert_outcomes(passed=2)  # 2 TZs * 1 Locale


def test_plugin_cli_overrides_ini(pytester):
    """CLI must win over ini for both dimensions."""
    pytester.makeini(
        dedent(
            """
        [pytest]
        tz_timezones = Asia/Tokyo
        tz_locales   = C
    """
        )
    )
    pytester.makepyfile(TEST_CODE)
    res = pytester.runpytest(
        "--tz-timezones=UTC,America/New_York", "--tz-locales=C,en_US.UTF-8", "-q"
    )

    available_locales = get_available_locales(["C", "en_US.UTF-8"])
    expected_runs = 2 * len(available_locales)
    res.assert_outcomes(passed=expected_runs)


def test_unrelated_test_is_not_parametrized(pytester):
    """A test file with no tzshift-fixtures should run exactly once."""
    pytester.makepyfile("def test_plain(): assert True")
    res = pytester.runpytest("-q")
    res.assert_outcomes(passed=1)


def test_duplicate_options_are_deduplicated(pytester):
    pytester.makepyfile("def test_ok(tzshift): pass")
    res = pytester.runpytest(
        "--tz-locales=C,C,en_US.UTF-8,C", "--tz-timezones=UTC,UTC", "-q"
    )

    available_locales = get_available_locales(["C", "en_US.UTF-8"])
    # 1 unique TZ * number of unique available locales
    res.assert_outcomes(passed=len(available_locales))


def test_notzshift_disables_plugin(pytester):
    pytester.makepyfile(
        """
        import pytest, os
        def test_once(tzshift):
            assert tzshift.timezone == "SYSTEM"
            assert tzshift.locale == "SYSTEM"
    """
    )
    res = pytester.runpytest("--no-tzshift", "-q")
    res.assert_outcomes(passed=1)


def test_combo_cap(pytester):
    pytester.makeini(
        """
        [pytest]
        tz_timezones =
            UTC
            Europe/London
        tz_locales =
            C
            de_DE.UTF-8
        tzshift_max = 3
        """
    )
    pytester.makepyfile(
        """
        def test_dummy(tzshift):
            pass
        """
    )

    res = pytester.runpytest("-q")
    res.assert_outcomes(passed=3, warnings=1)
    res.stdout.fnmatch_lines(
        ["*tzshift: limiting parameterisation to first 3 of 4 combinations*"]
    )
