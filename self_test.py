#!/usr/bin/env python3
"""Three-tier self test for ai-mathmanuscript-corpus (corpus_qa.py).

All sample data below is generated in-test (invented math titles); no
copyrighted manuscript content is used anywhere.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import corpus_qa as cq  # noqa: E402

CLI = [sys.executable, os.path.join(HERE, "corpus_qa.py")]


def run_cli(*args):
    return subprocess.run(CLI + list(args), capture_output=True, text=True)


def good_record(rid="m-001"):
    return {
        "id": rid,
        "title": "On the convergence of a synthetic polynomial sequence",
        "problem_family": "analysis",
        "provenance": {"generator": "research-harness", "model": "example-model",
                       "date": "2026-09-30"},
        "verification": {"formal": True, "system": "lean"},
        "license": "CC-BY-4.0",
        "text_ref": "s3://bucket/m-001.pdf",
    }


class TestFunctional(unittest.TestCase):
    def test_valid_record_passes(self):
        errors, warnings = cq.validate_record(good_record())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_dedup_detects_near_dup(self):
        # 100-word text with one word changed: 8-gram shingle Jaccard ~0.84 >= 0.8
        base = " ".join("word%d" % i for i in range(100))
        near = base.replace("word50", "changed")
        far = "a completely different text about group cohomology and spectral sequences here"
        pairs = cq.dedup_texts({"a": base, "b": near, "c": far}, threshold=0.8)
        self.assertEqual([p["b"] for p in pairs if p["a"] == "a"], ["b"])

    def test_dedup_ignores_far_texts(self):
        pairs = cq.dedup_texts({"a": "one two three four five six seven eight",
                                "b": "alpha beta gamma delta epsilon zeta eta theta"})
        self.assertEqual(pairs, [])

    def test_license_statuses(self):
        self.assertEqual(cq.license_audit(good_record())[0], "ok")
        self.assertEqual(cq.license_audit({"license": "SomeProprietary License, all rights reserved"})[0], "reject")
        self.assertEqual(cq.license_audit({"license": "Custom-Weird"})[0], "review")
        self.assertEqual(cq.license_audit({})[0], "reject")


class TestErrorPaths(unittest.TestCase):
    def test_missing_required_fields(self):
        errors, _ = cq.validate_record({"id": "x"})
        self.assertTrue(any("missing or empty field" in e for e in errors))
        self.assertTrue(any("provenance" in e for e in errors))

    def test_bad_date(self):
        rec = good_record()
        rec["provenance"]["date"] = "not-a-date"
        errors, _ = cq.validate_record(rec)
        self.assertTrue(any("ISO-8601" in e for e in errors))

    def test_formal_without_system(self):
        rec = good_record()
        rec["verification"] = {"formal": True, "system": "none"}
        errors, _ = cq.validate_record(rec)
        self.assertTrue(any("proof system" in e for e in errors))

    def test_cli_missing_file_exits_2(self):
        res = run_cli("validate", "--file", "Z:/no/such/file.jsonl")
        self.assertEqual(res.returncode, 2)
        self.assertIn("error:", res.stderr)


class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.files = []

    def _path(self, name, content):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)
        self.files.append(p)
        return p

    def test_empty_jsonl(self):
        p = self._path("empty.jsonl", "")
        res = run_cli("validate", "--file", p)
        self.assertEqual(res.returncode, 0)
        self.assertIn("0 error(s)", res.stdout)

    def test_corrupt_jsonl_line(self):
        p = self._path("bad.jsonl", json.dumps(good_record()) + "\n{corrupt line\n")
        res = run_cli("validate", "--file", p)
        self.assertEqual(res.returncode, 1)
        self.assertIn("corrupt JSON line", res.stdout)

    def test_overlong_field(self):
        rec = good_record()
        rec["title"] = "T" * 200_000
        errors, _ = cq.validate_record(rec)
        self.assertEqual(errors, [])  # tolerated, schema has no length cap

    def test_empty_text_dedup(self):
        pairs = cq.dedup_texts({"a": "", "b": ""})
        self.assertEqual(pairs, [])  # empty shingle sets never match

    def test_corrupt_dedup_manifest(self):
        p = self._path("bad.json", "{not json")
        res = run_cli("dedup", "--manifest", p)
        self.assertEqual(res.returncode, 2)
        self.assertIn("not valid JSON", res.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
