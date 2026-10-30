#!/usr/bin/env bash
# Check and clean an LLM-written markdown file before it is posted to GitHub.
#
# Usage: scripts/ci/sanitize_report.sh <file>
#
# Fails if the file is missing or empty, larger than 60 KB, or contains
# anything that looks like a credential. Otherwise neutralises @mentions in
# place (a zero-width space after the @) so the text cannot ping anyone.

set -euo pipefail

FILE="${1:?usage: sanitize_report.sh <file>}"

if [ ! -s "$FILE" ]; then
  echo "::error::${FILE} is missing or empty."
  exit 1
fi
if [ "$(wc -c < "$FILE")" -gt 60000 ]; then
  echo "::error::${FILE} is larger than 60 KB; not publishing."
  exit 1
fi
SECRET_RE='sk-ant-|gh[opsur]_[A-Za-z0-9]{20,}|github_pat_|AKIA[0-9A-Z]{16}'
SECRET_RE="${SECRET_RE}|-----BEGIN|[A-Za-z0-9+/=]{80,}"
if grep -Eq "$SECRET_RE" "$FILE"; then
  echo "::error::${FILE} contains credential-like content; not publishing."
  exit 1
fi
sed -i 's/@\([A-Za-z0-9]\)/@\xE2\x80\x8B\1/g' "$FILE"
