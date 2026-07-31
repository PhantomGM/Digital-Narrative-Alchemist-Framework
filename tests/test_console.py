"""
Tests for common.console.enable_safe_stdout.

Guards a Windows-specific failure that produced two real bugs. When stdout is a
pipe rather than a console, Python uses the locale encoding (cp1252 here), and
printing anything outside it raises UnicodeEncodeError. EventLedger.emit()
failed on every call for this reason, and StateCritic.validate() silently
converted a detected mismatch into a match because logging the verdict raised
inside the try that falls back to "consistent".

Note on mechanics: stdout is swapped inside each test body, not in a fixture.
pytest resumes its global capture between fixture setup and the test call, which
reassigns sys.stdout and would discard a fixture-applied patch.
"""

import io
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import common.console as console  # noqa: E402
from common.console import enable_safe_stdout  # noqa: E402

# Characters this project actually prints: arrow, check mark, DNA emoji, box
# drawing. None are encodable in cp1252.
GLYPHS = "→ ✓ \U0001f9ec ─"


def use_cp1252_stdout(monkeypatch):
    """Swap in a cp1252 stream, as a piped Windows shell provides."""
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", stream)
    monkeypatch.setattr(sys, "stderr", stream)
    monkeypatch.setattr(console, "_applied", False)  # let each test start fresh
    assert sys.stdout is stream, "stdout patch did not take effect"
    return stream


def written(stream):
    stream.flush()
    return stream.buffer.getvalue().decode("cp1252")


# --- the hazard -------------------------------------------------------------

def test_the_hazard_is_real(monkeypatch):
    """Without the fix, these characters cannot reach a cp1252 stream."""
    stream = use_cp1252_stdout(monkeypatch)
    with pytest.raises(UnicodeEncodeError):
        print(GLYPHS)
        stream.flush()  # TextIOWrapper buffers; the encode happens here


def test_glyphs_print_without_raising_after_enabling(monkeypatch):
    stream = use_cp1252_stdout(monkeypatch)
    enable_safe_stdout()
    print(GLYPHS)
    stream.flush()  # must not raise


def test_unencodable_characters_degrade_to_replacement(monkeypatch):
    stream = use_cp1252_stdout(monkeypatch)
    enable_safe_stdout()
    print(GLYPHS)
    out = written(stream)
    assert "?" in out
    assert "→" not in out


def test_vault_prose_with_em_dash_and_emoji(monkeypatch):
    """
    The case that rewriting literals cannot fix: the text is data read from the
    vault, not a hardcoded decoration.
    """
    stream = use_cp1252_stdout(monkeypatch)
    enable_safe_stdout()
    print("Kaelen — the Archivist, sigil \U0001f9ec")
    stream.flush()  # must not raise


# --- what must not change ---------------------------------------------------

def test_ascii_output_is_unchanged(monkeypatch):
    """Output that already worked must look identical."""
    stream = use_cp1252_stdout(monkeypatch)
    enable_safe_stdout()
    print("plain ASCII line")
    assert "plain ASCII line" in written(stream)


def test_encoding_is_left_alone(monkeypatch):
    """Only the error handler changes, so byte output stays predictable."""
    use_cp1252_stdout(monkeypatch)
    enable_safe_stdout()
    assert sys.stdout.encoding.lower().replace("-", "") == "cp1252"
    assert sys.stdout.errors == "replace"


def test_stderr_is_covered_too(monkeypatch):
    use_cp1252_stdout(monkeypatch)
    enable_safe_stdout()
    assert sys.stderr.errors == "replace"


# --- contract ---------------------------------------------------------------

def test_reports_whether_it_changed_anything(monkeypatch):
    use_cp1252_stdout(monkeypatch)
    assert enable_safe_stdout() is True


def test_is_idempotent(monkeypatch):
    use_cp1252_stdout(monkeypatch)
    assert enable_safe_stdout() is True
    assert enable_safe_stdout() is False


def test_already_safe_stream_is_left_alone(monkeypatch):
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="replace")
    monkeypatch.setattr(sys, "stdout", stream)
    monkeypatch.setattr(sys, "stderr", stream)
    monkeypatch.setattr(console, "_applied", False)
    assert enable_safe_stdout() is False
    assert stream.errors == "replace"


# --- must never make things worse -------------------------------------------

def test_never_raises_on_a_stream_without_reconfigure(monkeypatch):
    """pytest's capture object and a plain StringIO have no reconfigure()."""
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    monkeypatch.setattr(console, "_applied", False)
    assert enable_safe_stdout() is False


def test_never_raises_when_reconfigure_fails(monkeypatch):
    class Hostile:
        errors = "strict"

        def reconfigure(self, **kwargs):
            raise ValueError("cannot reconfigure")

    monkeypatch.setattr(sys, "stdout", Hostile())
    monkeypatch.setattr(sys, "stderr", Hostile())
    monkeypatch.setattr(console, "_applied", False)
    assert enable_safe_stdout() is False


def test_missing_stream_is_tolerated(monkeypatch):
    """Under pythonw or a detached process the streams can be None."""
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(console, "_applied", False)
    assert enable_safe_stdout() is False
