# Changelog

## [Unreleased]
### Added
- Strict linting, typing, security scanning, and property tests wired into `make check` and pre-commit hooks.
- Structured logging with error identifiers across CLI utilities and the sample database manager.
- Hypothesis-based regression tests covering CLI parsers and ignore pattern expansion.
- `--dry-run` and `--verbose` flags across CLI commands plus utilities for planning log generation and tree previews.

### Changed
- Sample project models refactored to dataclasses with deterministic timestamps.
- Legacy wrapper scripts simplified to import the shared CLI directly.
- README now documents verification commands, observability practices, and SLO expectations.

### Fixed
- Lint violations throughout the sample assets and wrappers detected by Ruff.
- Consolidated dependency list with pinned tooling for reproducible local runs.
