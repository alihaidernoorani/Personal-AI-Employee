---
id: "005"
title: Cloud VM Provider Recommendation
stage: general
date: 2026-06-27
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 003-gold-ai-employee
user: Ali Haider Noorani
command: research cloud VM providers for Platinum-tier AI Employee
labels: ["cloud", "infrastructure", "platinum", "research"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - history/prompts/general/005-cloud-vm-provider-recommendation.general.prompt.md
tests:
  - none
---

## Prompt

Research and recommend a cloud VM provider and minimum specs for this use case:

**Context**: A Platinum-tier AI Employee needs a 24/7 cloud VM running:
- Python 3.13+ environment
- 3-4 Python daemon processes (watchers: Gmail, filesystem signals, stale-task monitor, heartbeat writer)
- rsync/rclone/Syncthing process for vault sync
- No web server, no database, no GPU, no large ML models
- Must be always-on; uptime target 99.5%

**Requirements**:
- Minimum RAM to run the 4 Python daemons + sync process without OOM
- Minimum storage: vault (~1,000 markdown files, ~50MB), logs (90 days), Python venv (~200MB), total estimate
- OS: Ubuntu 24.04 LTS preferred
- Must support SSH key-based auth only (no password auth)
- Monthly cost: minimize, prefer < $10/month
- Geographic preference: EU (user likely in Pakistan/UK timezone)

**Evaluate these providers at their cheapest tier**:
1. Hetzner Cloud (CX11 or CX21)
2. DigitalOcean Droplet (Basic $4-6/month)
3. AWS Lightsail ($3.50-5/month)
4. Contabo VPS S (€4.50/month)
5. Oracle Cloud Free Tier

For each: monthly cost, RAM, CPU, storage, networking, uptime SLA, and SSH-only auth support.

Give a final recommendation. Include minimum recommended specs (RAM, CPU, storage). Report in under 300 words.

## Response snapshot

Researched all five providers via web search (June 2026 pricing). Key findings:

- Hetzner CX11/CX21 are deprecated; replaced by CX22 at €3.79/month (2 vCPU, 4 GB RAM, 40 GB NVMe).
- DigitalOcean Basic $6: 1 vCPU, 1 GB RAM, 25 GB SSD — meets bare minimum only.
- AWS Lightsail $5: 1 vCPU, 1 GB RAM, 40 GB SSD — same concern.
- Contabo VPS S: €4.50, 4 vCPU, 8 GB RAM, 100 GB NVMe — raw specs good but poor reliability reputation and no EU-specific free-tier.
- Oracle Cloud Free: $0, now halved (2 OCPU, 12 GB RAM for free tier as of June 2026), no EU free-tier region, no formal SLA — instances can be reclaimed.

Workload RAM estimate: ~800 MB total; 1 GB is risky, 2 GB is safe minimum.
Storage estimate: ~8 GB minimum, 20 GB recommended.

**Recommendation: Hetzner CX22 at €3.79/month** — EU region, 4 GB RAM, 40 GB NVMe, formal 99.9% SLA with credit compensation, SSH key auth standard. Best price-to-reliability for this workload.

Minimum specs: 1 GB RAM minimum (2 GB recommended), 1 vCPU, 10 GB storage (20 GB recommended).

## Outcome

- Impact: Platinum-tier VM hosting decision documented with provider comparison and cost analysis
- Tests: none — research task
- Files: history/prompts/general/005-cloud-vm-provider-recommendation.general.prompt.md
- Next prompts: provision Hetzner CX22, configure rclone vault sync, set up systemd units for Python watchers
- Reflection: Oracle Free Tier is unsuitable for production always-on workloads due to June 2026 resource halving and no EU free region; Hetzner is the clear winner at this price point

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment: evaluate ARM64 Hetzner CAX11 (2 ARM vCPU, 4 GB, €3.29/month) as potential cheaper alternative if Python 3.13 ARM support is confirmed
