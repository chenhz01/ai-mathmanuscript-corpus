#!/usr/bin/env python3
"""ai-mathmanuscript-corpus — build spec + QA tools for AI-generated math manuscript corpora.

Schema validator, near-duplicate detector, and license auditor for corpus
RECORDS (metadata + pointers). This tool never ships, hosts or embeds any
manuscript text itself; you point it at files you already lawfully hold.
Pure standard library. No network. No secrets. Data currency: 2026-10-11.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys

AS_OF = "2026-10-11"

REQUIRED_FIELDS = ("id", "title", "problem_family", "license", "text_ref")
KNOWN_FIELDS = set(REQUIRED_FIELDS) | {"provenance", "verification"}
PROOF_SYSTEMS = {"lean", "lean4", "isabelle", "coq", "other"}
LICENSE_ALLOWLIST = {
    "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "MIT", "Apache-2.0",
    "BSD-3-Clause", "CC0", "PublicDomain", "public-domain",
}
PROPRIETARY_MARKERS = ("all rights reserved", "proprietary", "commercial license")


class InputError(ValueError):
    """Invalid user input; CLI maps this to exit code 2."""


def validate_record(rec):
    """Validate one corpus record. Returns (errors, warnings)."""
    errors, warnings = [], []
    if not isinstance(rec, dict):
        return ["record is not a JSON object"], []
    for key in REQUIRED_FIELDS:
        val = rec.get(key)
        if not isinstance(val, str) or not val.strip():
            errors.append("missing or empty field: %s" % key)
    prov = rec.get("provenance")
    if not isinstance(prov, dict) or not all(
            isinstance(prov.get(k), str) and prov.get(k).strip()
            for k in ("generator", "model", "date")):
        errors.append("provenance must include non-empty generator, model, date")
    else:
        try:
            datetime.date.fromisoformat(prov["date"])
        except ValueError:
            errors.append("provenance.date is not ISO-8601: %r" % prov["date"])
    ver = rec.get("verification")
    if not isinstance(ver, dict) or not isinstance(ver.get("formal"), bool):
        errors.append("verification.formal must be boolean")
    else:
        system = ver.get("system")
        if ver["formal"] and (not isinstance(system, str)
                              or system not in PROOF_SYSTEMS or system == "none"):
            errors.append("verification.system must name a proof system when formal=true")
    for key in rec:
        if key not in KNOWN_FIELDS:
            warnings.append("unknown field: %s" % key)
    return errors, warnings


def _normalize_words(text):
    return "".join(ch.lower() if ch.isalnum() else " " for ch in text).split()


def shingles(text, k=8):
    words = _normalize_words(text)
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def jaccard(a, b):
    if not a and not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def dedup_texts(texts, threshold=0.8):
    """texts: {id: str}. Returns near-dup pairs above threshold."""
    ids = sorted(texts)
    sh = {i: shingles(texts[i]) for i in ids}
    pairs = []
    for x, a in enumerate(ids):
        for b in ids[x + 1:]:
            score = jaccard(sh[a], sh[b])
            if score >= threshold:
                pairs.append({"a": a, "b": b, "jaccard": round(score, 4)})
    return pairs


def license_audit(rec):
    """Returns (status, detail). status in {ok, review, reject}."""
    lic = rec.get("license") if isinstance(rec, dict) else None
    if not isinstance(lic, str) or not lic.strip():
        return "reject", "license field missing or empty"
    normalized = lic.strip()
    if normalized in LICENSE_ALLOWLIST:
        return "ok", "license in allowlist: %s" % normalized
    low = normalized.lower()
    if any(marker in low for marker in PROPRIETARY_MARKERS):
        return "reject", "license marks proprietary/all-rights-reserved: %s" % normalized
    return "review", "license not in allowlist, manual review needed: %s" % normalized


def _iter_jsonl(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield lineno, json.loads(line)
                except json.JSONDecodeError as exc:
                    yield lineno, exc
    except OSError as exc:
        raise InputError("cannot read file: %s" % exc)


def cmd_validate(ns):
    bad = 0
    for lineno, obj in _iter_jsonl(ns.file):
        if isinstance(obj, Exception):
            print("line %d: ERROR: corrupt JSON line (%s)" % (lineno, obj))
            bad += 1
            continue
        errors, warnings = validate_record(obj)
        for e in errors:
            print("line %d: ERROR: %s" % (lineno, e))
        for w in warnings:
            print("line %d: WARN: %s" % (lineno, w))
        bad += len(errors)
    print("validation finished: %d error(s)" % bad)
    return 1 if bad else 0


def cmd_dedup(ns):
    try:
        with open(ns.manifest, "r", encoding="utf-8") as fh:
            mapping = json.load(fh)
    except json.JSONDecodeError as exc:
        raise InputError("manifest is not valid JSON: %s" % exc)
    except OSError as exc:
        raise InputError("cannot read manifest: %s" % exc)
    if not isinstance(mapping, dict):
        raise InputError("manifest must be a JSON object mapping id -> text file path")
    texts = {}
    for rid, path in mapping.items():
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                texts[rid] = fh.read()
        except OSError as exc:
            raise InputError("cannot read text for %s: %s" % (rid, exc))
    pairs = dedup_texts(texts, threshold=ns.threshold)
    for p in pairs:
        print("NEAR-DUP: %s <-> %s (jaccard=%.4f)" % (p["a"], p["b"], p["jaccard"]))
    print("dedup finished: %d pair(s) above %.2f" % (len(pairs), ns.threshold))
    return 0


def cmd_license(ns):
    worst = "ok"
    counts = {"ok": 0, "review": 0, "reject": 0}
    for lineno, obj in _iter_jsonl(ns.file):
        if isinstance(obj, Exception):
            print("line %d: ERROR: corrupt JSON line" % lineno)
            worst = max(worst, "reject", key=lambda s: {"ok": 0, "review": 1, "reject": 2}[s])
            counts["reject"] += 1
            continue
        status, detail = license_audit(obj)
        rid = obj.get("id", "?") if isinstance(obj, dict) else "?"
        print("line %d (%s): %s — %s" % (lineno, rid, status.upper(), detail))
        counts[status] += 1
        if status == "reject":
            worst = "reject"
        elif status == "review" and worst != "reject":
            worst = "review"
    print("license audit finished: %s (ok=%d review=%d reject=%d) as of %s"
          % (worst.upper(), counts["ok"], counts["review"], counts["reject"], AS_OF))
    return 2 if worst == "reject" else (1 if worst == "review" else 0)


def build_parser():
    p = argparse.ArgumentParser(prog="corpus_qa", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="validate a JSONL corpus record file")
    v.add_argument("--file", required=True)
    v.set_defaults(func=cmd_validate)

    d = sub.add_parser("dedup", help="detect near-duplicate texts via shingle Jaccard")
    d.add_argument("--manifest", required=True, help='JSON object {"id": "path/to/text"}')
    d.add_argument("--threshold", type=float, default=0.8)
    d.set_defaults(func=cmd_dedup)

    l = sub.add_parser("license-audit", help="audit license fields against allowlist")
    l.add_argument("--file", required=True)
    l.set_defaults(func=cmd_license)
    return p


def main(argv=None):
    ns = build_parser().parse_args(argv)
    try:
        return ns.func(ns)
    except InputError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
