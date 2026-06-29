---
layout: default
title: twat-labs
---

# twat-labs

**`twat-labs`** is an experimental sandbox plugin for the [twat](https://pypi.org/project/twat/) ecosystem.

It acts as a proving ground for new features, utilities, and integrations under development before potential inclusion in the core `twat` package or other specialised `twat-*` plugins.

## Installation

```bash
pip install twat-labs
```

## Role in the twat ecosystem

`twat-labs` registers itself as a plugin under the `twat.plugins` entry-point group with the key `labs`. When `twat` loads its plugin registry it discovers this package and surfaces its commands alongside those of other plugins.

## Command-line interface

`twat-labs` ships a [Fire](https://github.com/google/python-fire)-based CLI with three built-in commands:

```
twat-labs version       # print the installed version
twat-labs info          # show package name, version, and description
twat-labs experiments   # list any experiment modules found in the package
```

Individual entry-point shortcuts are also installed:

| Script | Equivalent |
|---|---|
| `twat-labs-version` | `twat-labs version` |
| `twat-labs-info` | `twat-labs info` |
| `twat-labs-experiments` | `twat-labs experiments` |

## Python API

```python
import twat_labs

print(twat_labs.__version__)   # e.g. "2.7.9"
twat_labs.main()               # invoke the CLI dispatcher programmatically
```

## Adding experiments

Drop a `.py` module under `src/twat_labs/` — it will appear in the output of
`twat-labs experiments` automatically (any public module whose name does not
start with `_`).

## Development

```bash
# Run tests
pytest tests/

# Lint + format
ruff check src/ tests/
ruff format src/ tests/

# Type-check
mypy src/twat_labs tests/
```

## Links

- [PyPI](https://pypi.org/project/twat-labs/)
- [Source](https://github.com/twardoch/twat-labs)
- [Issues](https://github.com/twardoch/twat-labs/issues)
- [twat ecosystem](https://pypi.org/project/twat/)
