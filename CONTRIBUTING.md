# Contributing

Thanks for helping out. The full agent-facing conventions live in [CLAUDE.md](./CLAUDE.md); this
is the short human version.

## Adding or editing a skill

1. Create or edit `plugins/fabien-skills/skills/<name>/SKILL.md`. The YAML frontmatter needs
   `name` and `description`; the description is what Claude matches on to decide when to invoke
   the skill, so make it trigger-rich (list the phrases a user would say).
2. Keep it portable: no assumptions about a specific repo, employer, build tooling or paths outside
   this repo. Gate optional tools on "if the project uses it".
3. Add or update the skill's row in the [README table](./README.md#whats-inside), including the
   "Needs" column.
4. Bump `version` in `plugins/fabien-skills/.claude-plugin/plugin.json` (semver).

## Commits

One line, prefixed with a [gitmoji](https://gitmoji.dev) shortcode: `:sparkles: add foo skill`.
Shortcodes, never rendered glyphs. No `Co-Authored-By` trailer.

## License

MIT. Contributions are accepted under the same terms; keep the `LICENSE` year and owner intact.
