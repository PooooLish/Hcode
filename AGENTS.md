# AGENTS.md

## Scope

- Work only inside this project unless the user explicitly expands the scope.
- Follow the workspace root `../../AGENTS.md`; this file may only tighten it.
- Keep project code, tests, documentation, and generated state inside this
  project.

## Safety

- Do not store or print real secrets.
- Do not delete files, install dependencies, or perform Git publishing actions
  without explicit approval.
- Keep generated outputs in `outputs/`, temporary files in `tmp/`, and logs in
  `logs/`.

## Workflow

1. Read `project.md`, `README.md`, and the relevant source files.
2. Complete `docs/open-source-assessment.md` before implementation. Use
   read-only research first; cloning, downloads, dependency installation, code
   copying, and forking require explicit approval.
3. State a short plan appropriate to the change.
4. Make small, reviewable edits.
5. Run focused verification.
6. Before changing Agents, update `Status`, `Decisions`, `Progress`,
   `Next Action`, `Blockers`, and `Verification` in `project.md`.
7. Run `python -B capabilities/tools/workspace.py handoff hcode`
   from the workspace root and review the packet against Git state.
8. Review the diff and report remaining risks.

## Project

- `hcode`
