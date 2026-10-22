/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.OperationCanceledException;
import android.os.ParcelFileDescriptor;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

/** Test APK only. Platform/Java APIs keep its separate process independent of target runtime classes. */
public final class TestDiagnosticProvider extends ContentProvider {
    public static final String AUTHORITY = "org.locallore.app.test.diagnostics";
    private final AtomicInteger opened = new AtomicInteger();
    private final AtomicInteger closed = new AtomicInteger();
    private final AtomicInteger started = new AtomicInteger();
    private final AtomicInteger cancelled = new AtomicInteger();
    private final AtomicInteger openedOnMain = new AtomicInteger();
    private final Object waiting = new Object();
    private Handler callbackHandler;

    @Override public boolean onCreate() {
        HandlerThread callbacks = new HandlerThread("diagnostic-test-close");
        callbacks.start();
        callbackHandler = new Handler(callbacks.getLooper());
        return true;
    }

    @Override public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        return openFile(uri, mode, null);
    }

    @Override public ParcelFileDescriptor openFile(Uri uri, String mode, CancellationSignal signal)
            throws FileNotFoundException {
        String path = caseName(uri);
        if (!"wt".equals(mode)) throw new FileNotFoundException("Unsupported synthetic mode");
        started.incrementAndGet();
        if (Looper.myLooper() == Looper.getMainLooper()) openedOnMain.incrementAndGet();
        if ("failure".equals(path)) throw new FileNotFoundException("SYNTHETIC_PROVIDER_SECRET_DO_NOT_EXPORT");
        if ("null".equals(path)) return null;
        if ("slow".equals(path)) {
            if (signal != null) signal.setOnCancelListener(() -> {
                cancelled.incrementAndGet();
                synchronized (waiting) { waiting.notifyAll(); }
            });
            long deadline = System.nanoTime() + 10_000_000_000L;
            try {
                synchronized (waiting) {
                    while ((signal == null || !signal.isCanceled()) && System.nanoTime() < deadline) {
                        waiting.wait(20);
                    }
                }
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                throw new OperationCanceledException("Synthetic provider interrupted");
            }
            if (signal != null) signal.throwIfCanceled();
            throw new OperationCanceledException("Synthetic slow provider timed out");
        }
        File file = fixture(path);
        try {
            if (!file.exists()) {
                try (FileOutputStream output = new FileOutputStream(file)) {
                    output.write("SYNTHETIC_OLD_BYTES_LONGER_THAN_NEW_OUTPUT".getBytes(StandardCharsets.US_ASCII));
                }
            }
            int flags = "write_failure".equals(path) ? ParcelFileDescriptor.MODE_READ_ONLY
                    : ParcelFileDescriptor.MODE_READ_WRITE | ParcelFileDescriptor.MODE_CREATE | ParcelFileDescriptor.MODE_TRUNCATE;
            ParcelFileDescriptor descriptor = ParcelFileDescriptor.open(file, flags, callbackHandler,
                    error -> closed.incrementAndGet());
            opened.incrementAndGet();
            return descriptor;
        } catch (IOException failure) {
            throw new FileNotFoundException("Synthetic fixture unavailable");
        }
    }

    @Override public Bundle call(String method, String arg, Bundle extras) {
        Bundle result = new Bundle();
        switch (method) {
            case "reset":
                fixture("success").delete();
                fixture("write_failure").delete();
                opened.set(0); closed.set(0); started.set(0); cancelled.set(0); openedOnMain.set(0);
                return result;
            case "stats":
                result.putInt("opened", opened.get()); result.putInt("closed", closed.get());
                result.putInt("started", started.get()); result.putInt("cancelled", cancelled.get());
                result.putInt("opened_on_main", openedOnMain.get());
                return result;
            case "bytes":
                File file = fixture("success");
                if (!file.exists()) return result;
                try (FileInputStream input = new FileInputStream(file);
                     ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                    byte[] buffer = new byte[1024];
                    int count;
                    while ((count = input.read(buffer)) != -1) {
                        if (output.size() + count > 16_384) throw new IllegalStateException("Synthetic fixture too large");
                        output.write(buffer, 0, count);
                    }
                    result.putByteArray("bytes", output.toByteArray());
                    return result;
                } catch (IOException failure) {
                    throw new IllegalStateException("Synthetic fixture unavailable");
                }
            default:
                throw new IllegalArgumentException("Unsupported synthetic operation");
        }
    }

    private File fixture(String name) {
        if (getContext() == null) throw new IllegalStateException("Missing synthetic provider context");
        return new File(getContext().getCacheDir(), "diagnostic-test-" + name + ".json");
    }

    private String caseName(Uri uri) throws FileNotFoundException {
        List<String> segments = uri.getPathSegments();
        String name = segments.size() == 1 ? segments.get(0) : "";
        if (!AUTHORITY.equals(uri.getAuthority()) || uri.getQuery() != null || uri.getFragment() != null
                || !("success".equals(name) || "failure".equals(name) || "write_failure".equals(name)
                || "null".equals(name) || "slow".equals(name))) {
            throw new FileNotFoundException("Unsupported synthetic destination");
        }
        return name;
    }

    @Override public String getType(Uri uri) {
        try { caseName(uri); }
        catch (FileNotFoundException invalid) { throw new IllegalArgumentException("Unsupported synthetic destination"); }
        return "application/json";
    }
    @Override public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs, String sortOrder) {
        return null;
    }
    @Override public Uri insert(Uri uri, ContentValues values) { throw new UnsupportedOperationException(); }
    @Override public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException();
    }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) { throw new UnsupportedOperationException(); }
}
