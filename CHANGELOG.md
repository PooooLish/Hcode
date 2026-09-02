# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) 的组织方式。正式发布版本后再声明语义化版本兼容性。

## [Unreleased]

### Added

- Public-repository documentation, example configuration, CI workflow, security policy, and Agent evaluation plan.
- MIT license and package repository metadata.

## [0.2.0] - 2026-09-01

### Added

- Compact Textual terminal UI with responsive status, help, completion, and tool presentation.
- TUI capture script and focused visual regression coverage.

### Changed

- Project, package, command, configuration directory, and environment identity renamed to Hcode/hcode.

### Fixed

- OpenAI-compatible streams now emit `StreamEnd` for normal and usage-only terminal chunks.
