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


def get_activate_command(project_dir: str) -> str:
    """Return the platform-specific command to activate the venv."""
    venv_path = get_venv_path(project_dir)
    if sys.platform == "win32":
        # Detect shell: PowerShell vs cmd
        shell = os.environ.get("COMSPEC", "").lower()
        parent = os.environ.get("PSModulePath", "")
        if parent:
            # Likely PowerShell
            return os.path.join(venv_path, "Scripts", "Activate.ps1")
        return os.path.join(venv_path, "Scripts", "activate.bat")
    # Unix — detect fish / csh vs bash/zsh
    shell = os.environ.get("SHELL", "/bin/bash")
    if "fish" in shell:
        return f"source {os.path.join(venv_path, 'bin', 'activate.fish')}"
    if "csh" in shell:
        return f"source {os.path.join(venv_path, 'bin', 'activate.csh')}"
    return f"source {os.path.join(venv_path, 'bin', 'activate')}"


def activate_venv(project_dir: str) -> bool:
    """Attempt to activate the venv in the current process environment."""
    venv_path = get_venv_path(project_dir)
    if not venv_exists(project_dir):
        return False

    # Set environment variables so child processes use the venv
    if sys.platform == "win32":
        bin_dir = os.path.join(venv_path, "Scripts")
    else:
        bin_dir = os.path.join(venv_path, "bin")

    os.environ["VIRTUAL_ENV"] = venv_path
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    os.environ.pop("PYTHONHOME", None)
    return True
