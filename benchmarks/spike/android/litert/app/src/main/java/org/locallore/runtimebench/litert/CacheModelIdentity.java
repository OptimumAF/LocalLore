// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import java.io.IOException;
import java.security.MessageDigest;

/** Bounded streaming integrity proof. Android supplies actual lstat/fstat on one owned FD. */
final class CacheModelIdentity {
    static final long EXPECTED_BYTES = 2588147712L;
    static final String EXPECTED_SHA256 = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c";
    static final int BLOCK_BYTES = 65536;

    interface Source {
        Stamp path() throws IOException; // null only for a known absent pathname
        Handle open() throws IOException; // implementation must use READ + NOFOLLOW
    }
    interface Handle {
        Stamp stat() throws IOException;
        int read(byte[] buffer, int count) throws IOException; // -1 is EOF; zero is not progress
        void close() throws IOException;
    }
    static final class Stamp {
        final long device, inode, size, modified, modifiedNanos, changed, changedNanos;
        final int mode;
        final boolean regular, precise;
        Stamp(long device, long inode, long size, long modified, boolean regular) {
            this(device, inode, size, modified, 0, modified, 0, regular ? 0100600 : 0120000, regular, false);
        }
        Stamp(long device, long inode, long size, long modified, long modifiedNanos, long changed,
              long changedNanos, int mode, boolean regular, boolean precise) {
            this.device = device; this.inode = inode; this.size = size; this.modified = modified;
            this.modifiedNanos = modifiedNanos; this.changed = changed; this.changedNanos = changedNanos;
            this.mode = mode; this.regular = regular; this.precise = precise;
        }
        boolean valid() { return device > 0 && inode > 0 && size >= 0 && regular
            && modifiedNanos >= 0 && modifiedNanos < 1000000000 && changedNanos >= 0 && changedNanos < 1000000000; }
        boolean same(Stamp other) {
            return other != null && valid() && other.valid() && device == other.device && inode == other.inode
                && size == other.size && modified == other.modified && modifiedNanos == other.modifiedNanos
                && changed == other.changed && changedNanos == other.changedNanos && mode == other.mode && precise == other.precise;
        }
    }
    static final class Result {
        final boolean verified;
        final String sha256, diagnostic;
        final long bytes;
        Result(boolean verified, String sha256, long bytes, String diagnostic) {
            this.verified = verified; this.sha256 = sha256; this.bytes = bytes; this.diagnostic = diagnostic;
        }
    }
    static final class OwnershipUnknown extends IOException {
        OwnershipUnknown() { super("model_descriptor_ownership_unknown"); }
    }

    static Result verify(Source source, long device) throws OwnershipUnknown {
        return verify(source, device, EXPECTED_BYTES, EXPECTED_SHA256);
    }

    // Expected values are injectable only in package-local synthetic JVM tests.
    static Result verify(Source source, long device, long expectedBytes, String expectedSha) throws OwnershipUnknown {
        if (device <= 0 || expectedBytes < 1 || expectedBytes > EXPECTED_BYTES
                || expectedSha == null || !expectedSha.matches("[a-f0-9]{64}"))
            return failed("invalid_receipt", 0);
        Handle handle = null;
        IOException primary = null;
        long count = 0;
        try {
            Stamp path = source.path();
            if (path == null) return failed("absent", 0);
            if (!path.regular) return failed("not_regular", 0);
            if (!path.valid()) return failed("invalid_receipt", 0);
            if (path.device != device) return failed("wrong_volume", 0);
            if (path.size != expectedBytes) return failed(path.size < expectedBytes ? "incomplete" : "mismatch", 0);
            handle = source.open();
            if (handle == null) return failed("invalid_receipt", 0);
            Stamp descriptor = handle.stat();
            if (!path.same(descriptor)) return failed("unstable", 0);
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[BLOCK_BYTES];
            boolean eof = false;
            while (count < expectedBytes) {
                int requested = (int) Math.min(buffer.length, expectedBytes - count);
                int read = handle.read(buffer, requested);
                if (read == -1) { eof = true; break; }
                if (read < 1 || read > requested) return failed("read_failed", count);
                digest.update(buffer, 0, read); count += read;
            }
            if (!eof) {
                int extra = handle.read(buffer, 1);
                if (extra < -1 || extra > 1 || extra == 0) return failed("read_failed", count);
                if (extra == 1) count++;
            }
            if (!descriptor.same(handle.stat()) || !descriptor.same(source.path())) return failed("unstable", count);
            if (count < expectedBytes) return failed("incomplete", count);
            if (count > expectedBytes) return failed("mismatch", count);
            String actual = hex(digest.digest());
            return new Result(actual.equals(expectedSha), actual, count, actual.equals(expectedSha) ? "verified" : "mismatch");
        } catch (IOException error) {
            primary = error;
            return failed("read_failed", count);
        } catch (java.security.NoSuchAlgorithmException impossible) {
            return failed("read_failed", count);
        } finally {
            if (handle != null) {
                try { handle.close(); }
                catch (Exception unknown) {
                    OwnershipUnknown failure = new OwnershipUnknown();
                    failure.addSuppressed(unknown);
                    if (primary != null) failure.addSuppressed(primary);
                    throw failure; // No false receipt when read succeeded but close did not.
                }
            }
        }
    }
    private static Result failed(String diagnostic, long bytes) { return new Result(false, "", bytes, diagnostic); }
    private static String hex(byte[] bytes) {
        char[] result = new char[bytes.length * 2];
        char[] alphabet = "0123456789abcdef".toCharArray();
        for (int i = 0; i < bytes.length; i++) {
            result[2 * i] = alphabet[(bytes[i] & 255) >>> 4]; result[2 * i + 1] = alphabet[bytes[i] & 15];
        }
        return new String(result);
    }
    private CacheModelIdentity() { }
}
