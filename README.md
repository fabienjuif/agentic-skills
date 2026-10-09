# agentic-skills

A personal collection of reusable [Claude Code](https://claude.com/claude-code) skills, packaged
as an installable plugin. The goal: write a skill once, use it across every project.

## What's inside

This repo is a **plugin marketplace** holding a single bundle plugin, `fabien-skills`:

| Skill           | What it does                                                                                                                        |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `make-plan`     | Produce a durable, resumable plan as a `docs/plans/<name>/` directory (so a fresh session or a human can pick the work up cold).    |
| `fix-stale-doc` | Full-repo documentation sweep — fans out sub-agents to fix stale claims, remove duplication, and compact verbose prose, per module. A final hardening pass re-reads every `⚠️` flag the sweep raised and resolves the high-confidence ones, so only genuine judgment calls reach the human. |
| `catch-up`      | Personal daily catch-up dashboard — Slack messages you're involved in, Jira tickets assigned/unassigned, and open PRs in your repos. Self-configures on first run. |
| `capture-docs`  | At session end, captures what was learned into the repo's docs so future sessions start cheaper. Updates both human and AI-facing docs. |
| `pr-review`     | Review a PR's diff and either print findings locally (default) or post them as one consolidated, graded (1–5), severity-grouped comment. Wraps `/code-review`, re-reads the previous review for continuity, and collapses the prior pushed review into a `<details>` summary. |
| `idea`          | Quickly capture a project idea into `docs/IDEA.md` — a "what next" backlog (technical or not). Warns when the file bloats; `/idea unbloat` runs an interactive prune where surviving ideas earn a `survived ×N` marker; `/idea sort` is an interactive triage where you assign `[now]`/`[next]`/`[later]` buckets (seeded by that marker) and the file is reordered to match. Promote to a plan with `make-plan` later. |
| `gitmoji`       | Commit the current changes with a [gitmoji](https://gitmoji.dev)-prefixed message, following the repo's own commit format. Lazy by design: the skill body carries only the dozen common gitmojis, and the full list sits in a sibling `gitmojis.md` that is grepped by keyword only when none of them fits. Fast too: git status, staged stat and recent log are injected at load, so the usual run is a single commit call. |
| `tmp-cleanup`   | Free RAM by deleting stale (default >3h) top-level entries from `/tmp`, which is tmpfs on many Linux systems. Dry-run by default via a bundled `tmp-cleanup.sh` (Linux and macOS, protects live locks, sockets and agent session dirs); the skill triggers on "free memory", "clean up" or noticed memory pressure. |

More skills get added to the same `fabien-skills` plugin over time.

## Install

From within Claude Code, add this repo as a marketplace, then install the plugin:

```
/plugin marketplace add fabienjuif/agentic-skills
/plugin install fabien-skills@agentic-skills
```

To develop locally against a checkout instead of GitHub:

```
/plugin marketplace add <path-to-your-checkout>
/plugin install fabien-skills@agentic-skills
```

Once installed, the skills are available in any project — e.g. type `/make-plan` or just ask
Claude to "create a plan".

## Layout

```
agentic-skills/
├── .claude-plugin/
│   └── marketplace.json        # marketplace manifest (lists the plugin)
├── plugins/
│   └── fabien-skills/
│       ├── .claude-plugin/
│       │   └── plugin.json      # plugin manifest
│       └── skills/
│           ├── make-plan/
│           │   └── SKILL.md
│           ├── fix-stale-doc/
│           │   └── SKILL.md
│           ├── catch-up/
│           │   └── SKILL.md
│           ├── capture-docs/
│           │   └── SKILL.md
│           ├── pr-review/
│           │   └── SKILL.md
│           ├── idea/
│           │   └── SKILL.md
│           ├── gitmoji/
│           │   ├── SKILL.md
│           │   └── gitmojis.md  # full list, read on demand
│           └── tmp-cleanup/
│               ├── SKILL.md
│               └── tmp-cleanup.sh  # dry-run by default, --apply deletes
├── README.md                    # this file (for humans)
├── CLAUDE.md                    # guidance for agents working in this repo
└── LICENSE                      # MIT
```

## Adding a skill

1. Create `plugins/fabien-skills/skills/<name>/SKILL.md` with YAML frontmatter (`name`,
   `description`).
2. Add a row to the table above.
3. Bump `version` in `plugins/fabien-skills/.claude-plugin/plugin.json`.

See [CLAUDE.md](./CLAUDE.md) for conventions (including the gitmoji commit style).

## License

[MIT](./LICENSE) © 2026 Fabien Juif
