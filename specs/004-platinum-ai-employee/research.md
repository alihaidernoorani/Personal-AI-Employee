# Research: Platinum Tier Personal AI Employee

**Feature**: `004-platinum-ai-employee`
**Date**: 2026-06-27
**Phase**: Phase 0 (all NEEDS CLARIFICATION resolved)

---

## Decision 1: Vault Sync Mechanism

**Decision**: Syncthing

**Rationale**:
- Folder-level Send-Only / Receive-Only modes enforce the Cloud/Local authority boundary by architectural policy, not by code convention — the cloud VM physically cannot overwrite `Dashboard.md`, `Done/`, `Approved/`, or `Rejected/` even if a bug attempts it.
- Sub-second propagation (inotify on Linux) easily meets the 60-second SLA; typical latency is 2–5 seconds.
- `.stignore` (gitignore syntax) provides simple, auditable exclusion of `.env` and credential files.
- Partition buffering is built-in — changes queue on disk and replay automatically on reconnect; no data loss during network outages.
- Headless daemon + REST API enables fully automated setup after one-time device ID exchange.

**Alternatives considered**:

| Option | Rejected Because |
|--------|-----------------|
| rsync over SSH (cron 30s) | Two-pass bidirectional creates race conditions; last-write-wins has no conflict handling; missed cron runs = silent data loss |
| rclone bisync | Cannot enforce folder-level authority without complex filter scripts; edge-case data loss risks on interrupted syncs |
| Git + auto-commit cron | Merge conflicts require manual resolution; history growth overhead; wrong paradigm for operational state |
| Unison | Both machines must run identical version — cross-OS packaging fragility makes automation brittle |

**Known constraint**: Syncthing's inotify does not work on WSL2's `/mnt/c` NTFS mount. The vault must either (a) live inside WSL2's native filesystem (`~/vault/`) and be accessed by Obsidian via WSL path mapping, or (b) Syncthing on Windows-native (not WSL2) syncs the NTFS vault. Option (b) is preferred for Obsidian compatibility — Syncthing.exe on Windows + Syncthing daemon on Linux cloud VM.

---

## Decision 2: Cloud VM Provider and Specifications

**Decision**: Hetzner CX22 (~€3.79/month / ~$4.10/month)

**Rationale**:
- 4 GB RAM (workload estimate: ~800 MB for 4 Python daemons + Syncthing + overhead), leaving 3.2 GB headroom
- 2 vCPU AMD (sufficient for CPU-light watcher polling)
- 40 GB NVMe SSD (~15 GB estimated use: vault 50 MB + Python venv 200 MB + 90-day logs 5 MB + system overhead)
- EU region (Frankfurt / Nuremberg) — lower latency to likely user location
- Formal 99.9% uptime SLA with credit compensation
- SSH key-only auth enforced by default; no password auth
- Lowest cost among EU providers meeting all requirements

**Minimum acceptable specs** (for budget-constrained deployments):
- 1 GB RAM, 1 vCPU, 20 GB storage (tight; no headroom for log accumulation)
- Hetzner CX11 (~€3.09/month) — 2 GB RAM, 2 vCPU, 20 GB: a reasonable alternative if CX22 is unavailable

**Alternatives considered**:

| Provider | Monthly Cost | RAM | Rejected Because |
|----------|-------------|-----|-----------------|
| Hetzner CX22 | €3.79 | 4 GB | ✅ Selected |
| DigitalOcean $6 Droplet | $6.00 | 1 GB | Only 1 GB RAM — at risk of OOM under load |
| AWS Lightsail $3.50 | $3.50 | 512 MB | Insufficient RAM; no EU free tier |
| Contabo VPS S | €4.50 | 8 GB | Good specs but lower uptime SLA reputation; less established support |
| Oracle Cloud Free | $0 | 1 GB | No EU free-tier region; instances can be reclaimed without notice; Oracle halved free-tier resources June 2026 |

**OS**: Ubuntu 24.04 LTS (5-year support; Python 3.12 in default repos; `python3.13` available via deadsnakes PPA)

---

## Decision 3: Constitution Check Automation Matrix

**Decision**: Tiered automation — 7 principles fully automated, 7 partially automated, 1 manual-only.

**Source**: Live code scan of current repository revealed 3 pre-existing violations to address.

### Automation Matrix

| # | Principle | Automatable | Check Method | FAIL Condition |
|---|-----------|-------------|-------------|----------------|
| I | Production First | NEEDS_MANUAL_REVIEW | Code quality heuristics + human checklist | Placeholder TODOs, `pass` stubs, demo-only paths |
| II | Local First | YES | Scan cloud VM filesystem for `.env`, `*.token`, credential patterns | Any credential file found on cloud VM |
| III | Cloud Worker | PARTIAL | Check `.mcp.json` absent on cloud VM; grep cloud skills for MCP calls | `.mcp.json` exists or MCP tool call found in cloud skill |
| IV | Human In The Loop | YES | Verify `APPROVAL_*.md` logic in `execute-plan` skill; check no skill auto-moves from `Pending_Approval/` to `Approved/` | Missing APPROVAL_* write before any sensitive action |
| V | Vault Driven Architecture | PARTIAL | Grep for socket/HTTP calls between agents; verify no shared memory | Direct inter-agent network call found in code |
| VI | Claim-by-Move | YES | Verify `In_Progress/cloud/` and `In_Progress/local/` exist; check skill code for move-before-process pattern | Missing move before task processing |
| VII | Single Writer Rule | YES | Grep all cloud-side code for writes to `Dashboard.md`, `Done/`, `Approved/`, `Rejected/` | Any write to prohibited paths in cloud agent code |
| VIII | Event Driven | PARTIAL | Grep for `PollingObserver`; verify `time.sleep()` in watcher loops; check no `while True: pass` | `InotifyObserver` without fallback on NTFS path; busy-wait found |
| IX | Modular Design | PARTIAL | Count lines per file (automated); review single-responsibility (manual) | Any file > 300 lines; God Object patterns (manual) |
| X | Agent Skills | YES | Grep watchers for reasoning logic; verify all skills in `.claude/skills/` | Decision logic found in watcher code |
| XI | Observability | YES | Verify `Logs/YYYY-MM-DD.json` written after MCP calls; check audit schema fields | Missing audit log entry for any MCP action |
| XII | Reliability | PARTIAL | Grep for exponential backoff pattern; verify watchdog in orchestrator | Missing retry logic on external calls; watchdog absent |
| XIII | Security | YES | Check `.gitignore` for `.env`; scan vault .md files for token patterns; verify `DRY_RUN=true` in `.env.example` | Secret in vault file; `.env` not gitignored; `DRY_RUN=false` as default |
| XIV | Documentation | PARTIAL | Verify SKILL.md frontmatter present; check each `watchers/` file has module docstring; verify `contracts/` folder present | Missing SKILL.md or docstring on any component |
| XV | Code Quality | PARTIAL | Count lines per file (automated); SOLID/DI quality (manual review) | File > 300 lines (automated); poor cohesion (manual) |

### Pre-existing Violations (found by live scan)

These must be fixed before the `constitution-check` skill can report PASS:

| Violation | File | Principle | Finding |
|-----------|------|-----------|---------|
| File too large | `mcp-servers/odoo-mcp/server.py` | XV | 636 lines — exceeds 300-line limit |
| File too large | `mcp-servers/social-mcp/server.py` | XV | 515 lines — exceeds 300-line limit |
| File too large | `watchers/gmail_api_watcher.py` | VIII/XV | 322 lines — exceeds 300-line limit |

**Remediation**: Split each file into logical sub-modules before running `constitution-check` in Phase 4. These splits are tracked as tasks in `tasks.md`.

---

## Decision 4: Stale Task Recovery Implementation

**Decision**: `os.stat().st_mtime` polling with configurable timeout.

**Rationale**: No additional library needed; Python's `os.stat()` returns modification time which is set when the file is moved into `In_Progress/<agent>/`. A file in `In_Progress/cloud/` that hasn't been modified in `STALE_TASK_TIMEOUT_SECONDS` seconds is treated as abandoned.

**Implementation**:
```python
def scan_for_stale_tasks(in_progress_path: Path, threshold_seconds: int) -> list[Path]:
    stale = []
    for task_file in in_progress_path.iterdir():
        age = time.time() - task_file.stat().st_mtime
        if age > threshold_seconds:
            stale.append(task_file)
    return stale
```

Default timeout: 600 seconds (10 minutes). Configurable via `STALE_TASK_TIMEOUT_SECONDS` in `.env`.

---

## Decision 5: `In_Progress/` Rename Migration

**Decision**: Rename `In_Progress/local_agent/` to `In_Progress/local/` as part of Phase 0.

**Rationale**: Spec uses `In_Progress/local/` and `In_Progress/cloud/`. Migration needed at Gold → Platinum transition.

**Migration procedure** (must run with no tasks in progress):
1. Verify `In_Progress/local_agent/` is empty
2. Rename: `mv In_Progress/local_agent/ In_Progress/local/`
3. Update all skill references: `sed -i 's|In_Progress/local_agent|In_Progress/local|g'` on all `.md` skill files
4. Update `orchestrator.py` path reference
5. Update `Dashboard.md` to reflect new path

**Risk**: If tasks are in progress during migration, they will be stranded. Mitigate by performing migration during a maintenance window or when `In_Progress/local_agent/` is confirmed empty.
