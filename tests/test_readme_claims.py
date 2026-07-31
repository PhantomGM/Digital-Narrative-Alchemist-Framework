"""
The README's factual claims must match the code.

Documentation drift is not cosmetic. The README claimed "14 entity types" when 21
were registered, and its roadmap asked for a `region` decoder that had existed for
some time while missing the six generators that genuinely lacked one. A reader
following it would have been wrong about what the project does.

Only durable, architecture-level claims are checked here — counts of types,
decoders and scripts. Nothing that changes every commit, so this guard does not
turn ordinary work into a documentation chore.
"""

import io
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.decoder import DNADecoder  # noqa: E402
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402
from layer5_dna_substrate.obsidian_sync import ObsidianSync  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def readme():
    with io.open(os.path.join(REPO, "README.md"), encoding="utf-8") as handle:
        return handle.read()


@pytest.fixture(scope="module")
def generators():
    return set(ProceduralForge().generators)


@pytest.fixture(scope="module")
def decoders():
    return set(DNADecoder().prompts)


def test_generator_count_is_accurate(readme, generators):
    match = re.search(r"(\d+) entity types registered", readme)
    assert match, "the README no longer states a generator count"
    assert int(match.group(1)) == len(generators)


def test_decoder_count_is_accurate(readme, decoders):
    match = re.search(r"(\d+) with dedicated decoders", readme)
    assert match, "the README no longer states a decoder count"
    assert int(match.group(1)) == len(decoders)


def test_the_decoderless_generators_are_named_correctly(readme, generators, decoders):
    """The roadmap once named the wrong ones, including one already done."""
    match = re.search(r"generators still lack decoder prompts — (.+?)\.", readme, re.S)
    assert match, "the README no longer lists the decoderless generators"
    listed = sorted(re.findall(r"`([a-z_]+)`", match.group(1)))
    assert listed == sorted(generators - decoders)


def test_no_invented_dna_types(readme, generators):
    """Every type the DNA section names must actually be registered."""
    section = re.search(r"### DNA types(.+?)### Consistency auditing", readme, re.S)
    assert section, "the DNA types section is missing"
    named = set(re.findall(r"`([a-z_]+)`", section.group(1)))
    assert named <= generators, f"not registered: {sorted(named - generators)}"


def test_every_script_listed_exists(readme):
    section = re.search(r"### Scripts(.+?)^---", readme, re.S | re.M)
    assert section, "the scripts section is missing"
    listed = set(re.findall(r"`([\w]+\.py)`", section.group(1)))
    actual = {name for name in os.listdir(os.path.join(REPO, "scripts"))
              if name.endswith(".py") and name != "__init__.py"}
    assert listed <= actual, f"documented but absent: {sorted(listed - actual)}"


def test_no_script_is_undocumented(readme):
    section = re.search(r"### Scripts(.+?)^---", readme, re.S | re.M)
    listed = set(re.findall(r"`([\w]+\.py)`", section.group(1)))
    actual = {name for name in os.listdir(os.path.join(REPO, "scripts"))
              if name.endswith(".py") and name != "__init__.py"}
    assert actual <= listed, f"undocumented: {sorted(actual - listed)}"


def test_protected_statuses_match_the_canon_table(readme):
    """The canon table promises which statuses the sync refuses to overwrite."""
    assert ObsidianSync.PROTECTED_STATUSES == {"canon", "deprecated"}
    assert "`canon`" in readme and "`deprecated`" in readme


def test_no_reference_to_a_repo_templates_directory(readme):
    """
    The roadmap pointed at `templates/` in the repo, which has never existed —
    the templates live in the vault.
    """
    assert not os.path.isdir(os.path.join(REPO, "templates"))
    assert "(`templates/`)" not in readme


def test_vault_paths_are_documented_as_required(readme):
    """Scripts refuse to guess a vault; a reader must be told before hitting it."""
    assert "OBSIDIAN_VAULT_PATH" in readme
    assert "--vault" in readme
