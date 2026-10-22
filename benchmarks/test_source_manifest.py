"""Offline integrity checks for research metadata, not a model compatibility test."""
import json
from pathlib import Path
import re
import unittest


class SourceManifestTests(unittest.TestCase):
    def test_pins_hashes_and_unmeasured_status_are_explicit(self):
        path = Path(__file__).resolve().parents[1] / "docs/runtime/source-manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["status"], "research_only_no_runtime_selected")
        runtimes = {runtime["id"]: runtime for runtime in manifest["runtimes"]}
        self.assertEqual(set(runtimes), {"litert-lm", "llama.cpp"})
        for runtime in runtimes.values():
            self.assertRegex(runtime["commit"], r"^[0-9a-f]{40}$")
        for candidate in manifest["candidates"]:
            self.assertIn(candidate["runtime"], runtimes)
            self.assertRegex(candidate["revision"], r"^[0-9a-f]{40}$")
            self.assertFalse(candidate["weights_downloaded"])
            self.assertFalse(candidate["device_measured"])
            if candidate["published_artifact_sha256"] is not None:
                self.assertRegex(candidate["published_artifact_sha256"], r"^[0-9a-f]{64}$")
        urls = set()
        for source in manifest["sources"]:
            self.assertNotIn(source["url"], urls)
            urls.add(source["url"])
            self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(source["bytes"], 0)
            self.assertLessEqual(source["bytes"], 2 * 1024 * 1024)
            self.assertRegex(source["url"], r"^https://(raw\.githubusercontent\.com|huggingface\.co)/")
            self.assertIsNotNone(re.search(r"/[0-9a-f]{40}/", source["url"]))


if __name__ == "__main__":
    unittest.main()
