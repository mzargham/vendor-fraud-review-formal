"""Render open-questions/adjudication-log.md from the judgment record.

The page is a generated view of open-questions/adjudications.ttl: entries
in vfr:order, each with the adjudicator's words verbatim and the change
note. Edits belong in the record; the regeneration step refuses a page
that has drifted.
"""
import pathlib
import textwrap

import rdflib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECORD = ROOT / "open-questions" / "adjudications.ttl"
PAGE = ROOT / "open-questions" / "adjudication-log.md"
VFR = rdflib.Namespace("https://example.org/vfr#")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")

HEADER = """\
# Adjudication log

<!-- GENERATED from adjudications.ttl by checks/render_log.py. Do not edit
     by hand: this page is a view of the judgment record, and the checks
     refuse a page that drifts from it. -->

Rulings and design notes, in the order they were made. Each entry records
the date, the adjudicator's words verbatim, and what changed in the
substrate as a result. The machine-readable record (gap, ruling, named
adjudicator, derived implementations) is adjudications.ttl.
"""


def _wrap(text):
    return "\n".join(
        textwrap.fill(paragraph, width=78) for paragraph in str(text).split("\n")
    )


def render():
    g = rdflib.Graph()
    g.parse(RECORD, format="turtle")
    entries = []
    for node in set(g.subjects(VFR.order, None)):
        entries.append((int(g.value(node, VFR.order)), node))
    out = [HEADER]
    for _, node in sorted(entries):
        title = g.value(node, VFR.entryTitle)
        date = g.value(node, PROV.generatedAtTime)
        out.append(f"\n## {date} — {title}\n")
        ruling = g.value(node, VFR.rulingText)
        note = g.value(node, VFR.noteText)
        if ruling is not None:
            out.append(_wrap(f'**Ruling (verbatim):** "{ruling}"'))
        if note is not None:
            out.append(_wrap(f'**Note (verbatim):** "{note}"'))
        out.append("")
        out.append(_wrap(f"**Changed:** {g.value(node, VFR.changeNote)}"))
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    PAGE.write_text(render())
    print(f"rendered {PAGE.relative_to(ROOT)} from {RECORD.relative_to(ROOT)}")
