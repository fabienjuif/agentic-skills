# agentic-skills

A personal collection of reusable [Claude Code](https://claude.com/claude-code) skills, packaged
as an installable plugin. The goal: write a skill once, use it across every project.

## What's inside

This repo is a **plugin marketplace** holding a single bundle plugin, `fabien-skills`:

| Skill           | What it does                                                                                                                        |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `make-plan`     | Produce a durable, resumable plan as a `docs/plans/<name>/` directory (so a fresh session or a human can pick the work up cold).    |
| `fix-stale-doc` | Full-repo documentation sweep — fans out sub-agents to fix stale claims, remove duplication, and compact verbose prose, per module. |
| `catch-up`      | Personal daily catch-up dashboard — Slack messages you're involved in, Jira tickets assigned/unassigned, and open PRs in your repos. Self-configures on first run. |
| `capture-docs`  | At session end, captures what was learned into the repo's docs so future sessions start cheaper. Updates both human and AI-facing docs. |
| `pr-review`     | Review a PR's diff and either print findings locally (default) or post them as one consolidated, graded (1–5), severity-grouped comment. Wraps `/code-review`, re-reads the previous review for continuity, and collapses the prior pushed review into a `<details>` summary. |

More skills get added to the same `fabien-skills` plugin over time.

## Install

From within Claude Code, add this repo as a marketplace, then install the plugin:

```
/plugin marketplace add fabienjuif/agentic-skills
/plugin install fabien-skills@agentic-skills
```

To develop locally against a checkout instead of GitHub:

```
/plugin marketplace add /home/fabien/repos/agentic-skills
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
│           └── pr-review/
│               └── SKILL.md
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
