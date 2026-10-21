---
name: merge
description: Squash-merge a pull request on GitHub or Forgejo/Gitea end to end - gate it (required checks, plus an optional local command such as "make ci" on the exact head), merge with the repo's commit format pinned to the gated sha, delete the remote branch, remove its local worktree and branch, fast-forward the base, then offer to check the other open PRs for conflicts. Use when the user says "/merge <n>", "/squash <n>", "merge 27", "squash merge PR N", "land this PR".
---

# /merge: squash-merge a PR

Argument: the PR number(s); several merge one after the other. Merging is what the user asked for,
so do it without another confirmation once the gate passes. Scripts are next to this file
(`<skill dir>`), run from the repo's primary checkout. The forge comes from `origin`: a host `gh`
is logged in to is GitHub, any other is Forgejo/Gitea (token: `FORGEJO_TOKEN`, else
`~/.claude/.env`, else the git credential helper; never print it).

## Config

Optional `.claude/.config/merge.json`, walking up from the cwd to `$HOME` (first match wins):

```jsonc
{
  "gate": "make ci",      // local command run on the PR head before merging; default none
  "subject": "title",     // "title" (trailing "(#N)" stripped) or "title (#N)"
  "body": "empty"         // "empty" or "commits" (one line per commit subject)
}
```

Precedence for each: the repo's own agent docs or CONTRIBUTING (a squash format, a merge gate they
name), then this config, then the repo's history: in `git log -10 --format='%s%x00%b'
origin/<base>`, do the squash subjects carry `(#N)`, are the bodies empty? With no signal at all:
the PR title without `(#N)`, empty body.

## Steps

1. `<skill dir>/pr.sh <n>`: keep `title`, `head_ref`, `base_ref`; `head_ref` is gone after the
   merge on Forgejo.
2. `sha=$(<skill dir>/gate.sh <n> [gate command...])` in the foreground. On GitHub it waits for
   the required checks (all checks when none are required); Forgejo checks are not read, only the
   local command gates there. The command runs in a throwaway worktree of the head, skipped when
   every changed file is docs or agent config (`*.md`, `docs/`, `.claude/`). On a failure, do not
   merge: report the failing step and offer to fix it on the branch.
3. `<skill dir>/merge.sh <n> "$sha" "<subject>" ["<body>"]`. It refuses a head that moved past
   `$sha` (re-run the gate), a closed PR and, on Forgejo, a conflicting one. Right after another
   merge Forgejo reports conflicts until it rechecks: `git merge-tree --write-tree
   origin/<base> FETCH_HEAD` after `git fetch origin refs/pull/<n>/head` tells a real one. On a
   real conflict, say so and offer to merge `origin/<base>` into the branch. Never pass `--admin`
   or bypass a review requirement; report it. Exit 3 means GitHub queued it (merge queue or
   auto-merge): report that and skip step 4 until it lands.
4. `<skill dir>/cleanup.sh <head_ref> "$sha" <base_ref>`: removes the branch's worktree and local
   branch, fast-forwards the base, prints the base's last commit. A dirty worktree or a branch with
   commits past `$sha` is kept and reported. Check the printed commit matches the chosen format.
5. Report the PR link and the commit subject.
6. Offer to check the other open PRs for conflicts with the new base:
   `<skill dir>/conflicts.sh` (on GitHub, only your own).
