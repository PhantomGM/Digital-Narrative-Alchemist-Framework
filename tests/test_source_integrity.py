"""
Every Python file in the tree must parse.

Four files sat broken in this repository from their first commit and went
unnoticed because nothing imported them: two had docstrings written with
backslash-escaped quote characters, and two were truncated mid-file with an AI
tool's status message ("File unchanged since last read...") written in where the
body belonged. Nothing caught it — they were never imported, so no test or run
ever touched them, and a syntax error in an unimported module is invisible.

This test is the cheap guard against that whole class: corruption from an
interrupted or over-escaped write, committed and then forgotten.
"""

import ast
import io
import os

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SKIP_DIRS = {
    "venv", ".git", "__pycache__", "node_modules", ".obsidian",
    "build", "dist", ".pytest_cache",
}

# Text that means a tool's output was written into a source file instead of code.
TOOL_ARTIFACTS = (
    "File unchanged since last read",
    "The content from the earlier read_file result",
    "refer to that instead of re-reading",
)


def python_files():
    found = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                path = os.path.join(dirpath, filename)
                found.append(os.path.relpath(path, REPO_ROOT).replace("\\", "/"))
    return sorted(found)


ALL_PY = python_files()


def test_the_tree_has_python_files():
    """Guard the guard: a broken walk would make everything below vacuous."""
    assert len(ALL_PY) > 50, f"only found {len(ALL_PY)} files; walk is wrong"


@pytest.mark.parametrize("rel", ALL_PY)
def test_file_parses(rel):
    path = os.path.join(REPO_ROOT, rel)
    source = io.open(path, encoding="utf-8").read()
    try:
        ast.parse(source)
    except SyntaxError as exc:
        pytest.fail(f"{rel} does not parse: line {exc.lineno}: {exc.msg}")


#  This module quotes the markers above, so it would flag itself.
SELF = os.path.relpath(os.path.abspath(__file__), REPO_ROOT).replace("\\", "/")


@pytest.mark.parametrize("rel", [p for p in ALL_PY if p != SELF])
def test_file_has_no_tool_output_written_into_it(rel):
    source = io.open(os.path.join(REPO_ROOT, rel), encoding="utf-8").read()
    for marker in TOOL_ARTIFACTS:
        assert marker not in source, (
            f"{rel} contains tool output where code should be: {marker!r}. "
            "A write was interrupted and the status message was saved as source."
        )
