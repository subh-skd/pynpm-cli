# pynpm — An npm-like Package Manager for Python

**pynpm** is a Python package manager inspired by npm. It uses `pip` under the hood but gives you clean dependency management with `package.yml` and `package-lock.yml`, automatic virtual environment handling, and no unnecessary transitive dependencies polluting your project.

## Features

- **`pynpm init`** — Initialize a project with `package.yml` and `.venv` (like `npm init`)
- **`pynpm install <pkg>`** — Install a package and save it to `package.yml` (like `npm install`)
- **`pynpm install`** — Install all dependencies from `package.yml` / lockfile (like `npm install`)
- **`pynpm uninstall <pkg>`** — Remove a package and clean up orphaned transitive deps
- **`pynpm list`** — Show project dependencies and their installed versions
- **`pynpm run <script>`** — Run scripts defined in `package.yml` (like `npm run`)
- **Automatic `.venv`** — Creates and uses a virtual environment automatically
- **Lockfile** — `package-lock.yml` locks exact versions for reproducible installs
- **Orphan cleanup** — Uninstalling a package also removes its unused transitive dependencies

## Installation

```bash
pip install pynpm-cli
```

## Quick Start

```bash
# Create a new project
mkdir my-project && cd my-project
pynpm init

# Install packages
pynpm install requests
pynpm install flask

# Install dev dependencies
pynpm install -D pytest

# Install all deps from package.yml (like npm install)
pynpm install

# Run a script
pynpm run test

# Remove a package
pynpm uninstall flask

# List dependencies
pynpm list
```

## package.yml

Your project configuration lives in `package.yml`:

```yaml
name: my-project
version: 1.0.0
description: My awesome project
author: Your Name
license: MIT
python: ">=3.8"

scripts:
  start: python main.py
  test: pytest

dependencies:
  requests: "==2.31.0"
  flask: "==3.0.0"

dev_dependencies:
  pytest: "==8.0.0"
```

## package-lock.yml

The lockfile captures the exact versions of **all** installed packages (including transitive dependencies) for reproducible installs:

```yaml
lockfile_version: 1
packages:
  requests:
    version: "2.31.0"
  urllib3:
    version: "2.1.0"
  charset-normalizer:
    version: "3.3.2"
```

## Command Aliases

| Full Command | Alias |
|---|---|
| `pynpm install` | `pynpm i` |
| `pynpm uninstall` | `pynpm rm` |

## How It Works

1. **`pynpm init`** creates `package.yml`, `.venv`, and `.gitignore`
2. **`pynpm install <pkg>`** installs into `.venv` via pip, records the direct dependency in `package.yml`, and snapshots all installed versions into `package-lock.yml`
3. **`pynpm uninstall <pkg>`** removes the package, cleans up orphaned transitive deps, and updates both config files
4. **`pynpm install`** (no args) reads `package-lock.yml` for exact versions, or falls back to `package.yml` version specs

## Publishing to PyPI

This project uses GitHub Actions with PyPI trusted publishing. To publish:

1. Configure trusted publishing on PyPI for your repository
2. Create a GitHub release — the workflow builds and publishes automatically

## License

MIT
