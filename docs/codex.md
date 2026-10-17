# Codex compatibility

The nine skills in `plugins/fabien-skills/skills/` are shared by Claude Code and Codex.
Install the bundle using the [README instructions](../README.md#install). Codex accepts the
existing Claude-compatible plugin manifest and marketplace; retaining them avoids duplicate
metadata and preserves Claude Code installs. See OpenAI's [plugin packaging guidance](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work).

## Standalone skills

If your Codex installation lacks plugin commands, install individual skill directories instead.
For local development, Codex supports symlinked skills under `~/.agents/skills/` or a project's
`.agents/skills/`. For example, substitute your checkout's absolute path:

```bash
mkdir -p "$HOME/.agents/skills"
ln -s /absolute/path/to/agentic-skills/plugins/fabien-skills/skills/make-plan \
  "$HOME/.agents/skills/make-plan"
```

Repeat for the skills you want; link the whole directory so adjacent scripts and references remain
available. Keep the checkout in place. If a destination already exists, inspect it before replacing
anything. Use either the plugin or standalone installation for a given skill to avoid duplicate
entries. Restart Codex if the new skill does not appear. See [skill discovery](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills).

## Shared configuration

`catch-up` and `close-session` read the same config regardless of host. New configs use
`.agents/.config/catch-up.json` and `.agents/.config/close-session.json`.

1. An explicit `CATCH_UP_CONFIG` or `CLOSE_SESSION_CONFIG` environment variable selects that exact file.
2. Otherwise search from the working directory upward. At each directory, check `.agents/.config/`
   first, then the legacy `.claude/.config/`. The nearest directory wins; files are never merged.
3. Inside the user's home directory, stop at home. Outside home, search to the filesystem root,
   then check the two home locations as a fallback.

A project-local legacy config therefore still overrides a home-level shared config. Invalid or
unreadable selected files are reported, not bypassed or overwritten; a missing explicit override
is also an error. Reconfiguration updates the selected file, including a legacy file. Nothing
is migrated automatically. New configurations default to the shared home location unless the user
requests project scope. `close-session` does not create configuration unless asked.

The file schemas and setup questions remain in the respective skills. Connected Slack, Jira,
Linear, and GitHub tools are discovered by capability; installing this plugin does not configure
or authenticate those services.

## Agent instructions and host tools

This repo's `AGENTS.md` instructs Codex to read the canonical `CLAUDE.md`. Newly generated plans
use canonical `AGENTS.md` instructions plus a thin `CLAUDE.md` pointer. Existing plans retain their
established canonical file. Either entry point must reach the same instructions.

Skills use available question and delegation tools, with conversation and sequential work as
fallbacks. `pr-review` can analyze the diff directly without `/code-review`. `gitmoji` gathers
missing Git context explicitly and resolves its reference file beside its loaded `SKILL.md`.
Claude-specific permission metadata is a hint for that host, not a Codex permission grant.

## Validation

When changing compatibility behavior:

- Validate both JSON manifests and all skill frontmatter; preserve packaged resource paths.
- Use the installed Codex runtime to read the checkout's marketplace and verify all nine skills
  resolve to files in that checkout, rather than relying on a previously installed cache.
- Check a separately copied package with a unique identity to confirm discovery without an
  existing installation of that identity. This is a loading check, not an installation test.
- Exercise changed instructions in isolated fixtures: staged Git changes, config precedence,
  absent integrations, and question/delegation fallbacks as applicable.
- Validate the Claude plugin with `claude plugin validate` when available.

The CLI install command syntax was checked with Codex 0.162.1. Detailed outcomes and limitations
are recorded in the [implementation plan](plans/codex-support/README.md). Live account mutations
and the desktop installation UI require separate integration checks.
