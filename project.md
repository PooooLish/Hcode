# Project: Hcode

## Status

active

## Goal

Develop Hcode as a terminal coding Agent with reviewable source, reproducible tests, explicit safety boundaries, and measurable capability evaluation.

## Constraints

- Keep source, tests, documentation, and generated state inside this project.
- Never commit real credentials, local provider configuration, logs, caches, or generated runtime output.
- Do not claim production isolation while the Windows sandbox backend is missing.
- Publish and redistribute the project only under the user-selected MIT License.

## Acceptance Criteria

- Hcode is managed by an independent Git repository on branch `main`.
- The repository contains accurate onboarding, contribution, security, changelog, evaluation, and CI documentation.
- Local configuration and generated state remain ignored and absent from Git history.
- The active Windows/Python 3.11 test suite passes after repository preparation.
- A root MIT license and matching package metadata are present before public push.

## Decisions

- Hcode/hcode is the only active project, package, CLI, configuration, and environment identity.
- The project repository is `git@github.com:PooooLish/Hcode.git` on branch `main`.
- Local configuration, credentials, logs, temporary files, caches, and generated outputs must remain untracked.
- API credentials are loaded only from environment variables.
- GitHub Actions use official GitHub actions pinned to immutable commit SHAs.
- The user selected the MIT License on 2026-09-02; copyright is attributed to `PooooLish`.

## Progress

- Imported and renamed the original Python project to Hcode.
- Removed repeated advertising headers without changing runtime behavior.
- Repaired the OpenAI-compatible stream termination path and verified it with a minimal real-provider test.
- Added a compact Textual terminal UI and regression coverage.
- Prepared a dedicated Python 3.11 environment and dependency lock file.
- Added code-flow, read-only analysis, environment, evaluation, contribution, security, and CI documentation.
- Initialized an independent local Git repository and configured the GitHub remote.
- Added the MIT License and matching public package metadata.

## Next Action

1. Push `main` to the public GitHub repository.
2. Confirm the first GitHub Actions run on Windows and Linux.
3. Begin the security-remediation and Agent-evaluation milestones documented in `SECURITY.md` and `docs/evaluation-plan.md`.

## Blockers

- Windows currently has no OS-level sandbox backend.
- Native Linux behavior and the GitHub Actions matrix remain unverified until CI runs.

## Verification

- Previous complete active-suite result: `739 passed, 3 skipped` on Windows with Python 3.11.
- Previous dependency check: `pip check` exited 0 with no broken requirements.
- Previous guarded TUI smoke: mounted the real app without constructing a provider client or opening an external socket.
- Git remote inspection on 2026-09-02: repository exists, is public, and has no branch or existing commit.
- Pre-commit scan: no ignored runtime/configuration path, private-key block, OpenAI-style token, or bearer token was staged.
- Documentation gate after repository preparation: all local Markdown link targets exist; both YAML files parse; `config.example.yaml` passes Hcode's configuration validator.
- Fresh dependency and CLI gate after all functional files: `pip check` and `python -B -m hcode --help` exited 0.
- Fresh complete active suite after repository preparation: `739 passed, 3 skipped in 40.48s` with exit code 0 on Windows/Python 3.11.
- GitHub Actions has not run yet because the initial public push is pending.
- License gate resolved on 2026-09-02: root MIT text, README notice, and PEP 621 license metadata added.
- Fresh post-license local gate: MIT text, package metadata, Markdown links, workflow YAML, and example configuration passed static validation; `pip check` and CLI help exited 0; the complete active suite passed `739 passed, 3 skipped in 40.26s` on Windows/Python 3.11.
