"""
Regression tests for common.paths.

These lock in the fix for a bug that silently stranded an entire generated vault
inside the repository: three call sites hardcoded a machine-specific absolute
path as a fallback, in a form that did not parse on the platform actually
running the code. The tests below cover both directions of that failure.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.paths import (  # noqa: E402
    PathConfigError, resolve_path, resolve_vault_path, resolve_wiki_path)

ENV = "TEST_VAULT_PATH_ENVVAR"


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv(ENV, raising=False)
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.delenv("OBSIDIAN_WIKI_PATH", raising=False)


# --- no silent defaults -----------------------------------------------------

def test_required_and_unconfigured_raises():
    """The original bug was a silent fallback. Absence must be an error."""
    with pytest.raises(PathConfigError) as exc:
        resolve_path(None, ENV, label="vault path")
    assert "No vault path configured" in str(exc.value)
    assert ENV in str(exc.value)


def test_optional_and_unconfigured_returns_none():
    assert resolve_path(None, ENV, required=False) is None


def test_blank_and_whitespace_are_treated_as_unconfigured(monkeypatch):
    monkeypatch.setenv(ENV, "   ")
    with pytest.raises(PathConfigError):
        resolve_path(None, ENV)
    assert resolve_path("  ", ENV, required=False) is None


# --- the platform-mismatch guard -------------------------------------------

def _simulate_posix(monkeypatch, cwd="/home/nickd/dnaf"):
    """
    Make os.path behave as it does under POSIX/WSL, which is where the original
    bug fired. The guard is deliberately platform-dependent: on Windows,
    basename() splits on '\\' and extracts a clean leaf, so there is nothing to
    catch. Only a POSIX interpreter leaves a Windows path as one component.
    """
    import posixpath
    monkeypatch.setattr(os.path, "abspath",
                        lambda p: p if p.startswith("/") else posixpath.join(cwd, p))
    monkeypatch.setattr(os.path, "basename", posixpath.basename)
    monkeypatch.setattr(os.path, "dirname", posixpath.dirname)


def test_unparsed_path_is_rejected(monkeypatch):
    """
    The exact historical failure: under POSIX a Windows path is not a path, so
    the whole string survives as one component and makedirs would create a
    single directory literally named 'C:\\Users\\...\\Hermes'.
    """
    _simulate_posix(monkeypatch)

    with pytest.raises(PathConfigError) as exc:
        resolve_path("C:\\Users\\nickd\\Desktop\\Hermes", ENV, label="vault path")

    msg = str(exc.value)
    assert "does not parse as a path on this platform" in msg
    # The message must show what the leaf became, so the cause is obvious.
    assert "C:\\\\Users\\\\nickd\\\\Desktop\\\\Hermes" in msg or \
           "C:\\Users\\nickd\\Desktop\\Hermes" in msg


def test_unparsed_path_is_rejected_before_any_directory_is_created(monkeypatch, tmp_path):
    """The guard must fire before makedirs, even with create=True."""
    _simulate_posix(monkeypatch, cwd=str(tmp_path).replace("\\", "/"))

    with pytest.raises(PathConfigError):
        resolve_path("C:\\Users\\nickd\\Vault", ENV, create=True)

    assert os.listdir(tmp_path) == [], "nothing may be created for an unparsed path"


def test_wrong_platform_path_fails_via_missing_parent(tmp_path):
    """The reverse case: a WSL path on Windows resolves but does not exist."""
    with pytest.raises(PathConfigError) as exc:
        resolve_path("/mnt/c/Users/nickd/Desktop/DefinitelyNotHere", ENV)
    assert "does not exist" in str(exc.value)


# --- existence and creation -------------------------------------------------

def test_missing_directory_raises_when_must_exist(tmp_path):
    target = tmp_path / "no_such_vault"
    with pytest.raises(PathConfigError) as exc:
        resolve_path(str(target), ENV)
    assert "does not exist" in str(exc.value)


def test_missing_directory_tolerated_when_not_must_exist(tmp_path):
    target = tmp_path / "no_such_vault"
    assert resolve_path(str(target), ENV, must_exist=False) == str(target)
    assert not target.exists(), "must_exist=False must not create anything"


def test_create_makes_the_directory(tmp_path):
    target = tmp_path / "new_vault"
    assert resolve_path(str(target), ENV, create=True) == str(target)
    assert target.is_dir()


def test_create_refuses_when_parent_is_missing(tmp_path):
    """Never build a deep tree at an unexpected location from a typo."""
    target = tmp_path / "a" / "b" / "c"
    with pytest.raises(PathConfigError) as exc:
        resolve_path(str(target), ENV, create=True)
    assert "parent directory does not exist" in str(exc.value)
    assert not (tmp_path / "a").exists()


def test_existing_directory_resolves(tmp_path):
    assert resolve_path(str(tmp_path), ENV) == str(tmp_path)


# --- configuration precedence ----------------------------------------------

def test_env_var_is_used_when_no_explicit_value(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(tmp_path))
    assert resolve_path(None, ENV) == str(tmp_path)


def test_explicit_value_wins_over_env_var(monkeypatch, tmp_path):
    other = tmp_path / "explicit"
    other.mkdir()
    monkeypatch.setenv(ENV, str(tmp_path))
    assert resolve_path(str(other), ENV) == str(other)


def test_surrounding_quotes_and_whitespace_are_stripped(tmp_path):
    assert resolve_path(f'  "{tmp_path}"  ', ENV) == str(tmp_path)


# --- presets ----------------------------------------------------------------

def test_vault_preset_reads_obsidian_vault_path(monkeypatch, tmp_path):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    assert resolve_vault_path() == str(tmp_path)


def test_wiki_preset_reads_obsidian_wiki_path(monkeypatch, tmp_path):
    monkeypatch.setenv("OBSIDIAN_WIKI_PATH", str(tmp_path))
    assert resolve_wiki_path() == str(tmp_path)


def test_wiki_preset_distinguishes_unset_from_broken(monkeypatch, tmp_path):
    """
    The session director relies on this distinction: unset means "feature off",
    but configured-and-broken must be reported instead of looking identical.
    """
    assert resolve_wiki_path(required=False) is None

    monkeypatch.setenv("OBSIDIAN_WIKI_PATH", str(tmp_path / "gone"))
    with pytest.raises(PathConfigError):
        resolve_wiki_path(required=False)
