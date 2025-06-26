# Configuration

You can set project-wide defaults, override them for a specific test run via the command line, or apply fine-grained control to individual tests or modules using markers.

This guide covers the three layers of configuration, from the broadest to the most specific.

## Configuration Layers

Understanding the order of precedence is key to using `pytest-tzshift` effectively. Settings are applied in the following order, with later steps overriding earlier ones:

1.  **`pytest.ini` / `pyproject.toml`**: This is where you set your project-wide defaults. It's the best place to define the core set of timezones and locales you want to test against.
2.  **Command-Line Options**: These flags override the `ini` file settings, making them perfect for CI runs or temporary adjustments without modifying project files.
3.  **`@pytest.mark.tzshift` Marker**: This marker provides the most granular control, allowing you to change or disable parametrization for a specific test function, class, or module.

Let's dive into each layer.

---

## 1. Project-Wide Defaults (`pytest.ini` or `pyproject.toml`)

For most projects, you'll want a consistent set of timezones and locales for all your tests. You can define these in your `pytest.ini` or `pyproject.toml` file.

### Available Settings

*   `tz_timezones`: A list of IANA timezone names (one per line).
*   `tz_locales`: A list of locale identifiers (one per line).
*   `tzshift_max`: An integer to cap the total number of generated test combinations. `0` means no limit.

### Example: `pytest.ini`

```ini
# pytest.ini
[pytest]
tz_timezones =
    UTC
    America/Los_Angeles
    Europe/Paris

tz_locales =
    C
    en_US.UTF-8
    fr_FR.UTF-8

# Don't generate more than 50 combinations in total
tzshift_max = 50
```

### Example: `pyproject.toml`

If you prefer using `pyproject.toml`, the configuration is equivalent:

```toml
# pyproject.toml
[tool.pytest.ini_options]
tz_timezones = [
    "UTC",
    "America/Los_Angeles",
    "Europe/Paris",
]
tz_locales = [
    "C",
    "en_US.UTF-8",
    "fr_FR.UTF-8",
]
# Don't generate more than 50 combinations in total
tzshift_max = 50
```

> **Note:** If you don't provide any configuration, `pytest-tzshift` uses a built-in list of common timezones and locales as a sensible default.

---

## 2. Command-Line Overrides

For temporary changes, you can override the `ini` settings from the command line. This is especially useful in CI/CD pipelines where you might want to run a faster, more limited set of combinations.

### Available Options

*   `--tz-timezones`: A comma-separated string of timezone names.
*   `--tz-locales`: A comma-separated string of locale identifiers.
*   `--tzshift-max`: An integer cap on test combinations.
*   `--no-tzshift`: A flag to disable the plugin entirely for the current run.

### Example Usage

Imagine your `pytest.ini` defines 5 timezones and 5 locales (25 combinations). For a quick pull request check, you could run:

```bash
pytest --tz-timezones="UTC,America/New_York" --tz-locales="en_US.UTF-8"
```

This command will ignore the `ini` settings and run your tests against only two combinations: `(UTC, en_US.UTF-8)` and `(America/New_York, en_US.UTF-8)`.

To disable the plugin for a single run without changing any code:

```bash
pytest --no-tzshift
```

---

## 3. Fine-Grained Control with Markers

The `@pytest.mark.tzshift` marker gives you ultimate control at the level of a test, class, or module. It can override the global configuration or even disable parametrization for specific items.

### Marker Arguments

*   `timezones: List[str]`: A list of timezones to use for this scope.
*   `locales: List[str]`: A list of locales to use for this scope.
*   `disable: bool`: If `True`, disables `tzshift` parametrization for this scope.

### Example: Overriding for a Single Test

If you have a test that is specifically sensitive to Daylight Saving Time transitions in the US, you can target it precisely.

```python
import pytest
from datetime import datetime

@pytest.mark.tzshift(timezones=["America/New_York", "America/Chicago"])
def test_dst_transition(tzshift):
    # This test will only run with the two specified timezones,
    # but will use the globally configured locales.
    tz, loc = tzshift
    # ... test logic for DST ...
```

### Example: Overriding for a Class

You can apply the marker to a class to affect all tests within it.

```python
import pytest

@pytest.mark.tzshift(locales=["ja_JP.UTF-8"])
class TestJapaneseFormatting:
    def test_date_format(self, tzshift):
        # Will run with all configured timezones, but only the Japanese locale.
        ...

    def test_currency_format(self, tzshift):
        # Also runs with only the Japanese locale.
        ...
```

### Example: Disabling for a Specific Test

Sometimes, a test has no dependency on timezone or locale. Running it multiple times is redundant. You can easily opt-out.

```python
@pytest.mark.tzshift(disable=True)
def test_pure_math_logic(tzshift):
    # This test will run only once, with system default settings.
    # The `tzshift` fixture will still be available but won't cause parametrization.
    assert 2 + 2 == 4
```

---

## Special Values and Validation

### The "SYSTEM" Sentinel

`pytest-tzshift` recognizes the special string `"SYSTEM"` (case-insensitive) for both timezones and locales. When used, the plugin will not modify the system's current setting for that parameter.

This is useful for testing against a single, specific timezone while using the native environment of whatever machine is running the tests.

```python
# test_system_locale.py

import pytest

# Test a specific timezone against the user's native locale
@pytest.mark.tzshift(timezones=["Europe/Berlin"], locales=["SYSTEM"])
def test_against_system_locale(tzshift):
    # tzshift.timezone will be "Europe/Berlin"
    # tzshift.locale will be "SYSTEM", and the actual locale remains unchanged.
    ...
```