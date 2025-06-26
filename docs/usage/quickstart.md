# Quickstart Guide

Testing code that depends on the system's timezone or locale can be a headache. Your tests might pass on your machine in New York but fail in CI running in a UTC environment. `pytest-tzshift` solves this by making it trivial to run your tests across a matrix of different timezones and locales.

This guide will get you up and running in minutes.

## Installation

First, install the plugin using pip:

```bash
pip install pytest-tzshift
```

Pytest will automatically discover and enable the plugin.

## Basic Usage: The `tzshift` Fixture

The core of the plugin is the `tzshift` fixture. To use it, simply add it as an argument to your test function. The plugin will then automatically run your test multiple times, once for each combination of the default timezones and locales.

Let's say you have a function that formats the current time. Its output is sensitive to both the system's timezone (`%Z`) and locale (`%x`, `%X`).

```python
# test_time.py
import time
from datetime import datetime

def format_current_time():
    """Formats the current time, sensitive to TZ and locale."""
    # datetime.now() respects the TZ environment variable
    # strftime() respects the current locale for %x and %X
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z (%x)")

def test_datetime_formatting(tzshift):
    """
    This test will be run under various TZ/locale combinations.
    """
    # The tzshift fixture has already set the environment for us.
    # It also yields a handy object with the current settings.
    current_tz, current_locale = tzshift

    print(f"Testing with TZ={current_tz}, Locale={current_locale}")
    output = format_current_time()
    print(f"-> Output: {output}")

    # Your assertions would go here.
    # For this example, we'll just check that it runs.
    assert isinstance(output, str)
```

Now, run pytest:

```bash
pytest -v
```

You'll see your single test function expanded into many parametrized runs, with clear and filterable test IDs:

```text
$ pytest -v
========================= test session starts ==========================
...
collected 30 items

test_time.py::test_datetime_formatting[0|UTC|C] PASSED
test_time.py::test_datetime_formatting[1|UTC|en_US.UTF-8] SKIPPED
test_time.py::test_datetime_formatting[2|UTC|de_DE.UTF-8] SKIPPED
...
test_time.py::test_datetime_formatting[5|America/New_York|C] PASSED
test_time.py::test_datetime_formatting[6|America/New_York|en_US.UTF-8] SKIPPED
...
test_time.py::test_datetime_formatting[29|Asia/Tokyo|ja_JP.UTF-8] SKIPPED

=================== 6 passed, 24 skipped, 2 warnings ===================
```

**What just happened?**

1.  `pytest-tzshift` saw that `test_datetime_formatting` requested the `tzshift` fixture.
2.  It generated a list of `(timezone, locale)` pairs from its default lists.
3.  For each pair, the `tzshift` fixture:
    a. Set the `TZ` environment variable.
    b. Set the system locale via `locale.setlocale(locale.LC_ALL, ...)`.
    c. Yielded a `TzShift` object so your test could inspect the current settings.
    d. Cleaned up and restored the original environment after the test finished.
4.  If a specific locale wasn't available on the system (common in minimal CI containers), the plugin automatically skipped that test run with a helpful message, preventing spurious failures.

## Configuration

You'll almost certainly want to customize the timezones and locales for your project. You can do this globally in `pytest.ini` or for a single run via the command line.

### Using `pytest.ini`

This is the recommended way to set project-wide defaults. Create or edit your `pytest.ini` file:

```ini
# pytest.ini
[pytest]
tz_timezones =
    UTC
    America/Los_Angeles
    Asia/Tokyo

tz_locales =
    C
    en_US.UTF-8
    ja_JP.UTF-8
```

Now, `pytest-tzshift` will use these lists instead of its built-in defaults. The plugin validates these values, warning you if a timezone is unknown or a locale is unavailable on the test runner.

### Using Command-Line Flags

To override the `ini` settings for a specific run, use the command-line flags. Values should be comma-separated.

```bash
pytest --tz-timezones="UTC,Europe/Berlin" --tz-locales="C"
```

## Fine-Grained Control with Markers

Sometimes you need to change the behavior for a single test or class. The `@pytest.mark.tzshift` marker gives you that power.

```python
import pytest

# This test will use the global settings from pytest.ini
def test_with_global_config(tzshift):
    ...

# This test will ONLY run with the specified timezones and the global locales
@pytest.mark.tzshift(timezones=["UTC", "Europe/Moscow"])
def test_specific_timezones(tzshift):
    assert tzshift.timezone in ("UTC", "Europe/Moscow")

# This test will use the global timezones but only the 'C' locale
@pytest.mark.tzshift(locales=["C"])
def test_specific_locale(tzshift):
    assert tzshift.locale == "C"

# If a test is incompatible with tzshift, you can disable it entirely
@pytest.mark.tzshift(disable=True)
def test_something_unrelated(tzshift):
    # This test will run only once, and the tzshift fixture
    # will not modify the environment.
    ...
```

## Special Values: The "SYSTEM" Sentinel

What if you want to include a baseline run using the test runner's actual system environment? `pytest-tzshift` provides a special `"SYSTEM"` sentinel for this. It's case-insensitive, so `system` or `System` work too.

When `"SYSTEM"` is used, the plugin will not modify the corresponding environment setting for that run.

```ini
# pytest.ini
[pytest]
tz_timezones =
    SYSTEM  # Run once with the machine's original TZ
    UTC
    America/New_York

tz_locales =
    SYSTEM  # Run once with the machine's original locale
    en_US.UTF-8
```

The test ID for these runs will use `sys` for brevity: `...[0|sys|sys]`.

## Limiting Combinations

The Cartesian product of timezones and locales can create a huge number of tests. To keep CI times reasonable, you can cap the total number of combinations with `--tzshift-max` or the corresponding `ini` option.

**Via Command Line:**

```bash
# Only run the first 10 combinations
pytest --tzshift-max=10
```

**Via `pytest.ini`:**

```ini
# pytest.ini
[pytest]
tzshift_max = 20
```

The plugin will issue a warning when it truncates the test list, so you're always aware that it's happening.

Happy testing!