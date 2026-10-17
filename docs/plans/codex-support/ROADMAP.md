# Roadmap

1. **Port instructions and configuration.** Update affected `SKILL.md` files and add the root
   `AGENTS.md` entry point. Exit: host-specific tools have fallbacks, config lookup preserves
   legacy settings, and generated plans are discoverable by both hosts.
2. **Document and version.** Update README, contributing guidance, compatibility docs, and the
   plugin version. Exit: one documented install path per host and one shared skill tree.
3. **Validate and publish.** Check metadata, native Codex loading, representative isolated
   scenarios, and Claude plugin validation. Review the final diff and open one PR. Exit: checks
   and their limitations recorded, branch pushed, PR open.

Dependencies: 1 → 2 → 3. Implementation, documentation, and validation are complete.
Delivery is the pull request for this branch; merge and release remain outside this task.
