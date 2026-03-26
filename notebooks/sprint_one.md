# Sprint 1 Review — NCR Atleos Log Aggregation Platform

> Date: 2026-03-22 | Sprint goal: Schema · Synthetic data · Parsers · Cleaning pipeline · Static wireframes | Deadline: Mar 22

---

## 1. Breakdown by Member

| Member | Role | Deliverable | Status | Notes |
|---|---|---|---|---|
| **Marcus** | Lead / Synthetic data / ML | Repo scaffold (#2), schema (#3), synthetic data (#4), CI fixes | ✅ Done | All 3 assigned issues closed; PR #19 merged; lint/gitignore fixes today |
| **Olga** | Cleaning pipeline | `data_cleaning.py`, directory restructure, `None`-string handling | ✅ Done | 3 commits Mar 20–21; pipeline functional |
| **Sophina** | Dashboard & visualisation | Dashboard wireframe (6 iterations Mar 20–21) | ✅ Done | Most iterated deliverable; README conflict resolved |
| **Max** | Log parsers (all 7 sources) | Single "Add files via upload" commit Mar 18 | ⚠️ Partial | Code exists in `src/parsers/ingest.py` but uploaded via GitHub UI — no branch, no PR, no review |
| **Emily** | Data filtering | Nothing committed | ❌ Not started | No commits. Marcus updated her README entry but no filtering code exists |
| **Callum** | Anomaly detection / correlation | Nothing committed | ❌ Not started | No commits at all; `src/analysis/` is empty |

---

## 2. Review Process Outcome

The contributing rules state: *"at least one teammate must review before merging."*

- **PR #19** (synthetic data, Marcus) — only formal PR in the log; merged by Marcus, so self-review risk unless a teammate approved via GitHub UI
- **Olga's work** — pushed directly without a visible PR merge commit
- **Max's upload** — GitHub web upload directly to a branch; no PR visible
- **Sophina's work** — committed to a separate branch and merged; resolved a README conflict with Olga

**The PR/review workflow was not consistently followed** outside of PR #19.

---

## 3. Sprint 1 Success vs. Plan

| Criterion | Met? |
|---|---|
| Schema frozen (Day 4) | ✅ Yes — `docs/schema.md` covering all 7 sources |
| Synthetic data for all 7 sources | ✅ Yes — generated and schema-compliant |
| Log parsers (all 7 sources) | ⚠️ Code present but unreviewed and untested |
| Cleaning pipeline | ✅ Yes — normalisation and null handling in place |
| Static wireframes | ✅ Yes — dashboard wireframe with accessibility iterations |
| CI passing | ⚠️ Only stabilised today (lint + test failures fixed) |
| Anomaly detection rules (A1–A7) | ❌ Not started |
| Data filtering | ❌ Not started |

**5 of 8 criteria fully met.** Callum and Emily are the gap.

---

## 4. Presentation Outlines

---

### 4.1 Client Meeting — 1pm (NCR Atleos)

Outcome-focused, non-technical. Goal: show progress, get feedback on wireframes and anomaly priorities.

1. **What we set out to do** (1 min)
   - Sprint 1 goal: lay the data foundation for the observability platform

2. **What we've built** (5 min)
   - **Schema** — 7 data sources, correlation IDs, anomaly taxonomy (A1–A7); demonstrates understanding of their infrastructure
   - **Synthetic data** — safe, reproducible dev/test data without touching production ATM logs
   - **Dashboard wireframe** — walkthrough of Sophina's work; opportunity for early client feedback on layout and metric priorities

3. **What's connected end to end** (2 min)
   - Synthetic data → parser → cleaning pipeline: data flows through three stages already

4. **What we need from them** (2 min)
   - Confirm the 7 anomaly types (A1–A7) match their operational reality
   - Feedback on wireframe priorities (e.g. cash cassette alerts vs. JVM metrics)

> **Avoid:** mentioning CI failures, missing contributions, or internal team issues.

---

### 4.2 Management Meeting — 5pm

Honest and forward-looking. Goal: surface risks before Sprint 2 begins.

1. **Sprint 1 summary** (3 min)
   - 5 of 8 deliverables complete; data foundation layer is solid

2. **Contribution breakdown** (3 min)
   - Present the per-member table from §1
   - Flag that Callum and Emily have zero commits
   - Note the PR review process was not consistently followed

3. **Risk to Sprint 2** (3 min)
   - Sprint 2 requires anomaly detection (Callum) and filtering (Emily) from day 1; if still blocked, the correlation engine cannot be built
   - Max's parsers need proper testing before the cleaning pipeline can safely depend on them
   - CI was only stabilised today; unit test coverage is currently 0%

4. **What needs to happen this week**
   - Callum and Emily need to be unblocked or reassigned — escalate to management directly
   - Enforce the PR review rule: require a named second reviewer on every merge
   - Write unit tests for parsers and cleaning pipeline before Sprint 2 work begins

5. **Sprint 2 readiness**
   - Foundation is in place; team can proceed if the two contribution gaps are resolved
