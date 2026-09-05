"""Direct citation is a checked property of the walkthrough, not a habit.

Every blockquote in the walkthrough prose that cites the whitepaper
(@oliphant2026) must be verbatim, under the same normalization the SKOS
definitions get, from the sha256-pinned PDF snapshot.
"""
import nbformat

from conftest import CHAPTERS, INDEX, normalized


def _blockquotes(markdown):
    """Yield lists of raw lines for each contiguous blockquote."""
    block = []
    for line in markdown.splitlines():
        if line.lstrip().startswith(">"):
            block.append(line.lstrip().lstrip(">").strip())
        elif block:
            yield block
            block = []
    if block:
        yield block


def _cited_quotes(markdown):
    """(quote text, citation line) for each @oliphant2026-cited blockquote."""
    for block in _blockquotes(markdown):
        citations = [l for l in block if "@oliphant2026" in l]
        if not citations:
            continue
        quote = " ".join(l for l in block if l and "@oliphant2026" not in l)
        yield quote, citations[-1]


def _chapter_markdown(path):
    nb = nbformat.read(path, as_version=4)
    return "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")


def test_every_cited_quote_is_verbatim_within_its_cited_section(pdf_sections):
    import re

    sources = [("index.md", INDEX.read_text())]
    sources += [(p.name, _chapter_markdown(p)) for p in CHAPTERS]
    checked = 0
    for name, markdown in sources:
        for quote, citation in _cited_quotes(markdown):
            assert quote, f"{name}: a cited blockquote carries no quoted text"
            locators = ["§" + m for m in re.findall(r"§(\d+\.\d+)", citation)]
            assert locators, f"{name}: citation lacks a section locator: {citation!r}"
            for locator in locators:
                assert locator in pdf_sections, (
                    f"{name}: locator {locator!r} names no section"
                )
            assert any(normalized(quote) in pdf_sections[l] for l in locators), (
                f"{name}: quote is not verbatim within its cited section(s) "
                f"{locators}: {quote!r}"
            )
            checked += 1
    assert checked >= 6, "the walkthrough should quote the pinned source throughout"


def test_every_chapter_quotes_the_pinned_source():
    for path in CHAPTERS:
        quotes = list(_cited_quotes(_chapter_markdown(path)))
        assert quotes, f"{path.name} has no machine-checked quote from the whitepaper"
