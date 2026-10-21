#!/usr/bin/env bash
# Squash-merge PR n with the given subject and body (default empty), deleting
# the remote branch. The forge refuses the merge if the head moved past the
# sha gate.sh passed on. Exit 3: GitHub queued it (merge queue or auto-merge)
# instead of merging now.
#   merge.sh <n> <sha> <subject> [body]
set -euo pipefail
# An empty sha means the gate failed before printing one: a PR once merged red so.
[ -n "${2:-}" ] || { echo "empty sha: the gate did not pass" >&2; exit 1; }
dir=$(dirname "$0")
. "$dir/forge.sh"
n=$1 sha=$2 subject=$3 body=${4:-}

if [ "$forge" = github ]; then
    gh pr merge "$n" --squash --match-head-commit "$sha" --subject "$subject" --body "$body"
    read -r state ref cross < <(gh pr view "$n" --json state,headRefName,isCrossRepository \
        --jq '"\(.state) \(.headRefName) \(.isCrossRepository)"')
    [ "$state" = MERGED ] || { echo "PR $n not merged yet ($state): queued or auto-merge" >&2; exit 3; }
    # Repos that auto-delete head branches answer 422 here.
    [ "$cross" = true ] || gh api -X DELETE "repos/{owner}/{repo}/git/refs/heads/$ref" >/dev/null 2>&1 || true
else
    read -r state mergeable < <("$dir/pr.sh" "$n" | python3 -c '
import json, sys; p = json.load(sys.stdin); print(p["state"], p["mergeable"])')
    [ "$state" = open ] || { echo "PR $n is $state" >&2; exit 1; }
    [ "$mergeable" = True ] || { echo "PR $n has conflicts" >&2; exit 1; }
    req=$(python3 -c 'import json, sys; print(json.dumps({"Do": "squash", "MergeTitleField": sys.argv[1], "MergeMessageField": sys.argv[2], "head_commit_id": sys.argv[3], "delete_branch_after_merge": True}))' "$subject" "$body" "$sha")
    # Right after another merge Forgejo answers 405 while it rechecks mergeability.
    for _ in 1 2 3 4 5 6; do
        code=$(fj -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d "$req" "$api/pulls/$n/merge")
        [ "$code" = 405 ] || break
        sleep 10
    done
    [ "$code" = 200 ] || { echo "merge refused: HTTP $code" >&2; exit 1; }
fi
echo "merged $n: $subject"
