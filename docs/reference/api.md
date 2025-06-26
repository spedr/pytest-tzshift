# API Reference

This page provides a detailed reference for the public API of `pytest-tzshift`, including the main fixture, data objects, constants, and the underlying Pytest hooks that power the plugin.

This documentation is generated directly from the source code's docstrings.

## Fixture

The primary way to interact with this plugin is through the `tzshift` fixture.

### `tzshift`

Requesting the `tzshift` fixture in a test function is what triggers the timezone and locale parametrization for that test. The fixture is responsible for setting up the environment before your test runs and safely tearing it down afterward.

During the test run, it yields a `TzShift` object, giving you read-only access to the active settings.

::: pytest_tzshift.plugin.tzshift

#### Example

```python
from pytest_tzshift import TzShift
import time
import locale

def test_time_and_locale_behavior(tzshift: TzShift):
    """
    A test that uses the tzshift fixture.

    This test will be run for each combination of configured
    timezones and locales.
    """
    # The `tzshift` object provides the active settings for this run.
    print(f"Active Timezone: {tzshift.timezone}")
    print(f"Active Locale:   {tzshift.locale}")

    # The environment reflects these settings.
    # Note: time.tzname will reflect the active timezone.
    print(f"time.tzname: {time.tzname}")

    # Note: locale.getlocale() will reflect the active locale.
    print(f"locale.getlocale(locale.LC_ALL): {locale.getlocale(locale.LC_ALL)}")

    # Your test logic here...
    assert True
```

## Data Objects

The plugin uses a simple data object to pass information to your tests.

### `TzShift`

This object is yielded by the `tzshift` fixture.

::: pytest_tzshift._types.TzShift

#### Example

```python
from pytest_tzshift import TzShift

def test_unpacking(tzshift: TzShift):
    # Unpack like a tuple
    tz, loc = tzshift

    assert tz == tzshift.timezone
    assert loc == tzshift.locale

    # Access by index
    assert tzshift[0] == tzshift.timezone
    assert tzshift[1] == tzshift.locale

    # Get length
    assert len(tzshift) == 2

    # Explicitly convert to a tuple
    assert tzshift.as_tuple() == (tz, loc)
```

## Constants

The plugin exposes sentinel values that have special meaning in configuration.

### `SYSTEM_TZ`

::: pytest_tzshift.plugin.SYSTEM_TZ
A sentinel string used in timezone lists to indicate that the original system timezone should be used as one of the parameterization values.

### `SYSTEM_LOCALE`

::: pytest_tzshift.plugin.SYSTEM_LOCALE
A sentinel string used in locale lists to indicate that the original system locale should be used as one of the parameterization values.

## Pytest Hooks

For advanced users and contributors, `pytest-tzshift` implements the following standard Pytest hooks. You do not need to interact with these directly to use the plugin, but they are documented here for completeness. The user-facing results of these hooks are the command-line options, `pytest.ini` settings, and the `@pytest.mark.tzshift` marker.

### `pytest_generate_tests`

This is the core engine of the plugin, responsible for creating the parametrized test runs.

::: pytest_tzshift.plugin.pytest_generate_tests

### `pytest_addoption`

This hook adds the command-line and `pytest.ini` configuration options. For details on using these options, see the [Configuration](./../usage/configuration.md) guide.

::: pytest_tzshift.plugin.pytest_addoption

### `pytest_configure`

This hook registers the `tzshift` marker, allowing for per-test or per-scope overrides.

::: pytest_tzshift.plugin.pytest_configure