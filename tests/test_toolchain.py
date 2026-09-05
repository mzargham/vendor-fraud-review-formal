"""The evaluator in use is the pinned evaluator, provably, on every run.

External review (2026-09-05), finding 2: a cached binary was trusted on
its --version text alone. The expected per-platform binary digests are
committed (toolchain/sysml-binaries.sha256, derived from tarballs
verified against the pinned release checksums in
toolchain/SHA256SUMS.pinned); the installed binary must hash to the
committed value, here and inside toolchain/get-sysml.sh on every
invocation.
"""
import hashlib
import platform

from conftest import ROOT, SYSML

PLATFORMS = {
    ("Darwin", "arm64"): "darwin-arm64",
    ("Darwin", "x86_64"): "darwin-amd64",
    ("Linux", "x86_64"): "linux-amd64",
    ("Linux", "aarch64"): "linux-arm64",
}


def _expected():
    text = (ROOT / "toolchain" / "sysml-binaries.sha256").read_text()
    return dict(
        reversed(line.split()) for line in text.strip().splitlines()
    )


def test_committed_digests_cover_every_supported_platform():
    assert set(_expected()) == set(PLATFORMS.values())


def test_installed_binary_matches_the_committed_digest():
    key = PLATFORMS.get((platform.system(), platform.machine()))
    assert key is not None, "unsupported platform for the pinned evaluator"
    got = hashlib.sha256(SYSML.read_bytes()).hexdigest()
    assert got == _expected()[key], (
        "the installed sysml binary does not hash to the committed digest: "
        "it is not the pinned evaluator"
    )


def test_fetch_script_verifies_the_binary_every_run():
    script = (ROOT / "toolchain" / "get-sysml.sh").read_text()
    assert "sysml-binaries.sha256" in script, (
        "get-sysml.sh does not verify the installed binary against the "
        "committed digests"
    )
    assert "SHA256SUMS.pinned" in script, (
        "get-sysml.sh does not verify tarballs against the in-repo pinned sums"
    )


def test_regeneration_removes_stale_generated_csvs():
    # External review (2026-09-05), finding 3: a removed or renamed query
    # must not leave its old CSV behind for the byte-diff to bless.
    import sys

    sys.path.insert(0, str(ROOT / "checks"))
    import render_queries

    stale = ROOT / "generated" / "zz-stale-regression.csv"
    stale.write_text("stale\n")
    try:
        render_queries.render()
        assert not stale.exists(), (
            "regeneration left a stale CSV in generated/: a removed query's "
            "output would survive the byte-diff"
        )
    finally:
        stale.unlink(missing_ok=True)
