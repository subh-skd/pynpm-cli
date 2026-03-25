"""Tests for package.yml and lockfile config handling."""

import os
import tempfile

import pytest

from pynpm import config


@pytest.fixture
def tmp_project(tmp_path):
    return str(tmp_path)


class TestPackageYml:
    def test_create_default(self, tmp_project):
        data = config.create_default_package_yml(tmp_project, name="test-proj")
        assert data["name"] == "test-proj"
        assert data["version"] == "1.0.0"
        assert os.path.isfile(os.path.join(tmp_project, "package.yml"))

    def test_read_write_roundtrip(self, tmp_project):
        original = {"name": "myapp", "version": "2.0.0", "dependencies": {"requests": "==2.31.0"}}
        config.write_package_yml(tmp_project, original)
        loaded = config.read_package_yml(tmp_project)
        assert loaded["name"] == "myapp"
        assert loaded["dependencies"]["requests"] == "==2.31.0"

    def test_add_dependency(self, tmp_project):
        config.create_default_package_yml(tmp_project, name="test")
        config.add_dependency(tmp_project, "flask", "==3.0.0")
        data = config.read_package_yml(tmp_project)
        assert data["dependencies"]["flask"] == "==3.0.0"

    def test_add_dev_dependency(self, tmp_project):
        config.create_default_package_yml(tmp_project, name="test")
        config.add_dependency(tmp_project, "pytest", "==8.0.0", dev=True)
        data = config.read_package_yml(tmp_project)
        assert data["dev_dependencies"]["pytest"] == "==8.0.0"

    def test_remove_dependency(self, tmp_project):
        config.create_default_package_yml(tmp_project, name="test")
        config.add_dependency(tmp_project, "flask", "==3.0.0")
        removed = config.remove_dependency(tmp_project, "flask")
        assert removed is True
        data = config.read_package_yml(tmp_project)
        assert "flask" not in data["dependencies"]

    def test_remove_nonexistent(self, tmp_project):
        config.create_default_package_yml(tmp_project, name="test")
        removed = config.remove_dependency(tmp_project, "nonexistent")
        assert removed is False

    def test_get_all_dependencies(self, tmp_project):
        config.create_default_package_yml(tmp_project, name="test")
        config.add_dependency(tmp_project, "flask", "==3.0.0")
        config.add_dependency(tmp_project, "pytest", "==8.0.0", dev=True)
        all_deps = config.get_all_dependencies(tmp_project)
        assert "flask" in all_deps
        assert "pytest" in all_deps


class TestLockfile:
    def test_update_lock(self, tmp_project):
        packages = [
            {"name": "flask", "version": "3.0.0"},
            {"name": "jinja2", "version": "3.1.2"},
        ]
        config.update_lock(tmp_project, packages)
        lock = config.read_lock(tmp_project)
        assert lock["lockfile_version"] == 1
        assert lock["packages"]["flask"]["version"] == "3.0.0"
        assert lock["packages"]["jinja2"]["version"] == "3.1.2"

    def test_empty_lock(self, tmp_project):
        lock = config.read_lock(tmp_project)
        assert lock == {}
