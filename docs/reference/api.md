# API Reference

This page lists the public objects exposed by **pytest-tzshift**.
Everything else in the source tree should be considered **internal** and may change without notice.

!!! tip
The tables below are generated automatically by **mkdocstrings** from the
docstrings in the code.
Click on a signature to expand the full documentation.

---

## Top-level package

\::: pytest\_tzshift

---

## `TzShift` helper class

A tiny immutable value object that represents a single `(timezone, locale)` combination and behaves like a 2-tuple.

\::: pytest\_tzshift.\_types.TzShift

---

## Pytest fixture

### `tzshift`

*Scope: function*

Requesting this fixture in a test function activates timezone/locale parametrisation and yields a **`TzShift`** for the current combination.

```python
def test_formatting(tzshift):
    tz, loc = tzshift           # tuple-unpacking works
    assert isinstance(tzshift.timezone, str)
    assert isinstance(tzshift.locale, str)
```

| Attribute   | Type  | Description                                      |
| ----------- | ----- | ------------------------------------------------ |
| `.timezone` | `str` | The IANA timezone name currently in effect.      |
| `.locale`   | `str` | The POSIX/GLIBC locale currently set (`LC_ALL`). |

You rarely need to import anything—just ask for the fixture.

---

## CLI options

| Option             | Description                                       | Config key     |
| ------------------ | ------------------------------------------------- | -------------- |
| `--tz-timezones=…` | Comma-separated list of IANA time-zones to sweep. | `tz_timezones` |
| `--tz-locales=…`   | Comma-separated list of locales to sweep.         | `tz_locales`   |
| `--tzshift-max=N`  | Cap the number of `(tz, locale)` combinations.    | `tzshift_max`  |
| `--no-tzshift`     | Disable all parametrisation for this run.         | *(none)*       |

All options have matching keys in `pytest.ini` / `pyproject.toml`; CLI flags always win.

---

## Marker

### `@pytest.mark.tzshift`

```python
@pytest.mark.tzshift(
    timezones=["UTC", "America/New_York"],
    locales=["C"],
    disable=False
)
def test_my_function(tzshift):
    ...
```

| Argument    | Type        | Meaning                                                           |
| ----------- | ----------- | ----------------------------------------------------------------- |
| `timezones` | `list[str]` | Replace the configured time-zone list for this test/class/module. |
| `locales`   | `list[str]` | Replace the configured locale list.                               |
| `disable`   | `bool`      | If `True`, run the test exactly once with the system defaults.    |

Precedence: **function > class > module > global config**.

---

## Sentinel constants

| Name            | Value      | Meaning                                                |
| --------------- | ---------- | ------------------------------------------------------ |
| `SYSTEM_TZ`     | `"SYSTEM"` | Keep the system’s current time-zone for this position. |
| `SYSTEM_LOCALE` | `"SYSTEM"` | Keep the system’s current locale.                      |

These are meant to be passed via markers or CLI/config lists:

```ini
[pytest]
tz_timezones = SYSTEM, UTC
tz_locales   = SYSTEM, en_US.UTF-8
```

---

### Stability policy

* Objects documented on this page follow **semantic versioning**.
* Anything not listed here (private helpers, internal modules) may change at any time without a major version bump.

If you need something that is not yet part of the public API, please open an issue so we can make it official!