"""Virtual environment creation and management."""

import os
import subprocess
import sys
import venv


VENV_DIR = ".venv"


def get_venv_path(project_dir: str) -> str:
    return os.path.join(project_dir, VENV_DIR)


def venv_exists(project_dir: str) -> bool:
    venv_path = get_venv_path(project_dir)
    if sys.platform == "win32":
        return os.path.isfile(os.path.join(venv_path, "Scripts", "python.exe"))
    return os.path.isfile(os.path.join(venv_path, "bin", "python"))


def create_venv(project_dir: str) -> str:
    """Create a .venv in the project directory. Returns the venv path."""
    venv_path = get_venv_path(project_dir)
    if venv_exists(project_dir):
        return venv_path
    venv.create(venv_path, with_pip=True, clear=False)
    return venv_path


def get_python_executable(project_dir: str) -> str:
    venv_path = get_venv_path(project_dir)
    if sys.platform == "win32":
        return os.path.join(venv_path, "Scripts", "python.exe")
    return os.path.join(venv_path, "bin", "python")


def get_pip_executable(project_dir: str) -> str:
    venv_path = get_venv_path(project_dir)
    if sys.platform == "win32":
        return os.path.join(venv_path, "Scripts", "pip.exe")
    return os.path.join(venv_path, "bin", "pip")


def run_pip(project_dir: str, args: list, capture: bool = False) -> subprocess.CompletedProcess:
    """Run pip inside the project's venv."""
    pip_exe = get_pip_executable(project_dir)
    cmd = [pip_exe] + args
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
    return subprocess.run(cmd, cwd=project_dir)


def ensure_venv(project_dir: str) -> None:
    """Ensure venv exists, create if not."""
    if not venv_exists(project_dir):
        create_venv(project_dir)
