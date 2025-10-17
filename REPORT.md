# Repository Report

## Structure & Dependency Map
- **zscripts/cli.py** – argparse-based CLI front-end calling helpers in `zscripts.utils` and `zscripts.config` to generate log bundles.
- **zscripts/utils.py** – filesystem traversal, ignore pattern handling, and log/tree writers; relies on configuration constants and Python stdlib (`os`, `fnmatch`, `re`).
- **zscripts/config.py** – JSON-backed configuration loader; produces immutable `Config` snapshots and resolved path helpers.
- **sample_project/** – reference workspace exercised by CLI/tests.
- **tests/** – pytest suite covering CLI flows, utils, config semantics, and legacy wrapper shims.
- **Tooling** – `pyproject.toml` defines Ruff, pytest, mypy (strict), and coverage; Makefile wraps lint/type/test commands.

## Key Findings
1. **Extension coverage gap:** `COLLECT_TYPE_EXTENSIONS` and `SINGLE_TYPE_EXTENSIONS` only include `.js` for JavaScript despite the README promising JSX/TypeScript support. The bundled sample project ships `frontend/App.jsx`, yet current collectors skip it; `.ts`/`.tsx` are also absent, undermining advertised cross-stack coverage.
2. **Doc drift:** README markets TypeScript handling, but implementation/tests never exercise those extensions, so regressions could go unnoticed.
3. **Legacy wrappers:** Modules under `zscripts/all*` import the CLI, so CLI regressions cascade into older entry points. Any change to extension sets must consider these wrappers to avoid surprise behavior changes.

## Risk Notes
- CLI path resolution relies on filesystem state; failures to create output directories surface as `OSError` -> exit code 1. Extension updates must keep default behaviour backward compatible (e.g., no narrowing of existing globs).
- Expanding extension lists increases file coverage; ensure ignore patterns still prevent runaway traversal of generated assets (e.g., build outputs).
- Sample project mutations affect multiple tests; need to update fixtures carefully to keep expectations accurate.

## Test Posture
- Pytest suite (40 tests) covers config immutability, CLI commands, ignore handling, and legacy wrappers. No direct assertions for JSX/TypeScript capture.
- Property-based fuzz cases exist for type parsing and skip-dir expansion; good defensive coverage, but file-type collection lacks regression tests.

## CI/CD Posture
- No GitHub Actions workflows detected; validation relies on manual `make` targets (fmt/lint/type/security/test) documented in README.
- Noxfile present but not wired into automated CI.

## Selected Update Modes
- **Full-System Polish** – Align advertised capabilities (JSX/TypeScript support) with actual behaviour and documentation.
- **Test & Verify** – Add regression tests that cover the expanded extension handling to guard future changes.

## Verification
- `pytest -q` (42 passed) – validates CLI/util changes with new JavaScript variant coverage.
