"""
Make standard output incapable of raising on unencodable characters.

The problem this solves is Windows-specific and easy to miss. When stdout is a
pipe or a redirect rather than a console, Python picks the locale encoding —
cp1252 here — and printing any character outside it raises UnicodeEncodeError.
The project prints freely: progress emoji in the demo scripts, check marks in
the coordinator, and, worse, vault-derived prose containing em dashes and
emoji. So the failure is not confined to decorative literals that could simply
be rewritten in ASCII; it follows the data.

Two real defects came from this. EventLedger.emit() printed a "→" and so failed
on every call. StateCritic.validate() logged its mismatch verdict with a check
mark from inside the try that falls back to "consistent", so a detected
mismatch was swallowed and reported as a match.

Rather than strip every glyph, entry points call enable_safe_stdout(), which
switches the streams to errors="replace". Unencodable characters degrade to "?"
instead of raising, and terminals that can render them are unaffected.
"""

import sys

__all__ = ["enable_safe_stdout"]

_applied = False


def enable_safe_stdout(force: bool = False) -> bool:
    """
    Switch sys.stdout and sys.stderr to errors="replace".

    Call once, early, from an entry point. Encoding is left alone, so output
    looks identical wherever it already worked; only the crash goes away.

    Returns True if at least one stream was reconfigured. Never raises: a
    stream that cannot be reconfigured (pytest's capture object, an already
    wrapped stream, a closed handle) is skipped, since failing to adjust
    logging must not take down the program it was meant to protect.
    """
    global _applied
    if _applied and not force:
        return False

    changed = False
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        # Nothing to do when the stream already replaces bad characters.
        if getattr(stream, "errors", None) in ("replace", "backslashreplace", "ignore"):
            continue
        try:
            reconfigure(errors="replace")
            changed = True
        except (ValueError, OSError, AttributeError):
            continue

    _applied = True
    return changed
