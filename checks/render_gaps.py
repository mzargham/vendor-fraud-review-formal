"""Render open-questions/computability-gaps.md from the judgment record.

The page is a generated view of open-questions/adjudications.ttl: edits
belong in the record, and the regeneration step refuses a page that has
drifted from it (byte-identical or fail).
"""
import pathlib
import textwrap

import rdflib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECORD = ROOT / "open-questions" / "adjudications.ttl"
PAGE = ROOT / "open-questions" / "computability-gaps.md"
VFR = rdflib.Namespace("https://example.org/vfr#")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")

HEADER = """\
# Computability gaps

<!-- GENERATED from adjudications.ttl by checks/render_gaps.py. Do not edit
     by hand: this page is a view of the judgment record, and the checks
     refuse a page that drifts from it. -->

Places where a literal parsing of the whitepaper (Revision 9) under-specifies
what the executable substrate requires. Nothing here is silently repaired:
where the build could not proceed without a choice, the most literal
available reading was taken, marked `provisional: GAP-nn` at the point of
use, and recorded. Every entry stays provisional until a ruling by a named
adjudicator is logged (verbatim in adjudication-log.md, machine-readable in
adjudications.ttl, from which this page is generated).
"""


def _wrap(text):
    return "\n".join(
        textwrap.fill(paragraph, width=78) for paragraph in str(text).split("\n")
    )


def render():
    g = rdflib.Graph()
    g.parse(RECORD, format="turtle")
    out = [HEADER]
    for gap in sorted(g.subjects(rdflib.RDF.type, VFR.ComputabilityGap), key=str):
        gid = str(gap).rsplit("#", 1)[-1]
        rulings = sorted(set(g.subjects(VFR.resolves, gap)), key=str)
        dates = sorted({str(g.value(r, PROV.generatedAtTime)) for r in rulings})
        status = str(g.value(gap, VFR.status)).upper()
        if rulings:
            status += f" ({', '.join(dates)}, see adjudication-log.md)"
        out.append(f"\n## {gid} — {g.value(gap, rdflib.RDFS.label)}\n")
        out.append(_wrap(f"**Status:** {status}"))
        out.append(_wrap(f"**Locus:** {g.value(gap, VFR.locusDetail)}"))
        out.append(_wrap(f"**Problem:** {g.value(gap, VFR.problem)}"))
        out.append(_wrap(
            f"**Surfaced:** {g.value(gap, VFR.surfacedOn)} — {g.value(gap, VFR.surfacedHow)}"
        ))
        out.append(_wrap(f"**Substrate forces:** {g.value(gap, VFR.substrateForces)}"))
        out.append(_wrap(f"**Possible readings:** {g.value(gap, VFR.possibleReadings)}"))
        out.append(_wrap(f"**Adjudicated reading in use:** {g.value(gap, VFR.readingInUse)}"))
        note = g.value(gap, VFR.note)
        if note is not None:
            out.append(_wrap(str(note)))
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    PAGE.write_text(render())
    print(f"rendered {PAGE.relative_to(ROOT)} from {RECORD.relative_to(ROOT)}")
