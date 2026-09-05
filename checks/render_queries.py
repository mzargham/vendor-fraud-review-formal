"""Render the SPARQL query results to generated/ as CSV (deterministic:
every query carries an ORDER BY). The check script runs this twice and
diffs against the committed files."""
from pathlib import Path

import rdflib

ROOT = Path(__file__).resolve().parent.parent

ds = rdflib.Dataset(default_union=True)
ds.parse(ROOT / "track" / "run-001.trig", format="trig")

for rq in sorted((ROOT / "queries").glob("*.rq")):
    result = ds.query(rq.read_text())
    out = ROOT / "generated" / f"{rq.stem}.csv"
    out.write_bytes(result.serialize(format="csv"))
    print(f"{out.relative_to(ROOT)}: {len(result)} rows")
