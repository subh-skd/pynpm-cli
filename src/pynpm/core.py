"""Core package management logic — install, uninstall, freeze, resolve."""

import json
import re
from typing import Dict, List, Optional, Tuple

import click

from pynpm import venv_manager, config


def _parse_pip_json_list(project_dir: str) -> List[Dict[str, str]]:
    """Get list of installed packages from pip as [{name, version}, ...]."""
    result = venv_manager.run_pip(project_dir, ["list", "--format=json"], capture=True)
    if result.returncode != 0:
        return []
    try:
        packages = json.loads(result.stdout)
        return [{"name": p["name"].lower(), "version": p["version"]} for p in packages]
    except (json.JSONDecodeError, KeyError):
        return []


def _get_installed_version(project_dir: str, package_name: str) -> Optional[str]:
    result = venv_manager.run_pip(project_dir, ["show", package_name], capture=True)
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    return None


def _parse_package_spec(spec: str) -> Tuple[str, Optional[str]]:
    """Parse 'package==1.0' or 'package>=1.0' or 'package' into (name, version_spec)."""
    for sep in ("==", ">=", "<=", "!=", "~=", ">", "<"):
        if sep in spec:
            name, ver = spec.split(sep, 1)
            return name.strip(), f"{sep}{ver.strip()}"
    return spec.strip(), None


def init_project(project_dir: str, name: str, version: str, description: str, author: str, license_: str, python_version: str) -> None:
    """Initialize a new project with package.yml and .venv."""
    config.create_default_package_yml(
        project_dir,
        name=name,
        version=version,
        description=description,
        author=author,
        license_=license_,
        python_version=python_version,
    )
    click.echo("Created package.yml")
    venv_manager.create_venv(project_dir)
    click.echo("Created .venv virtual environment")

    # Write .gitignore if it doesn't exist
    import os
    gitignore_path = os.path.join(project_dir, ".gitignore")
    if not os.path.isfile(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write(".venv/\n__pycache__/\n*.pyc\n*.egg-info/\ndist/\nbuild/\n")
        click.echo("Created .gitignore")


def install_package(project_dir: str, package_spec: str, dev: bool = False, save: bool = True) -> bool:
    """Install a single package into the venv and record it in package.yml."""
    venv_manager.ensure_venv(project_dir)

    name, version_spec = _parse_package_spec(package_spec)
    pip_spec = f"{name}{version_spec}" if version_spec else name

    click.echo(f"Installing {pip_spec}...")
    result = venv_manager.run_pip(project_dir, ["install", pip_spec])
    if result.returncode != 0:
        click.secho(f"Failed to install {pip_spec}", fg="red")
        return False

    # Get actual installed version
    installed_ver = _get_installed_version(project_dir, name)
    if not installed_ver:
        installed_ver = "latest"

    if save:
        version_str = version_spec if version_spec else f"=={installed_ver}"
        config.add_dependency(project_dir, name, version_str, dev=dev)
        click.secho(f"+ {name}@{installed_ver}", fg="green")

    _regenerate_lockfile(project_dir)
    return True


def install_all(project_dir: str) -> bool:
    """Install all dependencies from package.yml (like `npm install` with no args)."""
    if not config.package_yml_exists(project_dir):
        click.secho("No package.yml found. Run 'pynpm init' first.", fg="red")
        return False

    venv_manager.ensure_venv(project_dir)

    deps = config.get_all_dependencies(project_dir)
    if not deps:
        click.echo("No dependencies to install.")
        return True

    # Check if lockfile exists — if so, install exact versions from lock
    lock = config.read_lock(project_dir)
    if lock.get("packages"):
        click.echo("Installing from package-lock.yml...")
        specs = [f"{name}=={info['version']}" for name, info in lock["packages"].items()]
    else:
        click.echo("Installing from package.yml...")
        specs = [f"{name}{ver}" for name, ver in deps.items()]

    result = venv_manager.run_pip(project_dir, ["install"] + specs)
    if result.returncode != 0:
        click.secho("Some packages failed to install.", fg="red")
        return False

    _regenerate_lockfile(project_dir)
    click.secho("All dependencies installed.", fg="green")
    return True


def uninstall_package(project_dir: str, package_name: str) -> bool:
    """Uninstall a package and remove it from package.yml."""
    venv_manager.ensure_venv(project_dir)

    click.echo(f"Uninstalling {package_name}...")
    result = venv_manager.run_pip(project_dir, ["uninstall", "-y", package_name])
    if result.returncode != 0:
        click.secho(f"Failed to uninstall {package_name}", fg="red")
        return False

    removed = config.remove_dependency(project_dir, package_name)
    if removed:
        click.secho(f"- {package_name}", fg="red")
    else:
        click.echo(f"{package_name} was not in package.yml")

    # Clean up unused transitive deps
    _cleanup_orphans(project_dir)
    _regenerate_lockfile(project_dir)
    return True


def list_packages(project_dir: str) -> None:
    """Display installed packages."""
    if not config.package_yml_exists(project_dir):
        click.secho("No package.yml found.", fg="red")
        return

    data = config.read_package_yml(project_dir)
    deps = data.get("dependencies", {})
    dev_deps = data.get("dev_dependencies", {})

    if deps:
        click.secho("dependencies:", fg="cyan")
        for name, ver in deps.items():
            installed = _get_installed_version(project_dir, name)
            status = f" (installed: {installed})" if installed else " (not installed)"
            click.echo(f"  {name}: {ver}{status}")

    if dev_deps:
        click.secho("dev_dependencies:", fg="cyan")
        for name, ver in dev_deps.items():
            installed = _get_installed_version(project_dir, name)
            status = f" (installed: {installed})" if installed else " (not installed)"
            click.echo(f"  {name}: {ver}{status}")

    if not deps and not dev_deps:
        click.echo("No dependencies listed.")


def run_script(project_dir: str, script_name: str) -> int:
    """Run a script defined in package.yml."""
    import os
    import subprocess

    data = config.read_package_yml(project_dir)
    scripts = data.get("scripts", {})

    if script_name not in scripts:
        click.secho(f"Script '{script_name}' not found in package.yml", fg="red")
        available = ", ".join(scripts.keys()) if scripts else "none"
        click.echo(f"Available scripts: {available}")
        return 1

    command = scripts[script_name]
    click.echo(f"> {command}")

    # Build env with venv activated
    env = os.environ.copy()
    venv_path = venv_manager.get_venv_path(project_dir)
    if os.sys.platform == "win32":
        env["PATH"] = os.path.join(venv_path, "Scripts") + os.pathsep + env.get("PATH", "")
    else:
        env["PATH"] = os.path.join(venv_path, "bin") + os.pathsep + env.get("PATH", "")
    env["VIRTUAL_ENV"] = venv_path

    result = subprocess.run(command, shell=True, cwd=project_dir, env=env)
    return result.returncode


def _regenerate_lockfile(project_dir: str) -> None:
    """Snapshot all installed packages into package-lock.yml."""
    packages = _parse_pip_json_list(project_dir)
    # Filter out pip, setuptools, wheel (internal tools)
    skip = {"pip", "setuptools", "wheel"}
    packages = [p for p in packages if p["name"] not in skip]
    config.update_lock(project_dir, packages)


def _cleanup_orphans(project_dir: str) -> None:
    """Remove packages that are not direct deps and not required by any direct dep."""
    deps = config.get_all_dependencies(project_dir)
    if not deps:
        return

    direct_names = {name.lower() for name in deps}

    # Get full dependency tree for each direct dep
    required = set()
    for name in direct_names:
        required.add(name)
        _collect_requires(project_dir, name, required)

    # Get all installed
    installed = _parse_pip_json_list(project_dir)
    skip = {"pip", "setuptools", "wheel"}

    orphans = []
    for pkg in installed:
        if pkg["name"] in skip:
            continue
        if pkg["name"] not in required:
            orphans.append(pkg["name"])

    if orphans:
        click.echo(f"Removing orphaned packages: {', '.join(orphans)}")
        venv_manager.run_pip(project_dir, ["uninstall", "-y"] + orphans)


def _collect_requires(project_dir: str, package_name: str, collected: set) -> None:
    """Recursively collect all requirements of a package."""
    result = venv_manager.run_pip(project_dir, ["show", package_name], capture=True)
    if result.returncode != 0:
        return
    for line in result.stdout.splitlines():
        if line.startswith("Requires:"):
            req_str = line.split(":", 1)[1].strip()
            if not req_str:
                return
            for req in req_str.split(","):
                req_name = req.strip().lower()
                if req_name and req_name not in collected:
                    collected.add(req_name)
                    _collect_requires(project_dir, req_name, collected)
            return
