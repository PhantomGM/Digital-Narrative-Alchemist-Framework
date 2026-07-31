"""
Shared resolution for externally-configured filesystem paths (vaults, wikis).

Why this exists: three call sites independently hardcoded a machine-specific
absolute path as a *silent* default — two in WSL form ("/mnt/c/Users/...") and
one in Windows form ("C:\\Users\\..."). Neither form parses on the other
platform, and each failed in its own quiet way:

  * Under POSIX, a Windows path is not a path at all — "\\" is not a separator,
    so the entire string becomes ONE directory name (with ":" and "\\" mapped
    into the U+F000 private-use range). A whole generated vault ended up
    stranded inside the repository under a single mangled filename.
  * Under Windows, a "/mnt/c/..." path silently fails an os.path.exists() guard,
    so an optional integration reports nothing and stays permanently dead.

Both failure modes come from guessing. resolve_path() never guesses: the caller
must supply the path or set the environment variable, and the value is validated
as a path *on the current platform* before anything reads or writes through it.
"""

import os

__all__ = ["PathConfigError", "resolve_path", "resolve_vault_path", "resolve_wiki_path"]


class PathConfigError(ValueError):
    """A configured path is missing or does not parse on this platform."""


def resolve_path(
    explicit: str = None,
    env_var: str = None,
    *,
    label: str = "path",
    required: bool = True,
    must_exist: bool = True,
    create: bool = False,
) -> str:
    """
    Resolve a filesystem path from an explicit value or an environment variable.

    Returns an absolute path, or None when the path is optional (required=False)
    and nothing was configured. Raises PathConfigError — never SystemExit, so
    library callers can decide how to degrade; CLI callers translate it.

    must_exist/create control whether a missing target is an error, tolerated,
    or created.
    """
    raw = explicit or (os.getenv(env_var) if env_var else None)
    if not raw or not raw.strip():
        if not required:
            return None
        hint = f" or set {env_var}" if env_var else ""
        raise PathConfigError(
            f"No {label} configured. Pass it explicitly{hint}. "
            "Refusing to guess: an unparsed path string gets created as a single "
            "literal directory, which silently strands the data."
        )

    resolved = os.path.abspath(os.path.expanduser(raw.strip().strip('"').strip("'")))

    # The decisive check. If a separator or drive-colon survives into the final
    # component, the string was never parsed as a path on THIS platform — e.g. a
    # Windows path under POSIX. Writing it creates one directory literally named
    # "C:\Users\...\Vault".
    leaf = os.path.basename(resolved)
    if any(ch in leaf for ch in (":", "\\", "/")):
        raise PathConfigError(
            f"{label} does not parse as a path on this platform (os.name={os.name!r}): "
            f"{raw!r} — its final component came out as {leaf!r}. "
            "Use this platform's own path form (e.g. /mnt/c/Users/... under WSL, "
            "C:\\Users\\... under Windows)."
        )

    if not os.path.isdir(resolved):
        if create:
            parent = os.path.dirname(resolved)
            if not os.path.isdir(parent):
                raise PathConfigError(
                    f"Cannot create {label}: parent directory does not exist: {parent}. "
                    "Refusing to build a tree at an unexpected location."
                )
            os.makedirs(resolved, exist_ok=True)
        elif must_exist:
            raise PathConfigError(f"{label} directory does not exist: {resolved}")

    return resolved


def resolve_vault_path(
    explicit: str = None,
    env_var: str = "OBSIDIAN_VAULT_PATH",
    *,
    create: bool = False,
    required: bool = True,
    must_exist: bool = True,
    label: str = "vault path",
) -> str:
    """resolve_path() preset for an Obsidian vault."""
    return resolve_path(
        explicit,
        env_var,
        label=label,
        required=required,
        must_exist=must_exist,
        create=create,
    )


def resolve_wiki_path(
    explicit: str = None,
    env_var: str = "OBSIDIAN_WIKI_PATH",
    *,
    required: bool = True,
    must_exist: bool = True,
    label: str = "wiki path",
) -> str:
    """
    resolve_path() preset for a read-only wiki directory used for RAG ingestion.

    Callers that treat the wiki as optional should pass required=False and still
    catch PathConfigError, so a *configured but broken* path is reported rather
    than being indistinguishable from "not configured".
    """
    return resolve_path(
        explicit,
        env_var,
        label=label,
        required=required,
        must_exist=must_exist,
        create=False,
    )
