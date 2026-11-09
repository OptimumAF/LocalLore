"""Inert checker bytes from PR #381 for the frozen SDK17/SDK18 host fixtures.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

from benchmarks import archive_ui_build, diagnostic_ui_build


ARCHIVE = Path(__file__).with_name("fixtures") / "sdk17-sdk18-apk-checkers.zip"


def frozen_checker_bytes(relative):
    with ZipFile(ARCHIVE) as archive:
        return archive.read(relative)


def frozen_checker_scope(adapter, fixture_root):
    """Bind only the synthetic checker call to the original inert files."""
    root = fixture_root / "frozen-apk-checkers"
    if not root.exists():
        (root / "benchmarks").mkdir(parents=True)
        (root / "scripts").mkdir()
        for relative, _, _ in adapter.CHECKERS:
            (root / relative).write_bytes(frozen_checker_bytes(relative))
    verify = adapter.revalidate_checker
    base = SimpleNamespace(__file__=str(root / "scripts/audit_apk.py"))
    decoder = SimpleNamespace(__file__=str(root / "scripts/audit_physical_model_apk.py"), base=base)
    aliases = {"audit_apk": base, "scripts.audit_apk": base, "scripts.audit_physical_model_apk": decoder}

    def verify_in_fixture():
        modules = {adapter, adapter.build, diagnostic_ui_build, archive_ui_build}
        with ExitStack() as stack:
            for module in modules:
                stack.enter_context(patch.object(
                    module, "__file__", str(root / "benchmarks" / Path(module.__file__).name)))
            stack.enter_context(patch.dict(adapter.sys.modules, aliases))
            return verify()

    return patch.object(adapter, "revalidate_checker", verify_in_fixture)
