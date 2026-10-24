/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.Binder;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.ParcelFileDescriptor;
import android.os.Process;
import android.os.ProxyFileDescriptorCallback;
import android.os.storage.StorageManager;
import android.provider.DocumentsContract.Document;
import android.provider.DocumentsContract.Root;
import android.provider.DocumentsProvider;
import android.system.ErrnoException;
import android.system.OsConstants;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** TEST APK only. Fixed original bytes, real system document grants and real proxy FD ownership. */
public final class ModelPickerDocumentsProvider extends DocumentsProvider {
    private static final String ROOT = "model-picker-root-v1";
    private static final String DIRECTORY = "root";
    private static final String[] KINDS = {"valid", "wrong", "open-failure", "blocked"};
    private static final String[] TITLES = {"Valid synthetic model.bin", "Wrong synthetic model.bin",
            "Unavailable synthetic model.bin", "Blocked synthetic model.bin"};
    private static final byte[] PAYLOAD =
            "LocalLore original model picker fixture v1. No model or story.\n"
                    .getBytes(StandardCharsets.US_ASCII);
    private final Object gate = new Object();
    private final Map<String, Run> runs = new HashMap<>();
    private Identity identity;
    private Handler callbacks;
    private Run latest;

    private static final class Identity {
        final int targetUid;
        final int testUid;
        final String authority;
        Identity(int target, int test, String authority) {
            targetUid = target; testUid = test; this.authority = authority;
        }
        void requireCaller() {
            int caller = Binder.getCallingUid();
            if (caller != targetUid && caller != testUid) throw new SecurityException("Fixture control denied");
        }
    }
    private static Identity identity(Context context) {
        if (context == null || !"org.locallore.app.modelpickerverify.test".equals(context.getPackageName())) {
            throw new IllegalStateException("Fixture package invalid");
        }
        try {
            PackageManager packages = context.getPackageManager();
            int own = packages.getApplicationInfo(context.getPackageName(), 0).uid;
            int target = packages.getApplicationInfo("org.locallore.app.modelpickerverify", 0).uid;
            if (own != Process.myUid() || own == target) throw new IllegalStateException("Fixture identity invalid");
            return new Identity(target, own, context.getPackageName() + ".modelpicker");
        } catch (PackageManager.NameNotFoundException failure) {
            throw new IllegalStateException("Fixture identity unavailable");
        }
    }

    /** Same TEST process as the protected provider; only exact target/test UIDs may control fixtures. */
    public static final class Control extends ContentProvider {
        private Identity identity;
        @Override public boolean onCreate() { identity = identity(getContext()); return true; }
        @Override public Bundle call(String method, String arg, Bundle extras) {
            identity.requireCaller();
            validateControl(method, arg, extras);
            long previous = Binder.clearCallingIdentity();
            try {
                Bundle reply = getContext().getContentResolver().call(
                        Uri.parse("content://" + identity.authority), method, null, extras);
                if (reply == null) throw new IllegalStateException("Fixture control unavailable");
                return reply;
            } finally { Binder.restoreCallingIdentity(previous); }
        }
        @Override public Cursor query(Uri uri, String[] p, String s, String[] a, String o) { throw unsupported(); }
        @Override public String getType(Uri uri) { throw unsupported(); }
        @Override public Uri insert(Uri uri, ContentValues values) { throw unsupported(); }
        @Override public int delete(Uri uri, String s, String[] a) { throw unsupported(); }
        @Override public int update(Uri uri, ContentValues v, String s, String[] a) { throw unsupported(); }
        @Override public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException { throw unavailable(); }
        private static UnsupportedOperationException unsupported() {
            return new UnsupportedOperationException("Fixture control operation unsupported");
        }
    }

    private static final class Run {
        final String token = UUID.randomUUID().toString().replace("-", "");
        final CountDownLatch release = new CountDownLatch(1);
        final AtomicInteger attempts = new AtomicInteger();
        final AtomicInteger opened = new AtomicInteger();
        final AtomicInteger closed = new AtomicInteger();
        final AtomicInteger active = new AtomicInteger();
        final AtomicInteger reads = new AtomicInteger();
        final AtomicInteger blockedReads = new AtomicInteger();
        final AtomicInteger failures = new AtomicInteger();
    }
    @Override public boolean onCreate() {
        identity = identity(getContext());
        HandlerThread thread = new HandlerThread("model-picker-fixture-io");
        thread.start(); callbacks = new Handler(thread.getLooper());
        return true;
    }
    @Override public Bundle call(String method, String arg, Bundle extras) {
        // Framework dispatch must retain DocumentsProvider's URI/grant checks.
        Bundle platform = super.call(method, arg, extras);
        if (platform != null || method.startsWith("android:")) return platform;
        identity.requireCaller();
        validateControl(method, arg, extras);
        synchronized (gate) {
            if ("configure".equals(method)) {
                if (runs.size() >= 16) throw new IllegalStateException("Fixture capacity reached");
                for (Run run : runs.values()) {
                    if (run.active.get() != 0 || run.failures.get() != 0) {
                        throw new IllegalStateException("Fixture owners not drained");
                    }
                }
                latest = new Run(); runs.put(latest.token, latest);
                Bundle result = new Bundle(); result.putString("run", latest.token);
                return result;
            }
            String token = extras.getString("run");
            Run run = runs.get(token);
            if (run == null || run != latest) throw new IllegalStateException("Fixture transaction unavailable");
            if ("release".equals(method)) run.release.countDown();
            return stats(run);
        }
    }
    private static void validateControl(String method, String arg, Bundle extras) {
        if (arg != null) throw new IllegalArgumentException("Fixture arguments invalid");
        if ("configure".equals(method)) {
            if (extras != null && !extras.isEmpty()) throw new IllegalArgumentException("Fixture arguments invalid");
        } else if ("stats".equals(method) || "release".equals(method)) {
            if (extras == null || !extras.keySet().equals(Collections.singleton("run"))
                    || !(extras.get("run") instanceof String)
                    || !extras.getString("run").matches("[a-f0-9]{32}")) {
                throw new IllegalArgumentException("Fixture arguments invalid");
            }
        } else throw new IllegalArgumentException("Fixture operation unsupported");
    }
    private static Bundle stats(Run run) {
        Bundle result = new Bundle();
        result.putInt("attempts", run.attempts.get());
        result.putInt("opened", run.opened.get()); result.putInt("closed", run.closed.get());
        result.putInt("active", run.active.get()); result.putInt("reads", run.reads.get());
        result.putInt("blocked_reads", run.blockedReads.get()); result.putInt("failures", run.failures.get());
        return result;
    }
    private String title() { return "LocalLore model fixtures (" + getContext().getPackageName() + ")"; }
    @Override public Cursor queryRoots(String[] projection) {
        MatrixCursor cursor = new MatrixCursor(projection == null ? new String[]{Root.COLUMN_ROOT_ID,
                Root.COLUMN_DOCUMENT_ID, Root.COLUMN_TITLE, Root.COLUMN_FLAGS, Root.COLUMN_MIME_TYPES,
                Root.COLUMN_ICON} : projection);
        MatrixCursor.RowBuilder row = cursor.newRow();
        for (String column : cursor.getColumnNames()) {
            Object value = null;
            if (Root.COLUMN_ROOT_ID.equals(column)) value = ROOT;
            if (Root.COLUMN_DOCUMENT_ID.equals(column)) value = DIRECTORY;
            if (Root.COLUMN_TITLE.equals(column)) value = title();
            if (Root.COLUMN_FLAGS.equals(column)) value = Root.FLAG_LOCAL_ONLY | Root.FLAG_SUPPORTS_IS_CHILD;
            if (Root.COLUMN_MIME_TYPES.equals(column)) value = "application/octet-stream";
            if (Root.COLUMN_ICON.equals(column)) value = android.R.drawable.ic_menu_save;
            row.add(value);
        }
        return cursor;
    }
    private MatrixCursor cursor(String[] projection) {
        return new MatrixCursor(projection == null ? new String[]{Document.COLUMN_DOCUMENT_ID,
                Document.COLUMN_DISPLAY_NAME, Document.COLUMN_MIME_TYPE, Document.COLUMN_FLAGS,
                Document.COLUMN_SIZE} : projection);
    }
    @Override public Cursor queryDocument(String id, String[] projection) throws FileNotFoundException {
        MatrixCursor cursor = cursor(projection);
        synchronized (gate) { add(cursor, id); }
        return cursor;
    }
    @Override public Cursor queryChildDocuments(String parent, String[] projection, String sort)
            throws FileNotFoundException {
        if (!DIRECTORY.equals(parent)) throw unavailable();
        MatrixCursor cursor = cursor(projection);
        synchronized (gate) {
            if (latest != null) for (String kind : KINDS) add(cursor, latest.token + ":" + kind);
        }
        return cursor;
    }
    @Override public boolean isChildDocument(String parent, String id) {
        synchronized (gate) {
            try { return DIRECTORY.equals(parent) && document(id).run == latest; }
            catch (FileNotFoundException failure) { return false; }
        }
    }
    private static final class Selected {
        final Run run; final int kind;
        Selected(Run run, int kind) { this.run = run; this.kind = kind; }
    }
    private Selected document(String id) throws FileNotFoundException {
        if (id == null || !id.matches("[a-f0-9]{32}:(valid|wrong|open-failure|blocked)")) throw unavailable();
        Run run = runs.get(id.substring(0, 32));
        int kind = Arrays.asList(KINDS).indexOf(id.substring(33));
        if (run == null || kind < 0) throw unavailable();
        return new Selected(run, kind);
    }
    private void add(MatrixCursor cursor, String id) throws FileNotFoundException {
        boolean directory = DIRECTORY.equals(id);
        Selected selected = directory ? null : document(id);
        MatrixCursor.RowBuilder row = cursor.newRow();
        for (String column : cursor.getColumnNames()) {
            Object value = null;
            if (Document.COLUMN_DOCUMENT_ID.equals(column)) value = id;
            if (Document.COLUMN_DISPLAY_NAME.equals(column)) value = directory ? title() : TITLES[selected.kind];
            if (Document.COLUMN_MIME_TYPE.equals(column)) value = directory ? Document.MIME_TYPE_DIR : "application/octet-stream";
            if (Document.COLUMN_FLAGS.equals(column)) value = 0;
            if (Document.COLUMN_SIZE.equals(column)) value = directory ? 0 : PAYLOAD.length;
            row.add(value);
        }
    }
    @Override public ParcelFileDescriptor openDocument(String id, String mode, CancellationSignal signal)
            throws FileNotFoundException {
        if (!"r".equals(mode)) throw unavailable();
        if (signal != null) signal.throwIfCanceled();
        final Selected selected;
        synchronized (gate) {
            selected = document(id);
            if (selected.run != latest || selected.run.attempts.incrementAndGet() > 16
                    || selected.run.active.get() != 0) throw unavailable();
            if (selected.kind != 2) selected.run.active.incrementAndGet();
        }
        if (selected.kind == 2) throw new FileNotFoundException("PRIVATE_PROVIDER_ERROR_MUST_NOT_REACH_UI");
        final byte[] bytes = PAYLOAD.clone();
        if (selected.kind == 1) bytes[0] ^= 1;
        Run run = selected.run;
        try {
            StorageManager manager = getContext().getSystemService(StorageManager.class);
            if (manager == null) throw new IOException("Fixture proxy unavailable");
            ParcelFileDescriptor descriptor = manager.openProxyFileDescriptor(ParcelFileDescriptor.MODE_READ_ONLY,
                    new ProxyFileDescriptorCallback() {
                        @Override public long onGetSize() { return bytes.length; }
                        @Override public int onRead(long offset, int size, byte[] data) throws ErrnoException {
                            run.reads.incrementAndGet();
                            if (selected.kind == 3) {
                                run.blockedReads.incrementAndGet();
                                try {
                                    if (!run.release.await(30, TimeUnit.SECONDS)) {
                                        run.failures.incrementAndGet(); throw new ErrnoException("fixture-read", OsConstants.EIO);
                                    }
                                } catch (InterruptedException failure) {
                                    Thread.currentThread().interrupt(); run.failures.incrementAndGet();
                                    throw new ErrnoException("fixture-read", OsConstants.EIO);
                                }
                            }
                            if (offset < 0 || offset > bytes.length || size < 0 || size > data.length) {
                                run.failures.incrementAndGet(); throw new ErrnoException("fixture-read", OsConstants.EINVAL);
                            }
                            int count = Math.min(size, bytes.length - (int) offset);
                            System.arraycopy(bytes, (int) offset, data, 0, count);
                            return count;
                        }
                        @Override public void onRelease() { run.closed.incrementAndGet(); run.active.decrementAndGet(); }
                    }, callbacks);
            run.opened.incrementAndGet();
            return descriptor;
        } catch (IOException failure) {
            run.active.decrementAndGet();
            throw unavailable();
        } catch (RuntimeException failure) {
            run.active.decrementAndGet(); run.failures.incrementAndGet();
            throw unavailable();
        }
    }
    private static FileNotFoundException unavailable() { return new FileNotFoundException("Fixture document unavailable"); }
}
