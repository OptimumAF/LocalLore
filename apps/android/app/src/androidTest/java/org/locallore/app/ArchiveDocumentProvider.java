/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.res.AssetFileDescriptor;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.ParcelFileDescriptor;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** TEST APK ONLY, separate process. No arbitrary path/title input or target-app files. */
public final class ArchiveDocumentProvider extends ContentProvider {
    private static final int LIMIT = 32 * 1024 * 1024;
    private static final List<String> CASES = Arrays.asList("empty", "nonempty", "exact_limit", "overflow",
        "null", "failure", "read_only", "blockedopen");
    private final AtomicInteger opened = new AtomicInteger(), closed = new AtomicInteger(), started = new AtomicInteger(),
        mainOpens = new AtomicInteger(), rw = new AtomicInteger(), reads = new AtomicInteger(), forbiddenModes = new AtomicInteger(),
        blocked = new AtomicInteger();
    private final AtomicBoolean released = new AtomicBoolean();
    private final Object gate = new Object();
    private Handler callbacks;

    @Override public boolean onCreate() {
        HandlerThread thread = new HandlerThread("archive-provider-close"); thread.start();
        callbacks = new Handler(thread.getLooper()); return true;
    }
    @Override public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        return openFile(uri, mode, null);
    }
    @Override public AssetFileDescriptor openAssetFile(Uri uri, String mode, CancellationSignal signal) throws FileNotFoundException {
        ParcelFileDescriptor descriptor = openFile(uri, mode, signal);
        return descriptor == null ? null : new AssetFileDescriptor(descriptor, 0, AssetFileDescriptor.UNKNOWN_LENGTH);
    }
    @Override public ParcelFileDescriptor openFile(Uri uri, String mode, CancellationSignal ignored) throws FileNotFoundException {
        String name = caseName(uri);
        if (!"r".equals(mode) && !"rw".equals(mode)) {
            forbiddenModes.incrementAndGet(); throw new FileNotFoundException("Unsupported synthetic mode");
        }
        started.incrementAndGet();
        if ("rw".equals(mode)) rw.incrementAndGet(); else reads.incrementAndGet();
        if (Looper.myLooper() == Looper.getMainLooper()) mainOpens.incrementAndGet();
        if ("failure".equals(name)) throw new FileNotFoundException("SYNTHETIC_PRIVATE_PROVIDER_FAILURE");
        if ("null".equals(name)) return null;
        if ("blockedopen".equals(name)) {
            blocked.incrementAndGet();
            try {
                long deadline = System.nanoTime() + 15_000_000_000L;
                synchronized (gate) {
                    while (!released.get() && System.nanoTime() < deadline) gate.wait(20);
                }
                if (!released.get()) throw new FileNotFoundException("Synthetic open not released");
            } catch (InterruptedException failure) {
                Thread.currentThread().interrupt(); throw new FileNotFoundException("Synthetic open interrupted");
            } finally { blocked.decrementAndGet(); }
        }
        try {
            File file = fixture(name);
            if (!file.exists()) initialize(file, name);
            int flags = "r".equals(mode) || "read_only".equals(name)
                ? ParcelFileDescriptor.MODE_READ_ONLY : ParcelFileDescriptor.MODE_READ_WRITE;
            // Deliberately no MODE_TRUNCATE or MODE_CREATE on an opened destination.
            ParcelFileDescriptor descriptor = ParcelFileDescriptor.open(file, flags, callbacks, error -> closed.incrementAndGet());
            opened.incrementAndGet(); return descriptor;
        } catch (IOException failure) { throw new FileNotFoundException("Synthetic archive fixture unavailable"); }
    }
    private void initialize(File file, String name) throws IOException {
        if (!file.createNewFile()) throw new IOException("Synthetic leaf already exists");
        try (FileOutputStream output = new FileOutputStream(file)) {
            if ("nonempty".equals(name)) output.write("SYNTHETIC_OLD_ARCHIVE_BYTES".getBytes(StandardCharsets.US_ASCII));
            if ("exact_limit".equals(name) || "overflow".equals(name)) {
                byte[] buffer = new byte[8192]; Arrays.fill(buffer, (byte) 0x5a);
                for (int remaining = LIMIT; remaining > 0; remaining -= buffer.length) output.write(buffer);
                if ("overflow".equals(name)) output.write(0x7f);
            }
        }
    }
    @Override public Bundle call(String method, String arg, Bundle extras) {
        Bundle result = new Bundle();
        switch (method) {
            case "release": released.set(true); synchronized (gate) { gate.notifyAll(); } return result;
            case "stats":
                result.putInt("opened", opened.get()); result.putInt("closed", closed.get()); result.putInt("started", started.get());
                result.putInt("opened_on_main", mainOpens.get()); result.putInt("rw", rw.get()); result.putInt("reads", reads.get());
                result.putInt("forbidden_modes", forbiddenModes.get()); result.putInt("blocked", blocked.get()); return result;
            case "reset":
                requireDrained();
                for (String name : CASES) {
                    File file = fixture(name);
                    if (file.exists() && !file.delete()) throw new IllegalStateException("Synthetic cleanup failed");
                }
                opened.set(0); closed.set(0); started.set(0); mainOpens.set(0); rw.set(0); reads.set(0); forbiddenModes.set(0);
                released.set(false); return result;
            case "new_empty":
                requireDrained();
                File empty = fixture("empty");
                if (empty.exists() && !empty.delete()) throw new IllegalStateException("Synthetic cleanup failed");
                return result;
            case "bytes":
                if (!CASES.contains(arg)) throw new IllegalArgumentException("Unsupported synthetic case");
                File file = fixture(arg);
                if (!file.exists()) return result;
                if (file.length() > 65536) throw new IllegalStateException("Synthetic readback too large");
                try (FileInputStream input = new FileInputStream(file); ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                    byte[] buffer = new byte[1024]; int count;
                    while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
                    result.putByteArray("bytes", output.toByteArray()); return result;
                } catch (IOException failure) { throw new IllegalStateException("Synthetic readback failed"); }
            default: throw new IllegalArgumentException("Unsupported synthetic operation");
        }
    }
    private void requireDrained() {
        if (blocked.get() != 0 || opened.get() != closed.get()) throw new IllegalStateException("Synthetic provider is still active");
    }
    private File fixture(String name) {
        if (getContext() == null || !CASES.contains(name)) throw new IllegalStateException("Invalid synthetic case");
        return new File(getContext().getCacheDir(), "archive-document-test-" + name + ".bin");
    }
    private String caseName(Uri uri) throws FileNotFoundException {
        String authority = getContext() == null ? "" : getContext().getPackageName() + ".archives";
        List<String> segments = uri.getPathSegments(); String name = segments.size() == 1 ? segments.get(0) : "";
        if (!"content".equals(uri.getScheme()) || !authority.equals(uri.getAuthority()) || uri.getQuery() != null ||
            uri.getFragment() != null || !CASES.contains(name)) throw new FileNotFoundException("Unsupported synthetic case");
        return name;
    }
    @Override public String getType(Uri uri) { return "application/octet-stream"; }
    @Override public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs, String sortOrder) { return null; }
    @Override public Uri insert(Uri uri, ContentValues values) { throw new UnsupportedOperationException(); }
    @Override public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) { throw new UnsupportedOperationException(); }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) { throw new UnsupportedOperationException(); }
}
