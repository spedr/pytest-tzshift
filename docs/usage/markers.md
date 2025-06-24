# Markers & Fixtures

## `@pytest.mark.tzshift` Marker

The `tzshift` marker lets you override or disable timezone/locale parametrization on a **per-test**, **per-class**, or **per-module** basis.
This is the most flexible way to fine-tune the matrix of environments your test runs in.

---

### Basic usage

Apply the marker directly to a test function:

```python
import pytest

@pytest.mark.tzshift(timezones=["UTC"], locales=["C"])
def test_only_once(tzshift):
    # This test will run only once, with UTC and 'C' locale.
    ...
```

---

### Marker options

| Argument  | Type       | Description                                                             |
| --------- | ---------- | ----------------------------------------------------------------------- |
| timezones | list\[str] | List of timezones (e.g., `["UTC", "America/New_York"]`). Optional.      |
| locales   | list\[str] | List of locales (e.g., `["en_US.UTF-8", "C"]`). Optional.               |
| disable   | bool       | Set to `True` to **completely disable** tzshift for this test or scope. |

* If neither `timezones` nor `locales` is specified, the defaults from config or CLI are used.
* If `disable=True`, the test runs exactly once in the system's default environment.

---

### Disabling per test or group

```python
@pytest.mark.tzshift(disable=True)
def test_no_parametrize():
    # No timezone/locale parametrization for this test.
    ...
```

You can also apply this marker to a **class** or **module** to affect all contained tests:

```python
@pytest.mark.tzshift(timezones=["Europe/London"])
class TestOnlyLondon:
    def test_london_tz(self, tzshift):
        ...
```

---

### Precedence and inheritance

* The **innermost** marker always takes precedence:

  * Function > Class > Module > Global config/CLI options.

Example:

```python
@pytest.mark.tzshift(timezones=["Europe/Berlin"])
class TestBerlin:
    @pytest.mark.tzshift(timezones=["UTC"])
    def test_only_utc(self, tzshift):
        # Runs only with UTC, not Berlin.
        ...
```

---

### Using the “SYSTEM” sentinel

If you want to include the **system’s default timezone or locale**, use `"SYSTEM"` (case-insensitive), or just an empty string:

```python
@pytest.mark.tzshift(timezones=["SYSTEM", "UTC"], locales=["SYSTEM", "C"])
def test_including_system_defaults(tzshift):
    ...
```

---

## `tzshift` Fixture

Requesting the `tzshift` fixture in your test enables parametrization and gives you information about the current environment:

```python
def test_show_current_env(tzshift):
    tz, loc = tzshift  # or use tzshift.timezone, tzshift.locale
    print(f"Now testing under TZ={tz}, locale={loc}")
```

The fixture is an immutable object (`TzShift`) that can be unpacked as a tuple or accessed via attributes.

---

## Parametrization IDs

Each test run will display an ID in the test output, e.g.:

```
test_module.py::test_example[0|UTC|C] PASSED
test_module.py::test_example[1|America/New_York|en_US.UTF-8] PASSED
```

Where each bracketed ID is `[index|timezone|locale]`.

---

## Summary Table

| Where used | Example usage                                      | Effect                                   |
| ---------- | -------------------------------------------------- | ---------------------------------------- |
| Per-test   | `@pytest.mark.tzshift(timezones=["UTC"])`          | Only use UTC for this test               |
| Per-class  | `@pytest.mark.tzshift(locales=["C"])`              | All tests in the class use only C locale |
| Per-module | Place marker in `pytestmark = [...]` at module top | All tests in module inherit the marker   |
| Disable    | `@pytest.mark.tzshift(disable=True)`               | Run only once, with system defaults      |

---

See also:

* [Configuration](configuration.md) for setting global defaults
* [Quickstart](quickstart.md) for a minimal setup example

---
