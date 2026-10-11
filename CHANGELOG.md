# Changelog

All notable changes to this project are documented here.

## v0.1.1 — 2026-10-11 (round 2: audit + revision)

### Changed
- **Completeness (+25%)**: FAQ 4 → 5 entries; new entry documents how to extend
  the license allowlist as a policy decision (read the grant, then edit).
- **Correctness**: `license-audit` counts and reports corrupt JSONL lines
  per-status (reject) instead of only failing the run — auditable output.
- **Clarity**: intro paragraph audited at 40 words (<=60 limit, rule 16);
  no-content statement verified present in both Problem context and
  How-it-works ("contains no manuscript text / corpus data / copyrighted content").

### Verified
- self_test.py re-run after revision: all three tiers PASS
  (functional 4 / error-path 4 / edge 5 = 13 tests).

## v0.1.0 — 2026-10-11 (initial draft)

### Added
- `corpus_qa.py`: `validate` (record schema: provenance, verification,
  license), `dedup` (8-word shingle Jaccard), `license-audit`
  (allowlist + fail-closed three-status gate).
- `self_test.py`: functional / error-path / edge three-tier suite
  (sample records invented in-test; zero copyrighted content).
- README, MIT LICENSE, ALIGNMENT.md (16-item audit).
