#!/usr/bin/env bash
# Fetch the pinned OpenSysML binary into toolchain/bin/ (gitignored) and
# verify it on EVERY invocation, not only at download time (external
# review, 2026-09-05): tarballs are checked against the in-repo pinned
# release checksums (SHA256SUMS.pinned), and the installed binary must
# hash to the committed per-platform digest (sysml-binaries.sha256).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p bin
VER="v0.4.3"
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) PLAT="darwin-arm64" ;;
  Darwin-x86_64) PLAT="darwin-amd64" ;;
  Linux-x86_64) PLAT="linux-amd64" ;;
  Linux-aarch64) PLAT="linux-arm64" ;;
  *) echo "unsupported platform" >&2; exit 1 ;;
esac
ART="opensysml-${PLAT}.tar.gz"
BIN_WANT=$(grep " ${PLAT}\$" sysml-binaries.sha256 | awk '{print $1}')
[ -n "$BIN_WANT" ] || { echo "no committed digest for ${PLAT}" >&2; exit 1; }

sha() { (command -v sha256sum >/dev/null && sha256sum "$1" || shasum -a 256 "$1") | awk '{print $1}'; }

if [ -f bin/sysml ] && [ "$(sha bin/sysml)" = "$BIN_WANT" ]; then exit 0; fi

BASE="https://github.com/Open-MBEE/OpenSysML/releases/download/${VER}"
curl -fsSL -o /tmp/osml.tgz "${BASE}/${ART}"
TAR_WANT=$(grep " ${ART}\$" SHA256SUMS.pinned | awk '{print $1}')
TAR_GOT=$(sha /tmp/osml.tgz)
if [ -z "$TAR_WANT" ] || [ "$TAR_WANT" != "$TAR_GOT" ]; then
  echo "sysml tarball checksum mismatch (want=$TAR_WANT got=$TAR_GOT)" >&2; exit 1
fi
tar xzf /tmp/osml.tgz -C bin/ sysml
BIN_GOT=$(sha bin/sysml)
if [ "$BIN_GOT" != "$BIN_WANT" ]; then
  echo "installed sysml binary digest mismatch (want=$BIN_WANT got=$BIN_GOT)" >&2; exit 1
fi
echo "sysml installed+verified: $(bin/sysml --version | head -1)"
