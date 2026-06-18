# CLAUDE.md — agentic-skills

Guidance for any agent working in this repo. Read this before editing.

## What this repo is

A Claude Code **plugin marketplace** that ships one bundle plugin, `fabien-skills`, containing
reusable skills. It is meant to be installed across many projects, so everything here must stay
**project-agnostic** — no references to a specific employer/codebase, no hardcoded paths outside
this repo.

## Structure (don't move these)

- `.claude-plugin/marketplace.json` — marketplace manifest. Lists each plugin and its `source`
  (a `directory` source pointing at `plugins/<plugin>`).
- `plugins/fabien-skills/.claude-plugin/plugin.json` — the plugin manifest (`name`, `description`,
  `version`, `author`, `license`).
- `plugins/fabien-skills/skills/<name>/SKILL.md` — one directory per skill. Each `SKILL.md` needs
  YAML frontmatter with `name` and `description` (the `description` is what the model matches on to
  decide when to invoke the skill — make it trigger-rich).

## Adding or editing a skill

1. Create/edit `plugins/fabien-skills/skills/<name>/SKILL.md`.
2. Keep skills portable: no assumptions about a particular repo's layout, build tooling, or
   conventions. Where a skill suggests a tool (e.g. `prettier`), gate it on "if the project uses
   it".
3. Update the skill table in `README.md`.
4. Bump `version` in `plugins/fabien-skills/.claude-plugin/plugin.json` (semver).

## Commit convention — gitmoji (shortcode form)

Use [gitmoji](https://gitmoji.dev) **shortcodes**, not Unicode emoji. Format:

```
:emoji: <short, lowercase summary>
```

Use `:tada:` for the initial commit. Always the shortcode (`:sparkles:`), never the rendered
glyph. Common ones:

| Shortcode      | Use for                          |
| -------------- | -------------------------------- |
| `:tada:`       | initial commit                   |
| `:sparkles:`   | new skill / feature              |
| `:memo:`       | docs                             |
| `:recycle:`    | refactor                         |
| `:bug:`        | bug fix                          |
| `:wrench:`     | config / manifest changes        |
| `:fire:`       | removing code or files           |

Prefer single-line commit messages.

## License

MIT. Keep the `LICENSE` year/owner intact when adding files.
