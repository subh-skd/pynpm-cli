"""package.yml and package-lock.yml read/write handlers."""

import os
from typing import Any, Dict, List, Optional

import yaml


PACKAGE_FILE = "package.yml"
LOCK_FILE = "package-lock.yml"


def _read_yaml(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _write_yaml(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


# --------------- package.yml ---------------

def package_yml_exists(project_dir: str) -> bool:
    return os.path.isfile(os.path.join(project_dir, PACKAGE_FILE))


def read_package_yml(project_dir: str) -> Dict[str, Any]:
    return _read_yaml(os.path.join(project_dir, PACKAGE_FILE))


def write_package_yml(project_dir: str, data: Dict[str, Any]) -> None:
    _write_yaml(os.path.join(project_dir, PACKAGE_FILE), data)


def create_default_package_yml(
    project_dir: str,
    name: str,
    version: str = "1.0.0",
    description: str = "",
    author: str = "",
    license_: str = "MIT",
    python_version: str = ">=3.8",
) -> Dict[str, Any]:
    data = {
        "name": name,
        "version": version,
        "description": description,
        "author": author,
        "license": license_,
        "python": python_version,
        "scripts": {
            "start": "python main.py",
            "test": "pytest",
        },
        "dependencies": {},
        "dev_dependencies": {},
    }
    write_package_yml(project_dir, data)
    return data


def add_dependency(project_dir: str, name: str, version: str, dev: bool = False) -> None:
    data = read_package_yml(project_dir)
    key = "dev_dependencies" if dev else "dependencies"
    if key not in data:
        data[key] = {}
    data[key][name] = version
    write_package_yml(project_dir, data)


def remove_dependency(project_dir: str, name: str) -> bool:
    data = read_package_yml(project_dir)
    removed = False
    for key in ("dependencies", "dev_dependencies"):
        if key in data and name in data[key]:
            del data[key][name]
            removed = True
    if removed:
        write_package_yml(project_dir, data)
    return removed


def get_all_dependencies(project_dir: str) -> Dict[str, str]:
    """Return merged dict of dependencies + dev_dependencies."""
    data = read_package_yml(project_dir)
    deps = {}
    deps.update(data.get("dependencies", {}))
    deps.update(data.get("dev_dependencies", {}))
    return deps


# --------------- package-lock.yml ---------------

def read_lock(project_dir: str) -> Dict[str, Any]:
    return _read_yaml(os.path.join(project_dir, LOCK_FILE))


def write_lock(project_dir: str, data: Dict[str, Any]) -> None:
    _write_yaml(os.path.join(project_dir, LOCK_FILE), data)


def update_lock(project_dir: str, installed_packages: List[Dict[str, str]]) -> None:
    """Write the full resolved dependency tree to the lockfile."""
    lock_data = {
        "lockfile_version": 1,
        "packages": {},
    }
    for pkg in installed_packages:
        lock_data["packages"][pkg["name"]] = {
            "version": pkg["version"],
        }
    write_lock(project_dir, lock_data)
