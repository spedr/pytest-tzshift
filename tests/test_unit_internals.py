from __future__ import annotations

import os
import locale
import types
import sys
import dataclasses
import importlib

import pytest
from pytest_tzshift import TzShift
from pytest_tzshift import TzShift as PublicTzShift   # re-export from __init__
from pytest_tzshift import _types

plugin = importlib.import_module("pytest_tzshift.plugin")

def test_plugin_module_reimport_executes_top_level():
    """
    Some top level coverage.

    We also sanity-check that public constants survive the round-trip
    unchanged and that the helper `_is_system_sentinel` still behaves.
    """
    import importlib

    # Grab the already-imported module object
    import pytest_tzshift.plugin as plugin

    # Snapshot a few public attributes so we can compare after reload
    orig_tzs = list(plugin.DEFAULT_TIMEZONES)
    orig_locs = list(plugin.DEFAULT_LOCALES)
    orig_sys_tz = plugin.SYSTEM_TZ
    orig_sys_loc = plugin.SYSTEM_LOCALE

    # the actual reload that drives coverage
    reloaded = importlib.reload(plugin)

    # The module object is reused, not replaced
    assert reloaded is plugin

    # Public constants remain identical
    assert reloaded.DEFAULT_TIMEZONES == orig_tzs
    assert reloaded.DEFAULT_LOCALES == orig_locs
    assert reloaded.SYSTEM_TZ == orig_sys_tz == "SYSTEM"
    assert reloaded.SYSTEM_LOCALE == orig_sys_loc == "SYSTEM"

    # A couple of correctness spot-checks on the helper
    for good in ["SYSTEM", " system ", "", "SyStEm"]:
        assert reloaded._is_system_sentinel(good, reloaded.SYSTEM_TZ)
    for bad in [None, "UTC", "sys"]:
        assert not reloaded._is_system_sentinel(bad, reloaded.SYSTEM_TZ)

def test_tzshift_sequence_protocol_and_frozen():
    ts = TzShift("UTC", "C")

    # tuple-like unpacking
    tz, loc = ts
    assert (tz, loc) == ("UTC", "C")

    # len() and direct indexing
    assert len(ts) == 2
    assert ts[0] == "UTC"
    assert ts[1] == "C"
    with pytest.raises(IndexError):
        _ = ts[2]

    # explicit helper
    assert ts.as_tuple() == ("UTC", "C")

    # immutability and slots
    with pytest.raises(dataclasses.FrozenInstanceError):
        ts.timezone = "Europe/Paris"

    if sys.version_info >= (3, 10):
        assert not hasattr(ts, "__dict__")    # slots -> no instance dict
    assert "timezone" in ts.__slots__


def test_is_system_sentinel_recognises_variations():
    s = "SYSTEM"
    for candidate in ["SYSTEM", " system ", "SyStEm", ""]:
        assert plugin._is_system_sentinel(candidate, s)

    for candidate in [None, "UTC", "sys"]:
        assert not plugin._is_system_sentinel(candidate, s)


def test_as_list_helper_normalises():
    assert plugin._as_list(None) == []
    assert plugin._as_list("foo") == ["foo"]

    seq = ["a", "b"]
    out = plugin._as_list(seq)
    assert out == seq and out is not seq      # new shallow list


def test_pretty_helper():
    assert plugin._pretty("SYSTEM") == "sys"
    assert plugin._pretty("system") == "sys"
    assert plugin._pretty("UTC") == "UTC"

class _DummyConfig:
    """Minimal stub that satisfies only what _get_max_combinations touches."""

    def __init__(self, option_val, ini_val):
        self._opt = option_val
        self._ini = ini_val

    def getoption(self, name):
        return self._opt if name == "tzshift_max" else None

    def getini(self, name):
        return self._ini if name == "tzshift_max" else 0


@pytest.mark.parametrize(
    "cli, ini, expected",
    [
        (5, 0, 5),          # CLI beats ini
        (None, 7, 7),       # ini used when CLI silent
        (0, 3, None),       # zero means "no cap"
        (None, 0, None),    # same for ini
    ],
)
def test_get_max_combinations_valid(cli, ini, expected):
    cfg = _DummyConfig(cli, ini)
    assert plugin._get_max_combinations(cfg) == expected


@pytest.mark.parametrize("bad", ["oops", -1])
def test_get_max_combinations_invalid_raises(bad):
    cfg = _DummyConfig(bad, 0)
    with pytest.raises(pytest.UsageError):
        plugin._get_max_combinations(cfg)


def test_package_dunder_all_and_reexport():
    pkg = importlib.import_module("pytest_tzshift")

    # Public API promises
    assert "TzShift" in pkg.__all__

    # And the public name must be the same object that lives in _types
    assert PublicTzShift is _types.TzShift is pkg.TzShift


def test_types_module_reimport_executes_top_level(monkeypatch):
    """
    Re-importing pytest_tzshift._types during test time guarantees the
    module-level statements are executed under coverage (they ran already
    during collection, which happens before coverage starts).
    """
    name = "pytest_tzshift._types"

    # Drop the cached module so that a fresh import re-executes the file
    sys.modules.pop(name, None)

    new_mod = importlib.import_module(name)

    # A couple of basic sanity checks
    assert hasattr(new_mod, "PY310_PLUS")
    assert isinstance(new_mod.PY310_PLUS, bool)
    assert callable(new_mod._dataclass)
    assert hasattr(new_mod, "TzShift")


def test__dataclass_emulation_when_py39(monkeypatch):
    """
    Force the helper down its "Python < 3.10" branch and make sure it creates
    a frozen, slotted dataclass even though the real runtime can be 3.10+.

    We patch the module constant instead of juggling sys.version_info or a
    full reload.
    """
    # Make the decorator believe we're running under 3.9
    monkeypatch.setattr(_types, "PY310_PLUS", False, raising=False)

    @_types._dataclass(frozen=True, slots=True)
    class Dummy:
        x: int
        y: int = 0

    d = Dummy(4)

    # It is a dataclass and it is frozen
    assert dataclasses.is_dataclass(Dummy)
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.x = 99  # type: ignore[attr-defined]

    # The helper must have synthesised __slots__ manually
    assert hasattr(Dummy, "__slots__") and Dummy.__slots__ == ("x", "y")

    # Tuple-like behaviour inherited from dataclasses doesn't change
    assert (d.x, d.y) == dataclasses.astuple(d)



# Some tzshift fixture tests
# We need to access real generator function that lives under the fixture wrapper
# Or else we get hit with "Fixtures are not meant to be called directly"
_tzshift_gen_fn = plugin.tzshift.__wrapped__


class _FakeRequestNoParam:
    """Mimic a pytest request object without the .param attribute."""
    pass


def _run_gen(gen):
    """
    Helper: run a generator fixture until completion so that its
    finally block executes and environment is restored.
    """
    try:
        next(gen)          # enter the fixture (runs code up to `yield`)
    except StopIteration:  # pragma: no cover – shouldn't happen
        return
    with pytest.raises(StopIteration):
        next(gen)          # exhaust -> triggers finally


def test_tzshift_default_no_param_preserves(monkeypatch):
    """
    When the fixture is invoked without parametrisation it should yield the
    SYSTEM/SYSTEM sentinel pair and leave env/locale untouched.
    """
    monkeypatch.delenv("TZ", raising=False)
    original_locale = locale.setlocale(locale.LC_ALL)

    gen = _tzshift_gen_fn(_FakeRequestNoParam())
    ts = next(gen)
    assert ts.as_tuple() == ("SYSTEM", "SYSTEM")
    assert os.environ.get("TZ") is None
    assert locale.setlocale(locale.LC_ALL) == original_locale

    # exhaust & verify restoration
    with pytest.raises(StopIteration):
        next(gen)
    assert os.environ.get("TZ") is None
    assert locale.setlocale(locale.LC_ALL) == original_locale


def test_tzshift_preserves_existing_tz(monkeypatch):
    """
    If TZ was already set, SYSTEM/SYSTEM must keep that value and restore it.
    """
    monkeypatch.setenv("TZ", "Europe/London")
    original_locale = locale.setlocale(locale.LC_ALL)

    req = types.SimpleNamespace(param=("SYSTEM", "SYSTEM"))
    gen = _tzshift_gen_fn(req)
    ts = next(gen)
    assert ts == plugin.TzShift("SYSTEM", "SYSTEM")
    assert os.environ["TZ"] == "Europe/London"

    _run_gen(gen)
    assert os.environ["TZ"] == "Europe/London"
    assert locale.setlocale(locale.LC_ALL) == original_locale


def test_tzshift_changes_timezone_and_restores(monkeypatch):
    """
    Non-sentinel timezone should be applied then rolled back.
    """
    monkeypatch.delenv("TZ", raising=False)
    req = types.SimpleNamespace(param=("UTC", "SYSTEM"))

    gen = _tzshift_gen_fn(req)
    ts = next(gen)
    assert ts.timezone == "UTC"
    assert os.environ["TZ"] == "UTC"

    _run_gen(gen)
    # back to “unset”
    assert "TZ" not in os.environ


def test_tzshift_changes_locale_and_restores(monkeypatch):
    """
    Non-sentinel locale ("C" is always available) should take effect and then
    be restored afterwards.
    """
    original_locale = locale.setlocale(locale.LC_ALL)
    req = types.SimpleNamespace(param=("SYSTEM", "C"))

    gen = _tzshift_gen_fn(req)
    ts = next(gen)
    current = locale.setlocale(locale.LC_ALL)
    assert ts.locale == "C"
    assert current.lower().startswith("c")

    _run_gen(gen)
    assert locale.setlocale(locale.LC_ALL) == original_locale


def test_tzshift_skips_on_unavailable_locale(monkeypatch):
    """
    If the requested locale cannot be set, the fixture should call
    pytest.skip (which raises Skipped).
    """
    bad_locale = "xx_YY.UNKNOWN"
    req = types.SimpleNamespace(param=("SYSTEM", bad_locale))
    gen = _tzshift_gen_fn(req)

    with pytest.raises(pytest.skip.Exception):
        next(gen)          # raises before the yield point

    # The generator never yielded, but we can still close it safely to avoid
    # "generator ignored GeneratorExit" warnings.
    gen.close()