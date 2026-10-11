# Alignment Audit (Rules 85-100 / 16 items) — ai-mathmanuscript-corpus

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Safety/Ethics section | N/A | Non-security-domain; corpus-compliance is itself the ethics surface. README states the no-copyrighted-content boundary explicitly. |
| 2 | Privacy de-identification | PASS | grep `(sk-\|ghp_\|api[_-]?key\s*=\s*['"][A-Za-z0-9])` = 0 hits; no real names/emails; sample records use invented titles and placeholder refs (`s3://bucket/...`). |
| 3 | Copyright boundary | PASS | Repo embeds ZERO corpus/copyrighted content (README states this; self_test uses invented text). Source release referenced only as an external fact. LICENSE (MIT) present. |
| 4 | Fact-check labeling | PASS | Threshold 0.8 labeled `[estimated]` with provenance note; no performance claims without either test backing or label. |
| 5 | Confidence grading | PASS | README Confidence block: High (validator coverage, tested) + Medium (dedup default threshold), each with one-line rationale. |
| 6 | Plan B built-in | PASS | README "Minimal Fallback": JSON schema reusable in any toolchain; allowlist greppable; exact-dup via `sort -u`. |
| 7 | Timeout preset | PASS | Quickstart: ~2 s / seconds / ~2 s step timings + full self-test ~20 s, staged path. |
| 8 | Rule conflict arbitration | PASS | README "Design Trade-offs": license safety > schema strictness > dedup recall > speed. |
| 9 | Version changelog | PASS | CHANGELOG.md: v0.1.0 + v0.1.1 with per-dimension improvements. |
| 10 | Exemption instruction | N/A | Session-level governance rule; static repo N/A. |
| 11 | External knowledge cutoff | PASS | "as of 2026-10-11" stamped in header, license-audit output, and spec status line. |
| 12 | Assumptions explicit | PASS | README `[Core Assumptions]`: 4 items (metadata-only governance, provenance availability, binary formal flag, shingle threshold). |
| 13 | Logic-check trio | PASS | self_test.py: functional 4 / error-path 4 / edge 5 (empty JSONL, corrupt line, 200k-char field, empty text dedup, corrupt manifest) — all PASS. |
| 14 | Socratic FAQ | PASS | FAQ "When NOT to use this tool?" with 3 concrete anti-cases; 5 FAQ entries total after round 2. |
| 15 | Pareto iteration | PASS | v0.1.1: README completeness +25% (FAQ 4→5, incl. allowlist-extension guidance); audit output correctness fix; tests re-run PASS. |
| 16 | Ultimate fallback (60-word entry) | PASS | Intro paragraph = 40 words, states what it is and that the corpus stays with the user. |

Audit date: 2026-10-11. Auditor: zhengming W5 (self-audit, round 2).
