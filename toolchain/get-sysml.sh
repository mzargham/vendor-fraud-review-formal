#!/usr/bin/env bash
# Fetch the pinned OpenSysML binary into toolchain/bin/ (gitignored),
# verified against the release's SHA256SUMS.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p bin
VER="v0.4.3"
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) ART="opensysml-darwin-arm64.tar.gz" ;;
  Darwin-x86_64) ART="opensysml-darwin-amd64.tar.gz" ;;
  Linux-x86_64) ART="opensysml-linux-amd64.tar.gz" ;;
  Linux-aarch64) ART="opensysml-linux-arm64.tar.gz" ;;
  *) echo "unsupported platform" >&2; exit 1 ;;
esac
if [ -x bin/sysml ] && bin/sysml --version 2>/dev/null | grep -q "sysml v0.4.3"; then exit 0; fi
BASE="https://github.com/Open-MBEE/OpenSysML/releases/download/${VER}"
curl -fsSL -o /tmp/osml.tgz "${BASE}/${ART}"
curl -fsSL -o /tmp/osml.sums "${BASE}/SHA256SUMS.txt"
WANT=$(grep " ${ART}\$" /tmp/osml.sums | awk '{print $1}')
GOT=$( (command -v sha256sum >/dev/null && sha256sum /tmp/osml.tgz || shasum -a 256 /tmp/osml.tgz) | awk '{print $1}')
if [ -z "$WANT" ] || [ "$WANT" != "$GOT" ]; then
  echo "sysml checksum mismatch (want=$WANT got=$GOT)" >&2; exit 1
fi
tar xzf /tmp/osml.tgz -C bin/ sysml
echo "sysml installed+verified: $(bin/sysml --version | head -1)"
