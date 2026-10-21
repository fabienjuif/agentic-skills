#!/usr/bin/env bash
# Open PRs (on GitHub only yours) against their base as it is now, by a local
# merge-tree: the forge's own mergeable flag lags right after a merge.
#   conflicts.sh
set -euo pipefail
. "$(dirname "$0")/forge.sh"
if [ "$forge" = github ]; then
    prs=$(gh pr list --author @me --json number,baseRefName,url --jq '.[] | "\(.number) \(.baseRefName) \(.url)"')
else
    prs=$(fj "$api/pulls?state=open&limit=50" | python3 -c '
import json, sys
for p in json.load(sys.stdin): print(p["number"], p["base"]["ref"], p["html_url"])')
fi
[ -n "$prs" ] || { echo "no open PRs"; exit 0; }
while read -r n base url; do
    git fetch -q origin "refs/pull/$n/head" "$base"
    if git merge-tree --write-tree --quiet "origin/$base" FETCH_HEAD; then r=clean; else r=CONFLICTS; fi
    echo "$n $r $url"
done <<<"$prs"
