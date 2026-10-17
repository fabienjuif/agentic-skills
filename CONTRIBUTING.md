# Contributing

Thanks for helping out. The full agent-facing conventions live in [CLAUDE.md](./CLAUDE.md); this
is the short human version.

## Adding or editing a skill

1. Create or edit `plugins/fabien-skills/skills/<name>/SKILL.md`. The YAML frontmatter needs
   `name` and `description`; the description is what the agent matches on to decide when to invoke
   the skill, so make it trigger-rich (list the phrases a user would say).
2. Keep it portable: no assumptions about a specific repo, employer, build tooling or paths outside
   this repo. Gate optional tools on "if the project uses it".
3. Add or update the skill's row in the [README table](./README.md#whats-inside), including the
   "Needs" column.
4. Bump `version` in `plugins/fabien-skills/.claude-plugin/plugin.json` (semver).

## Supporting both hosts

Keep one shared skill implementation. Prefer capabilities over fixed tool names: ask with an
available question tool or conversation, delegate with available subagent tools, and resolve
bundled resources relative to the loaded `SKILL.md`. Do not assume shell snippets were executed
when a skill was loaded. Host-specific frontmatter may be retained as a hint, but the workflow
must also work without it.

Keep existing configs readable when introducing a new location. See [Codex compatibility](docs/codex.md)
for shared config precedence, instruction entry points, and validation expectations. Optional
Slack, Jira, and Linear integrations must remain optional on both hosts.

## Commits

One line, prefixed with a [gitmoji](https://gitmoji.dev) shortcode: `:sparkles: add foo skill`.
Shortcodes, never rendered glyphs. No `Co-Authored-By` trailer.

## License

MIT. Contributions are accepted under the same terms; keep the `LICENSE` year and owner intact.
