---
name: make-plan
description: Produce a self-contained plan directory with scope, roadmap, agent instructions, and session changelogs so a fresh agent or human can resume the work. Use when asked to "create a plan", "plan this out", or before implementing multi-step or architectural work.
---

# /make-plan — write a durable, resumable plan

Plans are **directories**, not single files. A good plan lets both a **fresh agent
session** and a **human** dig in cold and know exactly what was decided, why, and what's next.

## When to use

- The user asks to "create a plan", "plan this", "design this out".
- Before implementing anything non-trivial (3+ steps or an architectural decision).
- Skip for trivial one-line / config tweaks where the overhead isn't justified.

## Process

### 1. Investigate first — don't plan from assumptions

Ground the plan in the actual codebase. Use the host's available subagent tools for independent
research in parallel; if delegation is unavailable, investigate directly. Find the
real integration points, existing patterns, and prior art the user mentions. Cite concrete file
paths in the plan — a plan full of guesses is worse than no plan.

### 2. Resolve the decisions only the user can make

Use the host's available question tool, or ask conversationally, for choices that materially
change the plan (approach, scope, surface).
Don't ask about things you can verify yourself or where there's an obvious default — decide those
and state them. Lock the answers into `PROMPT.md`.

### 3. Create the plan directory

Pick a short kebab-case name. Create `docs/plans/<name>/` with **at least** these files:

| File                       | Audience      | Holds                                                                                                                                                                                                            |
| -------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PROMPT.md`                | scope guard   | The **frozen** original request + the decisions locked with the user + explicit **in/out of scope**. The anti-drift anchor. Amend only if scope truly changes (note it in a changelog).                          |
| `README.md`                | the human     | What this is, why it exists, the decision "in one breath", an architecture-at-a-glance diagram, a "where to go next" table, and a **Grounding** table of real file paths.                                        |
| `AGENTS.md`                | future agents | Canonical agent context: reading order, load-bearing decisions ("don't relitigate without reason"), delegation rules, and the changelog rule. Codex discovers this when working in the directory. |
| `CLAUDE.md`                | Claude Code   | A short instruction to read the adjacent `AGENTS.md`; keep shared rules in one place. |
| `ROADMAP.md`               | implementer   | Phased build. Each phase: concrete files to touch + an explicit **exit condition**. Sequence so the lowest-risk / no-dependency value ships first. End with a dependency graph + status.                         |
| `changelogs/<datetime>.md` | history       | One file per working session (never rewrite old ones). What changed, decisions made, open questions, the next step.                                                                                              |

When extending an existing plan, preserve its established instruction layout. Ensure both
`AGENTS.md` and `CLAUDE.md` lead to the canonical instructions without circular pointers.

Add more docs when the task warrants (e.g. `ARCHITECTURE.md`, `API-REALITY.md`, `QUESTIONS.md`,
`METRICS.md`).

Get the changelog timestamp with: `date +%Y-%m-%dT%H-%M-%S`.

### 4. Style

- Be concrete and grounded: real file paths, real function names, verified facts over prose.
- Lead with the recommendation; mark decisions that shouldn't be relitigated.
- Use Mermaid diagrams for architecture and dependency graphs.
- Keep it honest: flag open questions and blockers explicitly rather than papering over them.

### 5. Post-write

- Format the new Markdown if the project uses a formatter (e.g.
  `npx prettier --write "docs/plans/<name>/**/*.md"`).
- For a planning-only request, the plan is the deliverable; offer to start implementation after
  review. If the user already requested implementation, continue into the first phase.

## Resuming a plan

A fresh session continues a plan by reading `PROMPT.md` → the canonical agent instructions →
`ROADMAP.md` → the latest `changelogs/` entry, then appending a new changelog as it works.
