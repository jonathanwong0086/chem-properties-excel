import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import license_gate as gate

ROOT = Path(__file__).resolve().parent.parent


def make_skill(root: Path) -> None:
    (root / "SKILL.md").write_text('---\nmetadata:\n  version: "9.9.9"\n---\nbody\n', encoding="utf-8")
    (root / "data.json").write_text('{"a": 1}\n', encoding="utf-8")
    (root / "sub").mkdir()
    (root / "sub" / "x.py").write_text("print(1)\n", encoding="utf-8")
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref\n", encoding="utf-8")
    (root / "out.xlsx").write_bytes(b"generated")
    manifest = gate.build_manifest(root)
    (root / gate.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


class AcceptanceTest(unittest.TestCase):
    def test_not_accepted_until_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_skill(root)
            self.assertFalse(gate.is_accepted(root))
            marker = gate.record_acceptance(root)
            self.assertTrue(gate.is_accepted(root))
            payload = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(payload["answer"], "是")
            self.assertEqual(payload["skill_version"], "9.9.9")
            self.assertEqual(set(payload), {"question", "answer", "accepted_at", "skill_version"})

    def test_corrupt_marker_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / gate.MARKER_NAME).write_text("not json", encoding="utf-8")
            self.assertFalse(gate.is_accepted(root))

    def test_enforce_requires_acceptance(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_skill(root)
            with self.assertRaisesRegex(gate.LicenseError, "新华院"):
                gate.enforce(root)


class ManifestTest(unittest.TestCase):
    def test_manifest_skips_git_outputs_and_itself(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_skill(root)
            files = gate.build_manifest(root)["files"]
            self.assertEqual(set(files), {"SKILL.md", "data.json", "sub/x.py"})

    def test_crlf_checkout_hashes_same(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_skill(root)
            (root / "data.json").write_bytes(b'{"a": 1}\r\n')
            self.assertEqual(gate.integrity_problems(root), [])

    def test_detects_modified_and_missing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_skill(root)
            (root / "data.json").write_text('{"a": 2}\n', encoding="utf-8")
            (root / "sub" / "x.py").unlink()
            (root / "extra.md").write_text("local note\n", encoding="utf-8")
            self.assertEqual(gate.integrity_problems(root), ["已修改: data.json", "缺失: sub/x.py"])

    def test_modified_copy_blocked_for_non_author(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_skill(root)
            gate.record_acceptance(root)
            (root / "data.json").write_text("{}\n", encoding="utf-8")
            with mock.patch.object(gate, "gh_login", return_value="someone-else"):
                with self.assertRaisesRegex(gate.LicenseError, "jonathanwong0086"):
                    gate.enforce(root)
            with mock.patch.object(gate, "gh_login", return_value=None):
                with self.assertRaises(gate.LicenseError):
                    gate.enforce(root)

    def test_modified_copy_allowed_for_author(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_skill(root)
            gate.record_acceptance(root)
            (root / "data.json").write_text("{}\n", encoding="utf-8")
            with mock.patch.object(gate, "gh_login", return_value="jonathanwong0086"):
                gate.enforce(root)

    def test_pristine_copy_does_not_call_gh(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_skill(root)
            gate.record_acceptance(root)
            with mock.patch.object(gate, "gh_login", side_effect=AssertionError("gh called")):
                gate.enforce(root)


class RepositoryManifestTest(unittest.TestCase):
    def test_committed_manifest_matches_repository(self):
        """Fails when files change without `python license_gate.py manifest`."""
        self.assertEqual(gate.integrity_problems(ROOT), [])

    def test_committed_manifest_version_matches_skill(self):
        manifest = json.loads((ROOT / gate.MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], gate.skill_version(ROOT))
        self.assertEqual(manifest["license"], gate.LICENSE_ID)


if __name__ == "__main__":
    unittest.main()
