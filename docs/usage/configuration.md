# Configuration

You can control **pytest-tzshift** using your `pytest.ini`/`pyproject.toml` config file, command-line flags, and per-test markers. This page explains all options and how they interact.

---

## 1. Configuration File Options (`pytest.ini` or `pyproject.toml`)

Add these under your `[pytest]` section:

```ini
[pytest]
tz_timezones =
    UTC
    America/New_York
    Europe/Berlin

tz_locales =
    C
    en_US.UTF-8
    de_DE.UTF-8

tzshift_max = 12
```

### Option reference

| Option         | Type     | Description                                                                                                     |
| -------------- | -------- | --------------------------------------------------------------------------------------------------------------- |
| `tz_timezones` | linelist | List of IANA timezone names. One per line. Default: UTC, New York, London, Kolkata, Sydney, Tokyo               |
| `tz_locales`   | linelist | List of POSIX locales (e.g., `en_US.UTF-8`). Default: C, en\_US.UTF-8, de\_DE.UTF-8, fr\_FR.UTF-8, ja\_JP.UTF-8 |
| `tzshift_max`  | int      | Maximum number of timezone/locale combinations to generate. Default: unlimited (`0`)                            |

---

## 2. Command-Line Options

All config options can also be set as command-line flags, overriding values in config files:

| CLI Option       | Example Value                 | Description                                   |
| ---------------- | ----------------------------- | --------------------------------------------- |
| `--tz-timezones` | `UTC,Europe/Paris,Asia/Tokyo` | Comma-separated list of IANA timezones to use |
| `--tz-locales`   | `C,en_GB.UTF-8,fr_FR.UTF-8`   | Comma-separated list of locales to use        |
| `--tzshift-max`  | `5`                           | Maximum number of combinations to generate    |
| `--no-tzshift`   | *(no value)*                  | Completely disables tzshift for this test run |

**Examples:**

```shell
pytest --tz-timezones=Asia/Tokyo,UTC --tz-locales=ja_JP.UTF-8,C
pytest --tzshift-max=10
pytest --no-tzshift
```

*Note: Command-line values take priority over `pytest.ini`.*

---

## 3. Per-Test or Per-Class/Module Control with Markers

You can override or disable timezones/locales for specific tests or groups using the `@pytest.mark.tzshift` marker.

### Example: Override for a single test

```python
import pytest

@pytest.mark.tzshift(timezones=["UTC"], locales=["C"])
def test_specific(tzshift):
    # Will only run once, with UTC and C locale
    ...
```

### Example: Disable for a test

```python
@pytest.mark.tzshift(disable=True)
def test_no_parametrize():
    # No tz/locale parametrization for this test
    ...
```

### Precedence

* **Most specific wins:** Function > Class > Module > Config/CLI defaults.

---

## 4. Special Values: The “SYSTEM” Sentinel

If you want to include the **system default** timezone or locale, use `"SYSTEM"` (case-insensitive, or just an empty string):

```python
@pytest.mark.tzshift(timezones=["SYSTEM", "UTC"], locales=["SYSTEM", "en_US.UTF-8"])
def test_with_system_defaults(tzshift):
    ...
```

* `"SYSTEM"` means “leave as is” for timezone or locale in that combination.

---

## 5. Example: Complete `pytest.ini`

```ini
[pytest]
tz_timezones =
    SYSTEM
    Europe/Paris
tz_locales =
    SYSTEM
    fr_FR.UTF-8
tzshift_max = 6
```

---

## 6. How combinations are generated

* The plugin forms the **Cartesian product** of all selected timezones and locales.
* The total number can be limited with `tzshift_max`.
* If any combination is invalid on your machine (e.g. a missing locale), it is automatically skipped and a warning is shown.

---

## 7. Disabling pytest-tzshift entirely

For a whole run, just add `--no-tzshift`:

```shell
pytest --no-tzshift
```

Or use `disable=True` in a marker to skip for specific tests.

---

## 8. Tips

* On **Windows**, timezone changes may have no effect due to system limitations.
* **Locale changes are process-wide.** Avoid running locale-sensitive tests in parallel (one pytest worker).
* Unknown or unsupported timezones/locales will be ignored with a warning.

---

For more advanced usage, see [Markers & Fixtures](markers.md) and [API Reference](reference/api.md).