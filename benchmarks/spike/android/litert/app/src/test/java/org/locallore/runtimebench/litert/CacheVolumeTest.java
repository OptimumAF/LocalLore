// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Collections;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

public class CacheVolumeTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();
    private static final String UUID = "ABCD-1234", SESSION = "0123456789abcdef0123456789abcdef";
    private CacheVolume.Candidate candidate(String uuid, boolean mounted, boolean primary, boolean emulated,
                                            boolean writable, long device) {
        return new CacheVolume.Candidate(uuid, mounted, primary, emulated, writable,
            device, CacheVolume.CACHE_MIN, new File("cache"), new File("files"));
    }
    @Test public void exactUuidSelectsIndependentVolumeWithoutPrimaryFallback() throws Exception {
        CacheVolume.Candidate primary = candidate(null, true, true, true, true, 10);
        CacheVolume.Candidate external = candidate(UUID, true, false, false, true, 20);
        assertSame(external, CacheVolume.select(Arrays.asList(primary, external), UUID, 10));
        assertEquals("volume_missing", assertThrows(CacheVolume.Problem.class,
            () -> CacheVolume.select(Collections.singletonList(primary), UUID, 10)).category);
        assertEquals("volume_missing", assertThrows(CacheVolume.Problem.class,
            () -> CacheVolume.select(Collections.singletonList(external), "abcd-1234", 10)).category);
    }
    @Test public void duplicateUuidFailsInsteadOfChoosingFirst() {
        CacheVolume.Candidate value = candidate(UUID, true, false, false, true, 20);
        assertEquals("volume_ambiguous", assertThrows(CacheVolume.Problem.class,
            () -> CacheVolume.select(Arrays.asList(value, value), UUID, 10)).category);
    }
    @Test public void MountedWritableNonemulatedIndependentDeviceAreAllRequired() {
        for (CacheVolume.Candidate value : Arrays.asList(
            candidate(UUID, false, false, false, true, 20), candidate(UUID, true, true, false, true, 20),
            candidate(UUID, true, false, true, true, 20), candidate(UUID, true, false, false, false, 20),
            candidate(UUID, true, false, false, true, 10), candidate(UUID, true, false, false, true, 0))) {
            assertEquals("volume_invalid", assertThrows(CacheVolume.Problem.class,
                () -> CacheVolume.select(Collections.singletonList(value), UUID, 10)).category);
        }
    }
    @Test public void SeparateFloorsCannotBorrowCapacityFromEachOther() throws Exception {
        CacheVolume.Candidate enough = candidate(UUID, true, false, false, true, 20);
        CacheVolume.capacity(enough, CacheVolume.USERDATA_MIN);
        assertEquals("capacity_blocked", assertThrows(CacheVolume.Problem.class,
            () -> CacheVolume.capacity(enough, CacheVolume.USERDATA_MIN - 1)).category);
        CacheVolume.Candidate shortCache = new CacheVolume.Candidate(UUID, true, false, false, true,
            20, CacheVolume.CACHE_MIN - 1, new File("cache"), new File("files"));
        assertThrows(CacheVolume.Problem.class, () -> CacheVolume.capacity(shortCache, Long.MAX_VALUE));
    }
    @Test public void InputsCannotIntroducePathsArbitraryCasesOrUnusedPlayPayload() throws Exception {
        CacheVolume.request("inspect", UUID, SESSION, null, null);
        CacheVolume.request("play", UUID, SESSION, "gift", "e30=");
        for (String value : Arrays.asList("../ABCD-1234", "", "ABCD-1234/private-canary", "null"))
            assertThrows(CacheVolume.Problem.class, () -> CacheVolume.request("mmap", value, SESSION, null, null));
        assertThrows(CacheVolume.Problem.class, () -> CacheVolume.request("play", UUID, SESSION, "arbitrary", "e30="));
        assertThrows(CacheVolume.Problem.class, () -> CacheVolume.request("inspect", UUID, SESSION, "gift", "e30="));
        assertThrows(CacheVolume.Problem.class, () -> CacheVolume.request("mmap", UUID, SESSION.toUpperCase(), null, null));
        assertThrows(CacheVolume.Problem.class, () -> CacheVolume.request("play", UUID, SESSION, "gift", "a".repeat(5465)));
    }
    @Test public void FreshSessionRetainsMarkerAndRejectsAdoptionWithoutChangingSentinel() throws Exception {
        File parent = temporary.newFolder();
        Path directory = CacheVolume.freshSession(parent, SESSION);
        assertArrayEquals("locallore-explicit-cache-probe-v1\n".getBytes(StandardCharsets.US_ASCII),
            Files.readAllBytes(directory.resolve("owner-v1")));
        Path sentinel = directory.resolve("retained"); Files.write(sentinel, new byte[]{42});
        assertThrows(java.io.IOException.class, () -> CacheVolume.freshSession(parent, SESSION));
        assertArrayEquals(new byte[]{42}, Files.readAllBytes(sentinel));
    }
    @Test public void MissingOrNondirectoryAncestorsDoNotCreateAnOutput() throws Exception {
        Path parent = temporary.newFolder().toPath();
        Path file = parent.resolve("file"); Files.write(file, new byte[]{1});
        assertThrows(CacheVolume.Problem.class, () -> CacheVolume.freshSession(file.toFile(), SESSION));
        Path absent = parent.resolve("absent");
        assertThrows(CacheVolume.Problem.class, () -> CacheVolume.freshSession(absent.toFile(), SESSION));
        assertFalse(Files.exists(absent));
    }
    @Test public void ModelCanOnlyBeTheFixedLeafOfSelectedFrameworkFilesDirectory() throws Exception {
        File files = temporary.newFolder();
        CacheVolume.Candidate value = new CacheVolume.Candidate(UUID, true, false, false, true,
            20, CacheVolume.CACHE_MIN, temporary.newFolder(), files);
        assertEquals("model_missing", assertThrows(CacheVolume.Problem.class, () -> CacheVolume.model(value)).category);
        Files.write(files.toPath().resolve(CacheVolume.MODEL), new byte[]{1});
        assertEquals(files.toPath().resolve(CacheVolume.MODEL).toFile(), CacheVolume.model(value));
    }
}
