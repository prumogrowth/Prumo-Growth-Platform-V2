"""No network: adversarial smoke tests for source-pinned demonstration export."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from build_preview import collect_assets, git_blob_hash, make_archive


class ShareableDemoTests(unittest.TestCase):
    def test_asset_pin_and_runtime_only(self):
        assets, manifest = collect_assets()
        self.assertIn("index.html", assets)
        self.assertIn("styles.css", assets)
        self.assertIn("app.mjs", assets)
        self.assertTrue(all(x.endswith((".mjs", ".css", ".html")) for x in assets))
        self.assertFalse(any("test" in x or "README" in x for x in assets))
        for name, data in assets.items():
            pin = manifest["files"]["frontend/visual/" + name]
            self.assertEqual(pin["sha"], git_blob_hash(data))
            self.assertEqual(pin["size"], len(data))

    def test_export_contains_only_pinned_runtime_and_static_safety_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = make_archive(Path(tmp) / "site.zip")
            self.assertTrue(target.exists())
            assets, manifest = collect_assets()
            with ZipFile(target) as zipfile:
                names = zipfile.namelist()
                self.assertEqual(len(names), len(set(names)))
                self.assertEqual(set(names), set(assets) | {
                    "robots.txt", "_headers", "PREVIEW_BUILD_MANIFEST.json"})
                self.assertFalse(any(".." in name or "/" in name or "\\" in name for name in names))
                for name, data in assets.items():
                    self.assertEqual(zipfile.read(name), data)
                self.assertIn(b"Disallow: /", zipfile.read("robots.txt"))
                self.assertIn(b"noindex", zipfile.read("_headers"))
                snapshot = json.loads(zipfile.read("PREVIEW_BUILD_MANIFEST.json"))
                self.assertTrue(snapshot["synthetic_data_only"])
                self.assertFalse(snapshot["backend_calls"])
                self.assertFalse(snapshot["production_authorization"])
                self.assertEqual(snapshot["source_head"], manifest["source_head"])
                for name, digest in snapshot["runtime_files_sha256"].items():
                    self.assertEqual(digest, hashlib.sha256(zipfile.read(name)).hexdigest())


if __name__ == "__main__":
    unittest.main()
