#!/usr/bin/env bash
# One PR as forge-neutral JSON: number, state (open | closed | merged),
# mergeable (true | false | null while the forge rechecks), title, head_sha,
# head_ref, base_ref, cross_repo, url.
#   pr.sh <n>
set -euo pipefail
. "$(dirname "$0")/forge.sh"
if [ "$forge" = github ]; then
    gh pr view "$1" --json number,state,mergeable,title,headRefOid,headRefName,baseRefName,isCrossRepository,url --jq '{
        number, state: (.state | ascii_downcase), title, url,
        mergeable: ({MERGEABLE: true, CONFLICTING: false}[.mergeable]),
        head_sha: .headRefOid, head_ref: .headRefName, base_ref: .baseRefName,
        cross_repo: .isCrossRepository}'
else
    fj "$api/pulls/$1" | python3 -c '
import json, sys
p = json.load(sys.stdin)
print(json.dumps({
    "number": p["number"], "title": p["title"], "url": p["html_url"],
    "state": "merged" if p["merged"] else p["state"],
    "mergeable": p["mergeable"],
    "head_sha": p["head"]["sha"], "head_ref": p["head"]["ref"], "base_ref": p["base"]["ref"],
    "cross_repo": p["head"]["repo_id"] != p["base"]["repo_id"]}))'
fi
