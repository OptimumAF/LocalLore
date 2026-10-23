#!/usr/bin/env python3
"""Independent read-only collector regression; provision locked caches first.

This is retained RED review evidence for source c11a79d/c6be162. It does not
compile, extract source, run an app/worker/model, or determine legal approval.
Do not load it into the normal package entrypoint until the finding is resolved.
"""
import importlib.util
import os
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location(
    "reviewed_desktop_package", Path(__file__).with_name("desktop-package.py")
)
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class EmbeddedNativeAttributionReview(unittest.TestCase):
    def test_actual_collection_retains_embedded_json_author_attributions(self):
        # Observed in approved llama.cpp 620d2225 vendor/nlohmann/json.hpp,
        # SHA-256 f9ce5c0a1ac99e20ef92daeb60eb571e2146988daa553ac0269755348843efd7:
        # line17609 UTF-8 header: 2008 - 2009 Bjoern/Bjorn Hoehrmann (UTF-8 below);
        # line17635 and17663 number conversion: 2009 Florian Loitsch.
        # Both sections are outside the conditional C++14 Abseil fallback.
        # We require conservative preservation in this component's notices,
        # not a claim that every function/template contributes binary symbols.
        files, _, _ = package.rust_notices(os.environ.copy())
        catalog, _ = package.license_catalog()
        records = [r for r in catalog["additional_notices"] if
                   r.get("provenance", {}).get("path") in {
                       "licenses/LICENSE-jsonhpp", "vendor/nlohmann/json.hpp"}]
        self.assertTrue(records, "No catalog-bound nlohmann component material")
        material = b"\n".join(files[r["output"]] for r in records).decode("utf-8")
        missing = [name for name in ("Bj\u00f6rn Hoehrmann", "Florian Loitsch")
                   if name not in material]
        self.assertEqual(
            missing, [],
            "Selected pinned nlohmann header author notices are absent from "
            "the actual collected native-component packet; copying only its "
            "root Niels Lohmann MIT notice does not retain these attributions."
        )


if __name__ == "__main__":
    unittest.main()
