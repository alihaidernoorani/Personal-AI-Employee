# Research: Bronze Tier Personal AI Employee

**Branch**: `001-bronze-ai-employee` | **Date**: 2026-03-06

---

## R-001: Filesystem Watching on WSL2 NTFS Mounts

**Decision**: Use `watchdog.observers.polling.PollingObserver` (3-second timeout).

**Rationale**: The vault lives on `/mnt/c` (Windows NTFS via WSL2). Linux `inotify`
does not fire for filesystem events on NTFS mounts. `PollingObserver` works by
diffing directory state on each interval, which is reliable across all mount types.
A 3-second interval is imperceptible to a human and negligible on CPU.

**Alternatives considered**:
- `InotifyObserver` (default on Linux) — fails silently on `/mnt/c`; rejected.
- Native Windows `ReadDirectoryChangesW` via `pywin32` — requires Windows Python, not WSL2; rejected.
- Polling with `os.listdir` loop — reinvents watchdog; no benefit; rejected.

---

## R-002: Python Environment Management

**Decision**: `python3 -m venv .venv` at the repo root; activate with `.venv/bin/python`.

**Rationale**: The system Python on WSL2 Ubuntu is "externally managed" (PEP 668)
and rejects `pip install` without `--break-system-packages`. A local `.venv` is
the standard, safe, zero-dependency solution.

**Alternatives considered**:
- `uv` — faster but adds a dependency; acceptable for Silver+; deferred.
- `conda` — heavyweight; not warranted for 2 dependencies; rejected.

**Dependencies (Bronze tier)**:
- `watchdog>=4.0.0` — filesystem monitoring
- `python-dotenv>=1.0.0` — `.env` loading

---

## R-003: Task File Format

**Decision**: Markdown files with YAML frontmatter, stored in `Needs_Action/`.

**Rationale**: Obsidian renders YAML frontmatter natively. Structured frontmatter
allows Claude to parse task metadata programmatically (type, priority, status)
without free-text parsing. Markdown body provides human-readable context.

**Alternatives considered**:
- JSON files — not renderable in Obsidian; rejected.
- Plain `.txt` — no structured metadata; rejected.
- SQLite — violates constitution Principle II (vault as single source of truth); rejected.

**Filename convention**: `FILE_<YYYYMMDDTHHMMSSz>_<stem>.<ext>.md` for watcher-created files;
`DONE_<original>` prefix when moved to Done.

---

## R-004: Agent Skill Architecture

**Decision**: All AI reasoning logic encapsulated in `.claude/skills/process-needs-action/SKILL.md`.

**Rationale**: Constitution Principle I mandates all AI logic in `.claude/skills/`.
SKILL.md provides a structured, version-controlled procedure that Claude Code follows
exactly — analogous to a job description for the AI. This separates perception
(watcher scripts) from reasoning (skills) cleanly.

**Alternatives considered**:
- Logic embedded in watcher scripts — violates Principle I; rejected.
- Separate Python reasoning script invoked by Claude — adds unnecessary indirection; rejected.

---

## R-005: Idempotency Strategy

**Decision**: Track processed Inbox file names in `scripts/processed_inbox.json`.

**Rationale**: Constitution Principle I requires idempotency. On watcher restart,
any file already present in Inbox must not generate a duplicate task. A flat JSON
set of processed filenames is the simplest implementation with near-zero overhead.

**Alternatives considered**:
- Compare Inbox vs Needs_Action file names — fragile if files are renamed; rejected.
- Track by file hash — adds complexity and slower for large files; deferred to Gold tier.

---

## R-006: Secrets Management

**Decision**: `.env` file at repo root, loaded by `python-dotenv`. Gitignored.

**Rationale**: Constitution Principle V mandates no credentials in code or `.md` files.
`python-dotenv` is already in requirements. `DRY_RUN=true` is the default so nothing
external ever fires accidentally during development.

**Alternatives considered**:
- Windows Credential Manager via `keyring` — adds a dependency; deferred to Silver+ for banking credentials.
- OS environment variables only — requires manual export on each session; worse DX; rejected.
