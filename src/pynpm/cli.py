"""CLI entry point — all user-facing commands."""

import os

import click

from pynpm import __version__, core, config, venv_manager


@click.group()
@click.version_option(__version__, prog_name="pynpm")
def main():
    """pynpm — An npm-like package manager for Python."""
    pass


# ─── init ────────────────────────────────────────────────────────────

@main.command()
@click.option("--name", default=None)
@click.option("--version", default=None)
@click.option("--description", default=None)
@click.option("--author", default=None)
@click.option("--license", "license_", default=None)
@click.option("--python", "python_version", default=None)
@click.option("-y", "yes", is_flag=True, help="Accept all defaults")
def init(name, version, description, author, license_, python_version, yes):
    """Initialize a new project (creates package.yml and .venv)."""
    project_dir = os.getcwd()

    if config.package_yml_exists(project_dir):
        click.secho("package.yml already exists.", fg="yellow")
        if not click.confirm("Overwrite?", default=False):
            return

    default_name = os.path.basename(project_dir)

    if yes:
        name = name or default_name
        version = version or "1.0.0"
        description = description or ""
        author = author or ""
        license_ = license_ or "MIT"
        python_version = python_version or ">=3.8"
    else:
        name = name or click.prompt("Project name", default=default_name)
        version = version or click.prompt("Version", default="1.0.0")
        description = description or click.prompt("Description", default="")
        author = author or click.prompt("Author", default="")
        license_ = license_ or click.prompt("License", default="MIT")
        python_version = python_version or click.prompt("Python version", default=">=3.8")

    core.init_project(project_dir, name, version, description, author, license_, python_version)
    click.secho(f"\nProject '{name}' initialized successfully!", fg="green", bold=True)


# ─── install ─────────────────────────────────────────────────────────

@main.command()
@click.argument("packages", nargs=-1)
@click.option("-D", "--save-dev", is_flag=True, help="Save as dev dependency")
def install(packages, save_dev):
    """Install packages. With no args, installs all from package.yml."""
    project_dir = os.getcwd()

    if not packages:
        # Install all deps from package.yml (like `npm install`)
        core.install_all(project_dir)
        return

    for pkg in packages:
        core.install_package(project_dir, pkg, dev=save_dev)


# ─── uninstall ───────────────────────────────────────────────────────

@main.command()
@click.argument("packages", nargs=-1, required=True)
def uninstall(packages):
    """Uninstall packages and remove from package.yml."""
    project_dir = os.getcwd()

    if not config.package_yml_exists(project_dir):
        click.secho("No package.yml found. Run 'pynpm init' first.", fg="red")
        return

    for pkg in packages:
        core.uninstall_package(project_dir, pkg)


# ─── list ────────────────────────────────────────────────────────────

@main.command(name="list")
def list_cmd():
    """List project dependencies and their status."""
    project_dir = os.getcwd()
    core.list_packages(project_dir)


# ─── run ─────────────────────────────────────────────────────────────

@main.command()
@click.argument("script_name")
def run(script_name):
    """Run a script defined in package.yml."""
    project_dir = os.getcwd()

    if not config.package_yml_exists(project_dir):
        click.secho("No package.yml found. Run 'pynpm init' first.", fg="red")
        raise SystemExit(1)

    venv_manager.ensure_venv(project_dir)
    exit_code = core.run_script(project_dir, script_name)
    raise SystemExit(exit_code)


# ─── activate ────────────────────────────────────────────────────────

@main.command()
def activate():
    """Detect host platform and activate the .venv."""
    import platform

    project_dir = os.getcwd()

    if not venv_manager.venv_exists(project_dir):
        click.secho("No .venv found. Run 'pynpm init' first.", fg="red")
        raise SystemExit(1)

    host_os = platform.system()
    click.echo(f"Detected platform: {host_os}")

    venv_manager.activate_venv(project_dir)
    click.secho("Activated .venv for child processes.", fg="green")

    activate_cmd = venv_manager.get_activate_command(project_dir)
    click.echo(f"\nTo activate in your current shell, run:")
    click.secho(f"  {activate_cmd}", fg="cyan")


# ─── shorthand aliases ──────────────────────────────────────────────

@main.command(name="i")
@click.argument("packages", nargs=-1)
@click.option("-D", "--save-dev", is_flag=True, help="Save as dev dependency")
def install_alias(packages, save_dev):
    """Alias for 'install'."""
    project_dir = os.getcwd()
    if not packages:
        core.install_all(project_dir)
        return
    for pkg in packages:
        core.install_package(project_dir, pkg, dev=save_dev)


@main.command(name="rm")
@click.argument("packages", nargs=-1, required=True)
def uninstall_alias(packages):
    """Alias for 'uninstall'."""
    project_dir = os.getcwd()
    if not config.package_yml_exists(project_dir):
        click.secho("No package.yml found.", fg="red")
        return
    for pkg in packages:
        core.uninstall_package(project_dir, pkg)


if __name__ == "__main__":
    main()
