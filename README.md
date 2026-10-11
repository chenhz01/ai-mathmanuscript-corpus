# ai-mathmanuscript-corpus

A build specification and QA toolkit for AI-generated mathematics corpora. Validate records against a schema, detect near-duplicates, and audit license fields — without shipping or hosting any manuscript content. The corpus stays with you; this repo only defines what "clean" means.

Status: **spec + tools v0.1**, data currency **as of 2026-10-11**.

## Problem

AI labs now release math manuscripts in bulk (hundreds of papers, thousands of problem families, mixed formal-verification rates). Downstream researchers want to build on such corpora, but three questions block reuse: *is the metadata schema consistent?*, *are there near-duplicate manuscripts inflating results?*, and *what may I legally redistribute?* Public releases rarely answer all three, and teams re-invent ad-hoc checks per project. This repo turns those checks into a small, auditable toolkit plus a written corpus spec.

## How it works

The unit of governance is the **record** — metadata about one manuscript, never the manuscript body:

```json
{"id": "m-001", "title": "...", "problem_family": "...",
 "provenance": {"generator": "...", "model": "...", "date": "2026-09-30"},
 "verification": {"formal": true, "system": "lean"},
 "license": "CC-BY-4.0", "text_ref": "s3://bucket/m-001.pdf"}
```

- `validate` — schema check: required fields, ISO-8601 provenance dates, formal-verification consistency (a `formal: true` record must name a proof system), unknown-field warnings.
- `dedup` — normalized 8-word shingles + Jaccard similarity over texts *you* point it at; pairs above threshold are flagged for human review.
- `license-audit` — allowlist (`CC0-1.0`, `CC-BY-4.0`, `MIT`, ...) with three outcomes: `ok` / `review` / `reject` (proprietary or all-rights-reserved markers). Exit code reflects the worst status, so it can gate a pipeline.

**This repository contains no manuscript text, no corpus data, and no copyrighted content of any kind.** Corpus acquisition is deliberately left to you: obtain the source release yourself and respect its license.

## Quickstart (~3 min)

```bash
# Step 1: validate a records file (~2 s; create one first — see spec above)
python corpus_qa.py validate --file records.jsonl

# Step 2: near-dup scan over texts you hold (~seconds for 1k docs)
python corpus_qa.py dedup --manifest mapping.json --threshold 0.8

# Step 3: license gate (~2 s; exit 2 if anything is rejected)
python corpus_qa.py license-audit --file records.jsonl

# Full self test (~20 s)
python self_test.py
```

## Why not X

| Alternative | Why not |
|---|---|
| Ship the corpus itself in this repo | Copyright and licensing landmines; a mirror invites takedowns and freezes someone else's release format into ours. |
| Generic data-QA frameworks (Great Expectations-style) | Powerful but heavy; overkill for a 7-field schema, and none model formal-verification or license-gate semantics natively. |
| Ad-hoc scripts per research project | Each team re-derives dedup thresholds and license rules; results are not comparable across projects. |
| Full text plagiarism tools | They compare bodies of text we intentionally never touch; record-level provenance is the cheaper, safer unit. |

## Minimal Fallback

No Python available on the analysis box? The schema above is one JSON block — paste it into any language's JSON-schema tooling. The license allowlist is a nine-string set you can grep for manually. `dedup` degrades to `sort -u` on normalized lines for exact duplicates.

## Design Trade-offs

Priority: **license safety > schema strictness > dedup recall > speed**. Concretely: we fail closed on licenses (unknown = `review`, proprietary = `reject`) because false negatives are expensive; dedup defaults to a conservative 0.8 Jaccard threshold (high precision, tunable); and records store a `text_ref` pointer rather than content, keeping the tooling mirror-safe.

## Limits & Second-order Effects

- Schema v0.1 covers provenance/verification/license; it does not model per-theorem verification or reviewer sign-off.
- Shingle dedup misses paraphrased duplicates (different wording, same proof) — near-dup detection here is a recall *floor*, not a guarantee.
- **Second-order effects**: if this spec is widely adopted, license fields may get rubber-stamped ("just put CC-BY-4.0 so the audit passes") without checking the actual grant; and a clean dedup report may be over-read as "no duplicated *mathematics*", when two independently-written manuscripts can prove the same result. Human review stays mandatory for both.

## FAQ

**When NOT to use this tool?** If you need to host or redistribute corpus content, this gives you nothing but a schema. If your corpus is non-mathematical prose, the verification fields are dead weight. If you need semantic plagiarism detection, use a dedicated system.

**Does this repo contain any of the public math-manuscript corpora?** No — intentionally. Zero copyrighted content is embedded; `self_test.py` uses invented sample records only.

**Why is an unknown license "review" and not "ok"?** Fail-closed: an unrecognized string may still be restrictive. The `review` status forces a human decision without hard-blocking exploration.

**What threshold should dedup use?** Start at 0.8 (high precision). Lower it only when manually reviewing flagged pairs; every lowering trades reviewer time for recall.

**How do I extend the license allowlist?** Edit `LICENSE_ALLOWLIST` in `corpus_qa.py` — it is a plain set of SPDX-style strings. Add a license only after reading its actual grant; the allowlist is a policy decision, not a technical one.

Confidence: **High (>=80%)** that the validator catches the schema violations it lists (unit-tested). **Medium (60–79%)** that the 0.8 shingle threshold is a useful default — derived from general text-reuse practice, not measured on a math corpus `[estimated]`.

## [Core Assumptions]

1. Corpus governance can operate on metadata records; manuscript bodies never need to enter this toolchain.
2. Provenance (generator, model, date) is reliably available at record-creation time; records lacking it are treated as defective.
3. Formal-verification status is binary per manuscript (v0.1) — partial verifications are recorded as `formal: false`.
4. An 8-word shingle Jaccard threshold near 0.8 flags practically relevant duplicates in English math prose `[estimated]`.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 zhengming contributors.
