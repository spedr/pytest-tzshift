# Contributing

Thank you for your interest in improving **pytest-tzshift**!
This plugin started from a personal need to test a project over different locales and timezones. Developing cross-platform solutions that involve system-level tools can be tricky, and this is still an ongoing project. Your help is valuable.

Whether you're reporting a bug, suggesting a feature, improving documentation, or sending code, this guide is for you.

---

## How to contribute

### Open an Issue

If you've found a bug or have an idea, please [open an issue](https://github.com/spedr/pytest-tzshift/issues) on GitHub.
Describe:

* What you tried
* What you expected
* What actually happened
* Any relevant error messages, stack traces, or logs

Feel free to suggest enhancements, ask questions, or request new features!

---

### Fork & Clone

* Click "Fork" on GitHub.
* Clone your fork locally:

  ```shell
  git clone https://github.com/YOURUSERNAME/pytest-tzshift.git
  cd pytest-tzshift
  ```

---

### Set Up Your Environment

We recommend using [virtualenv](https://virtualenv.pypa.io/) or [venv](https://docs.python.org/3/library/venv.html):

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

This will install pytest-tzshift in "editable" mode, along with development dependencies.

---

### Make Changes

* Follow [PEP8](https://peps.python.org/pep-0008/) style and keep code readable.
* Add tests for new features or bugfixes.
* Update or add docstrings where needed.

**Tip:** Run the test suite:

```shell
pytest
```

---

### Run Checks

Before you push, run:

```shell
pytest               # all tests should pass
ruff src/ tests/     # style/linting
mypy src/            # type checks
```

---

### Send a Pull Request

Push your branch to your fork and open a pull request against the `main` branch.

* Summarize your changes and why they're needed.
* Reference any related issues.
* If it’s a work-in-progress, mark it as a draft PR.

---

## Coding Guidelines

* **Tests:** Place new tests under `tests/`
* **Docs:** Update Markdown docs in `docs/` as needed, especially for new features or config.
* **Commits:** Use clear, descriptive commit messages.

---

## Development Tips

* If testing locale or timezone edge cases, try different environments: Linux, macOS, and Windows.
* Not all locales are available on every OS! Document any platform-specific quirks.
* For large changes, discuss first by opening an issue or draft PR.

---

Thank you!