"""The site is configured honestly: the TOC is complete, the citations
resolve, and the framing preamble is present.
"""
import re

import nbformat
import yaml

from conftest import CHAPTERS, INDEX, MYST_CONFIG, REFERENCES, ROOT


def _toc_files(entries):
    for entry in entries:
        if "file" in entry:
            yield entry["file"]
        yield from _toc_files(entry.get("children", []))


def _config():
    return yaml.safe_load(MYST_CONFIG.read_text())


def test_every_toc_entry_exists():
    toc = list(_toc_files(_config()["project"]["toc"]))
    assert toc, "myst.yml declares no toc"
    for rel in toc:
        assert (ROOT / rel).exists(), f"toc entry does not exist: {rel}"


def test_every_chapter_is_in_the_toc_in_order():
    toc = [rel for rel in _toc_files(_config()["project"]["toc"])]
    chapter_positions = []
    for chapter in CHAPTERS:
        rel = str(chapter.relative_to(ROOT))
        assert rel in toc, f"chapter missing from toc: {rel}"
        chapter_positions.append(toc.index(rel))
    assert chapter_positions == sorted(chapter_positions), "chapters out of order in toc"
    assert toc[0] == "index.md", "index.md must open the toc"


def test_bibliography_is_declared_and_present():
    project = _config()["project"]
    assert "references.bib" in project.get("bibliography", []), (
        "myst.yml does not declare references.bib"
    )
    assert REFERENCES.exists()


def test_every_citation_key_resolves():
    defined = set(re.findall(r"^@\w+\{([^,]+),", REFERENCES.read_text(), re.M))
    assert "oliphant2026" in defined, "the whitepaper must have a bib entry"
    used = set()
    texts = [INDEX.read_text()]
    for path in CHAPTERS:
        nb = nbformat.read(path, as_version=4)
        texts += [c.source for c in nb.cells if c.cell_type == "markdown"]
    for text in texts:
        used |= set(re.findall(r"\[@([A-Za-z][\w-]*)", text))
        used |= set(re.findall(r";\s*@([A-Za-z][\w-]*)", text))
    assert "oliphant2026" in used, "the walkthrough never cites the whitepaper"
    unresolved = used - defined
    assert not unresolved, f"citation keys with no bib entry: {sorted(unresolved)}"


def test_index_opens_with_the_translation_not_audit_preamble():
    text = INDEX.read_text()
    assert "translation, not an audit" in text, "the framing preamble is missing"
    assert "limits of the written form" in text, (
        "the preamble must attribute filled gaps to the written form, not the author"
    )
    assert "5.6" in text.split("##")[0] or "5.6" in text[:2000], (
        "the preamble must state the scope: one piece of the paper, section 5.6"
    )
