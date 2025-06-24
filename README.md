# pytest-tzshift

[![PyPI version](https://img.shields.io/pypi/v/pytest-tzshift.svg)](https://pypi.org/project/pytest-tzshift/)
[![CI](https://github.com/spedr/pytest-tzshift/actions/workflows/ci.yml/badge.svg)](https://github.com/spedr/pytest-tzshift/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

*A tiny Pytest plug-in that automatically re-runs your tests under a **matrix of time-zones and locales** so you can catch formatting, parsing, and daylight-saving bugs early.*

---

## Why?

Time-zones and locales are global process settings.
If your code **formats dates**, **parses user input**, or depends on **`datetime.now()`**, it may behave differently on users' machines.

`pytest-tzshift` attempts to make these differences visible:

```text
tests/test_format.py::test_human_readable[0|UTC|C]                  PASSED
tests/test_format.py::test_human_readable[1|America/New_York|C]     PASSED
tests/test_format.py::test_human_readable[2|Europe/Berlin|de_DE]    FAILED
```

---

## Installation

```bash
pip install pytest-tzshift          # requires Python ≥ 3.9
```

No further setup is necessary. The plug-in is auto-discovered by Pytest.

---

## Quick start

Add the `tzshift` fixture to any test:

```python
def test_price_formatting(tzshift):
    tz, loc = tzshift              # tuple-unpack

    price = 1234.56
    formatted = format_price(price)    # your code

    assert formatted.endswith("€") if loc.startswith("de_") else "€" not in formatted
```

Run Pytest as usual; each test will execute for every `(timezone, locale)` pair.

---

## Default matrix

| Time-zones (IANA)  | Locales (POSIX / glibc) |
| ------------------ | ----------------------- |
| `UTC`              | `C`                     |
| `America/New_York` | `en_US.UTF-8`           |
| `Europe/London`    | `de_DE.UTF-8`           |
| `Asia/Kolkata`     | `fr_FR.UTF-8`           |
| `Australia/Sydney` | `ja_JP.UTF-8`           |
| `Asia/Tokyo`       |                         |

Unavailable zones/locales are skipped with a warning.

---

## Customising the matrix

### Project-wide (`pytest.ini`)

```ini
[pytest]
tz_timezones =
    SYSTEM          # keep OS default
    Europe/Paris
tz_locales =
    SYSTEM
    fr_FR.UTF-8
tzshift_max = 10     # cap the total Cartesian product (0 = unlimited)
```

### Command line

```bash
pytest --tz-timezones=UTC,Asia/Tokyo --tz-locales=C,ja_JP.UTF-8
pytest --tzshift-max=20
pytest --no-tzshift                     # disable for this run
```

### Per-test marker

```python
import pytest

@pytest.mark.tzshift(timezones=["UTC"], locales=["C"])
def test_once_only(tzshift):
    ...

@pytest.mark.tzshift(disable=True)
def test_native_env():
    ...
```

---

## How it works

* **Collection phase**
  `pytest_generate_tests` builds the Cartesian product of the selected time-zones and locales, applies an optional `--tzshift-max` limit, and parametrises the fixture indirectly.

* **Fixture**
  For each combination, the `tzshift` fixture

  1. Saves the original `TZ` env-var and current locale,
  2. Calls `locale.setlocale(LC_ALL, …)` (skips if unavailable),
  3. Exports `TZ=…` and calls `time.tzset()` (on platforms that support it),
  4. Yields an immutable `TzShift(timezone, locale)` helper,
  5. Restores everything in a `finally` block.

---

## Platform notes

* On **Windows**, `time.tzset()` is missing; the time-zone part becomes a no-op (locales still work).
  You'll still see separate parametrised runs, but all in the system zone.
* Changing the process locale is global; avoid running locale-sensitive tests in parallel workers.

---

## Documentation

* **Quick start** – `docs/usage/quickstart.md`
* **Configuration details** – `docs/usage/configuration.md`
* **Markers & fixtures** – `docs/usage/markers.md`
* **API reference** – `docs/reference/api.md`

Browse the full site at **[https://spedr.github.io/pytest-tzshift](https://spedr.github.io/pytest-tzshift)** once published.

---

## Contributing

Bug reports, feature ideas, and pull requests are warmly welcome!
See [CONTRIBUTING](docs/contributing.md) for tips on setting up a dev environment, coding style, and running the test suite.

---

## License

Released under the [MIT License](license.md).