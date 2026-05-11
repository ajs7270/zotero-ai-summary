#!/usr/bin/env bash
set -euo pipefail
version="$(python3 -c "import json;print(json.load(open('plugin/manifest.json'))['version'])")"
mkdir -p dist
out="dist/zotero-ai-summary-${version}.xpi"
rm -f "$out"
(cd plugin && zip -qr "../$out" . -x '*.DS_Store')
python3 -c "import os;print(os.path.abspath('$out'))"
