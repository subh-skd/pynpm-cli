"""Tests for CLI commands."""

import os

from click.testing import CliRunner

from pynpm.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "pynpm" in result.output


def test_init_creates_files(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init", "-y"])
        assert result.exit_code == 0
        assert os.path.isfile("package.yml")
        assert os.path.isdir(".venv")


def test_init_interactive(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init"], input="myapp\n1.0.0\nA test app\nJohn\nMIT\n>=3.8\n")
        assert result.exit_code == 0
        assert os.path.isfile("package.yml")


def test_list_no_package_yml(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["list"])
        assert "No package.yml found" in result.output


def test_run_no_package_yml(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["run", "test"])
        assert result.exit_code != 0
