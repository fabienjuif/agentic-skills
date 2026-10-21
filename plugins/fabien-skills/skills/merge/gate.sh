#!/usr/bin/env bash
# Gate a PR before it merges; prints the head sha it passed on, for merge.sh.
# On GitHub, waits for the required checks (all checks when none are
# required). With a command, also runs it on the head in a throwaway worktree,
# unless every changed file is docs (*.md, docs/).
#   gate.sh <n> [command...]
set -euo pipefail
dir=$(dirname "$0")
. "$dir/forge.sh"
n=$1; shift
read -r state sha base < <("$dir/pr.sh" "$n" | python3 -c '
import json, sys; p = json.load(sys.stdin); print(p["state"], p["head_sha"], p["base_ref"])')
[ "$state" = open ] || { echo "PR $n is $state" >&2; exit 1; }

if [ "$forge" = github ]; then
    for scope in --required ""; do
        # shellcheck disable=SC2086 # empty scope means all checks
        if out=$(gh pr checks "$n" $scope --watch --fail-fast 2>&1); then
            echo "checks passed${scope:+ (required)}" >&2; break
        fi
        grep -qi 'no .*checks reported' <<<"$out" || { echo "$out" >&2; exit 1; }
        [ -n "$scope" ] || echo "no checks reported" >&2
    done
fi

if [ $# -gt 0 ]; then
    primary=$(git worktree list --porcelain | sed -n '1s/^worktree //p')
    git -C "$primary" fetch -q origin "$base" "refs/pull/$n/head"
    if git -C "$primary" diff --name-only "origin/$base...$sha" | grep -qvE '(\.md$|^docs/)'; then
        wt=$primary/.worktrees/gate-pr-$n
        git -C "$primary" worktree add -q --detach "$wt" "$sha"
        trap 'git -C "$primary" worktree remove --force "$wt"' EXIT
        (cd "$wt" && "$@") >&2
    else
        echo "docs-only: $* skipped" >&2
    fi
fi
echo "$sha"
