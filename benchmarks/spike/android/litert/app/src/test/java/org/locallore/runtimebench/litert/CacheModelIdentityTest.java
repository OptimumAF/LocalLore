// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.SeekableByteChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HashSet;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

/** Synthetic digest/fault tests; production Android lstat/fstat qualification is separate. */
public class CacheModelIdentityTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();
    private static final byte[] DATA = "synthetic-model-bytes".getBytes(java.nio.charset.StandardCharsets.US_ASCII);
    private static CacheModelIdentity.Stamp stamp(long size) { return new CacheModelIdentity.Stamp(20, 42, size, 100, true); }
    private static String sha(byte[] bytes) throws Exception {
        StringBuilder result = new StringBuilder();
        for (byte value : MessageDigest.getInstance("SHA-256").digest(bytes)) result.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
        return result.toString();
    }
    private static final class Source implements CacheModelIdentity.Source {
        byte[] data = DATA.clone();
        CacheModelIdentity.Stamp pathBefore = stamp(DATA.length), pathAfter = pathBefore;
        CacheModelIdentity.Stamp fdBefore = pathBefore, fdAfter = pathBefore;
        int pathCalls, statCalls, readCalls, opens, closes, offset, largestRequest;
        boolean readFails, closeFails, openFails;
        int invalidRead = Integer.MIN_VALUE;
        @Override public CacheModelIdentity.Stamp path() { return ++pathCalls == 1 ? pathBefore : pathAfter; }
        @Override public CacheModelIdentity.Handle open() throws IOException {
            opens++;
            if (openFails) throw new IOException("private-open-canary");
            return new CacheModelIdentity.Handle() {
                @Override public CacheModelIdentity.Stamp stat() { return ++statCalls == 1 ? fdBefore : fdAfter; }
                @Override public int read(byte[] buffer, int count) throws IOException {
                    readCalls++; largestRequest = Math.max(largestRequest, count);
                    if (readFails) throw new IOException("private-read-canary");
                    if (invalidRead != Integer.MIN_VALUE) return invalidRead;
                    if (offset == data.length) return -1;
                    int length = Math.min(count, data.length - offset);
                    System.arraycopy(data, offset, buffer, 0, length); offset += length; return length;
                }
                @Override public void close() throws IOException {
                    closes++;
                    if (closeFails) throw new IOException("private-close-canary");
                }
            };
        }
    }
    private CacheModelIdentity.Result verify(Source source) throws Exception {
        return CacheModelIdentity.verify(source, 20, DATA.length, sha(DATA));
    }
    @Test public void CompleteDigestUsesOneHandleAndClosesBeforeVerifiedReceipt() throws Exception {
        Source source = new Source(); CacheModelIdentity.Result result = verify(source);
        assertTrue(result.verified); assertEquals("verified", result.diagnostic);
        assertEquals(sha(DATA), result.sha256); assertEquals(DATA.length, result.bytes);
        assertEquals(1, source.opens); assertEquals(1, source.closes);
        assertEquals(2, source.pathCalls); assertEquals(2, source.statCalls);
    }
    @Test public void StreamingRequestsStayBoundedAcrossMultipleBlocksAndCheckEof() throws Exception {
        Source source = new Source(); source.data = new byte[CacheModelIdentity.BLOCK_BYTES * 2 + 19];
        for (int i = 0; i < source.data.length; i++) source.data[i] = (byte) (i % 251);
        source.pathBefore = stamp(source.data.length); source.pathAfter = source.pathBefore;
        source.fdBefore = source.pathBefore; source.fdAfter = source.pathBefore;
        CacheModelIdentity.Result result = CacheModelIdentity.verify(source, 20, source.data.length, sha(source.data));
        assertTrue(result.verified); assertEquals(4, source.readCalls);
        assertEquals(CacheModelIdentity.BLOCK_BYTES, source.largestRequest); assertEquals(1, source.closes);
    }
    @Test public void DigestMismatchRetainsOnlyCompleteDigestAndCount() throws Exception {
        Source source = new Source(); source.data[0] ^= 1;
        CacheModelIdentity.Result result = verify(source);
        assertFalse(result.verified); assertEquals("mismatch", result.diagnostic);
        assertEquals(sha(source.data), result.sha256); assertEquals(DATA.length, result.bytes);
        assertEquals(1, source.closes);
    }
    @Test public void TruncationAndGrowthNeverYieldVerifiedOrACompleteDigest() throws Exception {
        for (int size : new int[]{DATA.length - 1, DATA.length + 1}) {
            Source source = new Source(); source.data = Arrays.copyOf(DATA, size);
            CacheModelIdentity.Result result = verify(source);
            assertFalse(result.verified); assertEquals(size, result.bytes); assertEquals("", result.sha256);
            assertEquals(size < DATA.length ? "incomplete" : "mismatch", result.diagnostic);
            assertEquals(1, source.closes);
        }
    }
    @Test public void ChangedPathOrDescriptorIdentityRejectsEvenCorrectBytes() throws Exception {
        for (int choice = 0; choice < 5; choice++) {
            Source source = new Source();
            CacheModelIdentity.Stamp other = new CacheModelIdentity.Stamp(20, 99, DATA.length, 100, true);
            if (choice == 0) source.pathAfter = other;
            if (choice == 1) source.fdBefore = other;
            if (choice == 2) source.fdAfter = other;
            if (choice == 3) source.fdAfter = stamp(DATA.length + 1);
            if (choice == 4) source.pathAfter = null;
            CacheModelIdentity.Result result = verify(source);
            assertFalse(result.verified); assertEquals("unstable", result.diagnostic); assertEquals(1, source.closes);
        }
    }
    @Test public void AbsentNonregularWrongVolumeAndWrongInitialSizeDoNotOpen() throws Exception {
        for (int choice = 0; choice < 5; choice++) {
            Source source = new Source();
            if (choice == 0) source.pathBefore = null;
            if (choice == 1) source.pathBefore = new CacheModelIdentity.Stamp(20, 42, DATA.length, 100, false);
            if (choice == 2) source.pathBefore = new CacheModelIdentity.Stamp(21, 42, DATA.length, 100, true);
            if (choice == 3) source.pathBefore = stamp(DATA.length - 1);
            if (choice == 4) source.pathBefore = stamp(DATA.length + 1);
            CacheModelIdentity.Result result = verify(source);
            assertFalse(result.verified); assertEquals(0, source.opens);
            assertEquals(new String[]{"absent", "not_regular", "wrong_volume", "incomplete", "mismatch"}[choice], result.diagnostic);
        }
    }
    @Test public void ModeCtimeAndSubsecondDriftCannotHideBehindSameSizeAndSecond() throws Exception {
        CacheModelIdentity.Stamp baseline = new CacheModelIdentity.Stamp(20, 42, DATA.length,
            100, 10, 100, 10, 0100600, true, true);
        for (CacheModelIdentity.Stamp after : Arrays.asList(
                new CacheModelIdentity.Stamp(20, 42, DATA.length, 100, 11, 100, 10, 0100600, true, true),
                new CacheModelIdentity.Stamp(20, 42, DATA.length, 100, 10, 100, 11, 0100600, true, true),
                new CacheModelIdentity.Stamp(20, 42, DATA.length, 100, 10, 101, 10, 0100600, true, true),
                new CacheModelIdentity.Stamp(20, 42, DATA.length, 100, 10, 100, 10, 0100644, true, true))) {
            Source source = new Source(); source.pathBefore = baseline; source.pathAfter = baseline;
            source.fdBefore = baseline; source.fdAfter = after;
            assertEquals("unstable", verify(source).diagnostic); assertEquals(1, source.closes);
        }
    }
    @Test public void ReadAndOpenFailuresStayFixedAndKnownHandleIsClosed() throws Exception {
        Source read = new Source(); read.readFails = true;
        CacheModelIdentity.Result failed = verify(read);
        assertEquals("read_failed", failed.diagnostic); assertEquals("", failed.sha256);
        assertEquals(1, read.closes); assertFalse(failed.verified);
        Source open = new Source(); open.openFails = true;
        assertEquals("read_failed", verify(open).diagnostic); assertEquals(0, open.closes);
    }
    @Test public void CloseFailureHasNoGracefulReceiptEvenAfterCorrectReadOrReadFailure() throws Exception {
        for (boolean readFails : new boolean[]{false, true}) {
            Source source = new Source(); source.closeFails = true; source.readFails = readFails;
            CacheModelIdentity.OwnershipUnknown error = assertThrows(CacheModelIdentity.OwnershipUnknown.class, () -> verify(source));
            assertEquals("model_descriptor_ownership_unknown", error.getMessage()); assertEquals(1, source.closes);
        }
    }
    @Test public void NonprogressOrImpossibleReadCountsFailWithoutLooping() throws Exception {
        for (int count : new int[]{0, -2, DATA.length + 1}) {
            Source source = new Source(); source.invalidRead = count;
            assertEquals("read_failed", verify(source).diagnostic);
            assertEquals(1, source.readCalls); assertEquals(1, source.closes);
        }
    }
    @Test public void InstalledJvmProviderAcceptsNoFollowReadOnFreshRegularSyntheticFile() throws Exception {
        Path path = temporary.newFile().toPath(); Files.write(path, DATA);
        ByteBuffer buffer = ByteBuffer.allocate(DATA.length);
        try (SeekableByteChannel channel = Files.newByteChannel(path,
                new HashSet<>(Arrays.asList(StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS)))) {
            while (buffer.hasRemaining()) assertTrue(channel.read(buffer) > 0);
            assertEquals(-1, channel.read(ByteBuffer.allocate(1)));
        }
        assertArrayEquals(DATA, buffer.array());
    }
}
