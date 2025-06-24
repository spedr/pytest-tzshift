Here's a concise, informative, and friendly `quickstart.md` page to get users up and running quickly:

---

# Quickstart Guide

Welcome! **pytest-tzshift** is a simple yet powerful Pytest plugin that transparently reruns your tests under multiple combinations of timezones and locales. This helps you discover timezone- or locale-dependent bugs early.

This guide will help you set up the plugin and start using it right away.

## Installation

Install via `pip`:

```shell
pip install pytest-tzshift
```

Make sure your Python environment is version **3.9 or newer** (required by the built-in `zoneinfo` library).

## Usage

Once installed, simply request the `tzshift` fixture in your tests, and pytest-tzshift will automatically run them multiple times with different timezone and locale combinations.

Here's a simple example:

```python
def test_localized_datetime(tzshift):
    timezone, locale = tzshift

    # Your test code here, e.g., using datetime or locale
    from datetime import datetime
    now = datetime.now().strftime("%c")
    print(f"Running with TZ={timezone}, locale={locale}, datetime={now}")

    # Add your assertions here
```

When you run Pytest, your test will run multiple times:

```shell
pytest test_example.py
```

You will see output similar to:

```
test_example.py::test_localized_datetime[0|UTC|C] PASSED
test_example.py::test_localized_datetime[1|UTC|en_US.UTF-8] PASSED
test_example.py::test_localized_datetime[2|America/New_York|C] PASSED
test_example.py::test_localized_datetime[3|America/New_York|en_US.UTF-8] PASSED
...
```

## Customizing timezone and locale combinations

You can specify your preferred timezone and locale combinations either globally or per-test.

### Global configuration (`pytest.ini`)

Add your desired timezones and locales to your project's `pytest.ini` or `pyproject.toml`:

```ini
[pytest]
tz_timezones =
    UTC
    America/Los_Angeles
tz_locales =
    C
    en_US.UTF-8
    es_ES.UTF-8
```

### Command-line overrides

You can quickly override your config via command-line flags:

```shell
pytest --tz-timezones=Asia/Tokyo,UTC --tz-locales=ja_JP.UTF-8,C
```

### Per-test markers

To limit or disable timezone/locale shifting for specific tests or modules, use the `tzshift` marker:

```python
import pytest

@pytest.mark.tzshift(timezones=["UTC"], locales=["C"])
def test_limited(tzshift):
    # Runs only once with UTC/C
    pass

@pytest.mark.tzshift(disable=True)
def test_no_tzshift():
    # No timezone/locale parametrization
    pass
```

## Understanding the fixture object (`TzShift`)

Inside tests, the provided `tzshift` fixture object can be unpacked into timezone and locale:

```python
def test_example(tzshift):
    tz, loc = tzshift
    # or use tzshift.timezone, tzshift.locale
```

The object is immutable and can be treated like a tuple.

## Limit number of combinations

If you have many combinations, you can cap the maximum number to test:

```shell
pytest --tzshift-max=10
```

Or via your configuration:

```ini
[pytest]
tzshift_max = 10
```

## Disabling completely

To completely disable pytest-tzshift for a test run:

```shell
pytest --no-tzshift
```

---

That's it! You’re now ready to thoroughly test your timezone- and locale-sensitive code easily and efficiently.

Next up: check out the [Configuration](configuration.md) section for a deeper dive.