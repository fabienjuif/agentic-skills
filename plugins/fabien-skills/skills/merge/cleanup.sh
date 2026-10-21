#!/usr/bin/env bash
# After a merge: drop the PR branch's worktree and local branch, then
# fast-forward the base branch. A worktree with uncommitted changes, or a branch
# whose tip is not the merged sha, is kept and reported, never deleted.
#   cleanup.sh <branch> <sha> <base>
set -euo pipefail
branch=$1 sha=$2 base=$3
primary=$(git worktree list --porcelain | sed -n '1s/^worktree //p')
wt_of() { git -C "$primary" worktree list --porcelain | awk -v b="refs/heads/$1" '
    /^worktree / { w = substr($0, 10) } $0 == "branch " b { print w }'; }
kept=

wt=$(wt_of "$branch")
if [ -n "$wt" ]; then
    if [ -n "$(git -C "$wt" status --porcelain)" ] || [ "$(git -C "$wt" rev-parse HEAD)" != "$sha" ]; then
        echo "kept $wt: uncommitted changes or commits not in the PR" >&2; kept=1
    elif [ "$wt" = "$primary" ]; then
        git -C "$primary" switch -q "$base"
    else
        git -C "$primary" worktree remove "$wt" && echo "removed worktree $wt" >&2
    fi
fi
if [ -z "$kept" ] && git -C "$primary" rev-parse -q --verify "refs/heads/$branch" >/dev/null; then
    if [ "$(git -C "$primary" rev-parse "refs/heads/$branch")" = "$sha" ]; then
        git -C "$primary" branch -q -D "$branch" && echo "deleted branch $branch" >&2
    else
        echo "kept branch $branch: commits not in the PR" >&2
    fi
fi

bwt=$(wt_of "$base")
if [ -n "$bwt" ]; then
    git -C "$bwt" pull -q --ff-only -p
else
    git -C "$primary" fetch -q -p origin "$base:$base"
fi
git -C "$primary" log -1 --format='%s%n%b' "origin/$base"
