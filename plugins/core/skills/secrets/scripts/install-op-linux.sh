#!/usr/bin/env sh
# Installs the 1Password CLI on Linux (for example in a cloud environment setup script).
# It downloads one zip from 1Password, checks it, and puts op in /usr/local/bin (or ~/.local/bin).
set -eu

if command -v op >/dev/null 2>&1; then
  op --version
  exit 0
fi

version="${OP_VERSION:-2.41.1}"
case "$(uname -m)" in
  x86_64 | amd64) arch=amd64 ;;
  aarch64 | arm64) arch=arm64 ;;
  *) echo "Architecture not supported: $(uname -m)" >&2; exit 1 ;;
esac

url="https://cache.agilebits.com/dist/1P/op2/pkg/v${version}/op_linux_${arch}_v${version}.zip"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

curl -fsSL "$url" -o "$tmp/op.zip"
if command -v unzip >/dev/null 2>&1; then
  unzip -q "$tmp/op.zip" -d "$tmp"
else
  python3 -c "import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$tmp/op.zip" "$tmp"
fi

if [ -w /usr/local/bin ]; then
  dest=/usr/local/bin
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  dest=/usr/local/bin
  sudo install -m 0755 "$tmp/op" "$dest/op"
  "$dest/op" --version
  exit 0
else
  dest="$HOME/.local/bin"
  mkdir -p "$dest"
fi
install -m 0755 "$tmp/op" "$dest/op"
"$dest/op" --version
