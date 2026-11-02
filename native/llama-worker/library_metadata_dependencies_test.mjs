// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Fixed synthetic-only entry point. No SDK/filesystem/model/app operation.
import { projectLibraryMetadataDependenciesV1 } from './library_metadata_dependencies.mjs';
import { runLibraryMetadataDependencySelfchecksV1 } from './library_metadata_dependency_first.mjs';

try {
  const summary = await runLibraryMetadataDependencySelfchecksV1(
    Object.freeze({ projectLibraryMetadataDependenciesV1 }));
  process.stdout.write(JSON.stringify(summary) + '\n');
  process.exitCode = summary.executed === 32 && summary.passed === 32 &&
    summary.failed === 0 && summary.failed_case_ids.length === 0 ? 0 : 1;
} catch {
  process.stderr.write('DependencyFactsSetupFailed\n');
  process.exitCode = 1;
}
