"""Render the SPARQL query results to generated/ as CSV (deterministic:
every query carries an ORDER BY). Existing CSVs are removed first, so
generated/ holds exactly one CSV per committed query — a removed or
renamed query cannot leave a stale output behind for the byte-diff to
bless (external review, 2026-09-05). The check script runs this and
diffs against the committed files.
"""
from pathlib import Path

import rdflib

ROOT = Path(__file__).resolve().parent.parent


def render():
    for old in sorted((ROOT / "generated").glob("*.csv")):
        old.unlink()
    ds = rdflib.Dataset(default_union=True)
    ds.parse(ROOT / "track" / "run-001.trig", format="trig")
    for rq in sorted((ROOT / "queries").glob("*.rq")):
        result = ds.query(rq.read_text())
        out = ROOT / "generated" / f"{rq.stem}.csv"
        out.write_bytes(result.serialize(format="csv"))
        print(f"{out.relative_to(ROOT)}: {len(result)} rows")


if __name__ == "__main__":
    render()
