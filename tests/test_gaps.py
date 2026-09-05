"""The no-silent-alteration rule is itself machine-checked.

Every `provisional: GAP-nn` marker in the substrate has a matching entry in
open-questions/computability-gaps.md, and every adjudication references an
existing gap id. Gap entries stay PENDING until a logged adjudication.
"""
import re
from pathlib import Path

from conftest import ADJUDICATIONS, GAPS, ROOT

SUBSTRATE_GLOBS = (
    "model/*.sysml",
    "model/*.ttl",
    "vocabulary/*.ttl",
    "track/*.trig",
    "shapes/*.ttl",
    "queries/*.rq",
    "counterexamples/*",
    "exhibits.py",
    "index.md",
    "chapters/*.ipynb",
)


def _substrate_files():
    files: list[Path] = []
    for pattern in SUBSTRATE_GLOBS:
        files.extend(ROOT.glob(pattern))
    return files


def _gap_ids():
    text = GAPS.read_text()
    return set(re.findall(r"^##\s+(GAP-\d+)", text, flags=re.M)), text


def test_gap_entries_exist_with_status_lines():
    ids, text = _gap_ids()
    assert ids, "computability-gaps.md holds no entries; the gap file must exist and be populated as gaps arise"
    for gap_id in ids:
        entry = text.split(gap_id, 1)[1]
        assert re.search(r"\*\*Status:\*\*\s+(PENDING|ADJUDICATED)", entry), (
            f"{gap_id} carries no Status line"
        )


def test_every_provisional_marker_has_a_pending_gap_entry():
    ids, text = _gap_ids()
    for f in _substrate_files():
        for marker in re.findall(r"provisional:\s*(GAP-\d+)", f.read_text()):
            assert marker in ids, f"{f.name} marks {marker} but computability-gaps.md has no such entry"


def test_every_adjudication_references_an_existing_gap():
    ids, _ = _gap_ids()
    adjudicated = set(re.findall(r"(GAP-\d+)", ADJUDICATIONS.read_text()))
    unknown = adjudicated - ids
    assert not unknown, f"adjudication log references unknown gap ids: {unknown}"
