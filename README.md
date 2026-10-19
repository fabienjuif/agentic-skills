# agentic-skills

[![Latest release](https://img.shields.io/github/v/release/fabienjuif/agentic-skills)](https://github.com/fabienjuif/agentic-skills/releases)
[![License: MIT](https://img.shields.io/github/license/fabienjuif/agentic-skills)](./LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-blueviolet)](https://claude.com/claude-code)

[Claude Code](https://claude.com/claude-code) skills that make sessions resumable and repos
self-documenting. This is Fabien Juif's own toolkit, packaged as an installable plugin marketplace:
write a skill once, use it across every project. It is used daily on both work and personal
projects, which is why every skill stays project-agnostic.

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

Once installed, the skills are available in any project: type `/make-plan` or just ask Claude to
"create a plan".

## Why

Every new agent session starts from zero: it has to rediscover the codebase, the decisions already
made, and the work still open, and that rediscovery costs tokens and time. These skills push that
context into the repo instead. A plan directory keeps multi-step work resumable, an idea backlog
keeps "someday" thoughts out of the way without losing them, and docs capture at session end means
the next session reads the answer instead of re-deriving it. On the review side, `pr-review` keeps
PR threads clean with one comment that updates in place instead of stacking.

## What's inside

This repo is a **plugin marketplace** holding a single bundle plugin, `fabien-skills`:

| Skill           | What it does                                                                                                                              | Needs                                           |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `make-plan`     | Write a non-trivial task down as a `docs/plans/<name>/` directory a fresh session or a human can pick up cold.                             | `git` only                                      |
| `idea`          | Capture a project idea into a `docs/IDEA.md` backlog; prune and prioritize it later with `/idea unbloat` and `/idea sort`.                 | `git` only                                      |
| `capture-docs`  | At session end, write what was learned into human and AI-facing docs so the next session starts cheaper.                                  | `git` only                                      |
| `close-session` | Wrap up in one pass: update tickets, react on Slack threads of merged PRs, open a docs PR, clean scratch data, fast-forward main checkouts. | `git`, `gh`; Linear MCP and Slack MCP optional |
| `fix-stale-doc` | Full-repo documentation sweep that fixes stale claims, removes duplication and compacts prose, one sub-agent per module.                   | `git` only                                      |
| `pr-review`     | Review a PR and post one consolidated comment that updates in place across re-reviews, so the thread stays clean.                           | `gh`                                            |
| `gitmoji`       | Commit the current changes with the one [gitmoji](https://gitmoji.dev) that matches the intent, in the repo's own format. Never pushes.    | `git` only                                      |
| `catch-up`      | Daily dashboard of Slack messages, Jira tickets and open PRs that need you, distilled into one prioritized list. Self-configures on first run. | `gh`, Slack MCP, Jira MCP; each source optional |
| `tmp-cleanup`   | Free RAM by deleting stale entries from `/tmp` (tmpfs on many Linux systems). Dry-run by default.                                         | Linux or macOS                                  |
| `eta`           | ETA of what the agent is doing, in one fixed format (progress bar, clock time, per-step table), using timings learned from your past commands in each repo. | Python 3 (stdlib only)                          |

More skills get added to the same `fabien-skills` plugin over time.

## Releases

Each [release](https://github.com/fabienjuif/agentic-skills/releases) note lists what changed per
skill.

## Layout

```
agentic-skills/
├── .claude-plugin/
│   └── marketplace.json        # marketplace manifest (lists the plugin)
├── plugins/
│   └── fabien-skills/
│       ├── .claude-plugin/
│       │   └── plugin.json      # plugin manifest
│       ├── hooks/
│       │   └── hooks.json       # timing hooks used by the eta skill
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
│           ├── tmp-cleanup/
│           │   ├── SKILL.md
│           │   └── tmp-cleanup.sh  # dry-run by default, --apply deletes
│           ├── eta/
│           │   ├── SKILL.md
│           │   └── eta.py          # renders the ETA block; `hook` mode records timings
│           └── close-session/
│               └── SKILL.md
├── README.md                    # this file (for humans)
├── CONTRIBUTING.md              # how to add or edit a skill
├── CLAUDE.md                    # guidance for agents working in this repo
└── LICENSE                      # MIT
```

## Adding a skill

1. Create `plugins/fabien-skills/skills/<name>/SKILL.md` with YAML frontmatter (`name`,
   `description`).
2. Add a row to the table above.
3. Bump `version` in `plugins/fabien-skills/.claude-plugin/plugin.json`.

See [CONTRIBUTING.md](./CONTRIBUTING.md) and [CLAUDE.md](./CLAUDE.md) for conventions (including
the gitmoji commit style).

## License

[MIT](./LICENSE) © 2026 Fabien Juif
