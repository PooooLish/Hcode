# Open Source Assessment: Hcode

## Historical rename assessment (preserved)

### Scope

- Change: local identity-only rename of the user-supplied project.
- External code acquisition: none.
- New dependencies: none.
- Network research: not required because no repository, package, or implementation is being selected or reused.

### License and provenance

The supplied project has no root license file. This rename does not establish ownership,
grant redistribution rights, or change license status. Publication remains out of scope.

### Security and maintenance

Existing findings in `docs/read-only-code-analysis.md` remain unchanged. The rename must
not be represented as fixing any security issue. Dependency versions and hashes remain fixed.

### Decision

`greenfield` for the rename mechanics only: perform deterministic local identifier and path
changes without copying, integrating, adapting, cloning, or forking external code.

### Reuse boundary

No external concepts or code are required. Only the existing local project is transformed.

## Professional compact terminal UI assessment (2026-09-01)

| Source | Version/date checked | License | Useful reference | Reuse boundary |
| --- | --- | --- | --- | --- |
| OpenAI Codex CLI | repository main, checked 2026-09-01 | Apache-2.0 | compact terminal-first coding flow and explicit operational state | concepts only; no code/assets copied |
| Google Gemini CLI | repository/docs main, checked 2026-09-01 | Apache-2.0 | configurable loading phrases, status visibility, accessibility, themes, and alternate-buffer behavior | concepts only; no code/assets copied |
| Textual | installed 8.2.5 plus current official docs | MIT | `App.run_test`, `Pilot`, screen-size testing, reactive components, TCSS, and SVG export | use already-installed public APIs only |

Primary sources:

- https://github.com/openai/codex
- https://github.com/google-gemini/gemini-cli
- https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md
- https://textual.textualize.io/guide/testing/
- https://textual.textualize.io/guide/styles/
- https://textual.textualize.io/guide/reactivity/
- https://github.com/Textualize/textual

Decision: `reference`. Hcode keeps its current Python/Textual architecture and
implements the approved design locally. No repository is cloned, no external
source or asset is copied, no package is installed, and no dependency or
license obligation changes.
