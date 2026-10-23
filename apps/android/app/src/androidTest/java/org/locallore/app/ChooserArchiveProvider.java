/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.pm.ApplicationInfo;
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
import android.provider.DocumentsContract;
import android.provider.DocumentsContract.Document;
import android.provider.DocumentsContract.Root;
import android.provider.DocumentsProvider;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * TEST APK ONLY: a genuine DocumentsUI root containing exclusively synthetic archives.
 * Framework document operations retain DocumentsProvider permission/grant enforcement.
 * Custom setup/readback is restricted to the exact target/test UIDs, never MANAGE_DOCUMENTS
 * permission adoption. Titles, document IDs and caller data never become filesystem paths.
 */
public final class ChooserArchiveProvider extends DocumentsProvider {
    private static final int LIMIT = 128 * 1024;
    private static final int MAX_RUNS = 128;
    private static final int MAX_OUTPUTS = 8;
    private static final String ROOT_ID = "locallore-chooser-v1";
    private static final String ROOT_DOCUMENT = "root";
    private static final String TITLE = "LocalLore test archives";
    private static final String OUTPUT_TITLE = "locallore-private-story.json";
    private static final String MIME = "application/json";
    private static final String[] ROOT_COLUMNS = {
        Root.COLUMN_ROOT_ID, Root.COLUMN_DOCUMENT_ID, Root.COLUMN_TITLE,
        Root.COLUMN_FLAGS, Root.COLUMN_MIME_TYPES, Root.COLUMN_ICON
    };
    private static final String[] DOCUMENT_COLUMNS = {
        Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME, Document.COLUMN_MIME_TYPE,
        Document.COLUMN_FLAGS, Document.COLUMN_SIZE, Document.COLUMN_LAST_MODIFIED
    };
    private final Object gate = new Object();
    private final Map<String, Entry> documents = new HashMap<>();
    private final List<Run> runs = new ArrayList<>();
    private Run latest;
    private File base;
    private String authority;
    private int targetUid = -1;
    private int testUid = -1;
    private Handler closeCallbacks;

    private static final class Identity {
        final int target;
        final int test;
        final String authority;
        Identity(int target, int test, String authority) {
            this.target = target; this.test = test; this.authority = authority;
        }
    }
    private static Identity identity(Context context) {
        if (context == null) throw new IllegalStateException("Fixture context unavailable");
        String testPackage = context.getPackageName();
        if (!testPackage.endsWith(".test")) throw new IllegalStateException("Fixture package invalid");
        String targetPackage = testPackage.substring(0, testPackage.length() - 5);
        try {
            PackageManager manager = context.getPackageManager();
            ApplicationInfo target = manager.getApplicationInfo(targetPackage, 0);
            ApplicationInfo own = manager.getApplicationInfo(testPackage, 0);
            if (own.uid != Process.myUid() || target.uid == own.uid) {
                throw new IllegalStateException("Fixture identity invalid");
            }
            return new Identity(target.uid, own.uid, testPackage + ".chooser");
        } catch (PackageManager.NameNotFoundException failure) {
            throw new IllegalStateException("Fixture identity unavailable");
        }
    }

    /**
     * Ordinary test-only control provider, SAME process as the protected DocumentsProvider.
     * Acquisition needs no MANAGE_DOCUMENTS; authentication precedes payload parsing and
     * privileged acquisition. It cannot delegate any document, URI-grant or arbitrary call.
     */
    public static final class Control extends ContentProvider {
        private Identity identity;
        @Override public boolean onCreate() {
            identity = ChooserArchiveProvider.identity(getContext());
            return true;
        }
        @Override public Bundle call(String method, String arg, Bundle extras) {
            int caller = Binder.getCallingUid();
            if (caller != identity.target && caller != identity.test) {
                throw new SecurityException("Fixture control denied");
            }
            if (arg != null) throw new IllegalArgumentException("Fixture arguments invalid");
            Bundle payload = null;
            if ("configure".equals(method)) {
                byte[][] data = configuration(extras);
                payload = new Bundle();
                payload.putByteArray("archive", data[0]);
                payload.putByteArray("future", data[1]);
                payload.putByteArray("malformed", data[2]);
            } else if ("stats".equals(method)) {
                if (extras != null && !extras.isEmpty()) {
                    throw new IllegalArgumentException("Fixture arguments invalid");
                }
            } else {
                throw new IllegalArgumentException("Fixture operation unsupported");
            }
            Uri endpoint = new Uri.Builder().scheme("content").authority(identity.authority).build();
            long previous = Binder.clearCallingIdentity();
            try {
                Bundle result = getContext().getContentResolver().call(endpoint, method, null, payload);
                if (result == null) throw new IllegalStateException("Fixture control unavailable");
                return result;
            } finally {
                Binder.restoreCallingIdentity(previous);
            }
        }
        @Override public Cursor query(Uri uri, String[] projection, String selection,
                String[] selectionArgs, String sortOrder) { throw unsupported(); }
        @Override public String getType(Uri uri) { throw unsupported(); }
        @Override public Uri insert(Uri uri, ContentValues values) { throw unsupported(); }
        @Override public int delete(Uri uri, String selection, String[] selectionArgs) { throw unsupported(); }
        @Override public int update(Uri uri, ContentValues values, String selection,
                String[] selectionArgs) { throw unsupported(); }
        @Override public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
            throw new FileNotFoundException("Fixture control operation unsupported");
        }
        @Override public ParcelFileDescriptor openFile(Uri uri, String mode, CancellationSignal signal)
                throws FileNotFoundException {
            throw new FileNotFoundException("Fixture control operation unsupported");
        }
        private static UnsupportedOperationException unsupported() {
            return new UnsupportedOperationException("Fixture control operation unsupported");
        }
    }

    private static final class Run {
        final String token;
        final File directory;
        final List<Entry> entries = new ArrayList<>();
        final AtomicInteger opened = new AtomicInteger();
        final AtomicInteger closed = new AtomicInteger();
        final AtomicInteger active = new AtomicInteger();
        final AtomicInteger closeFailures = new AtomicInteger();
        int created;
        int reads;
        int writes;
        Entry lastOutput;
        Run(String token, File directory) { this.token = token; this.directory = directory; }
    }
    private static final class Entry {
        final Run run;
        final String id;
        final String title;
        final File file;
        final boolean output;
        boolean writeOpened;
        Entry(Run run, String suffix, String title, File file, boolean output) {
            this.run = run;
            this.id = "run-" + run.token + ":" + suffix;
            this.title = title;
            this.file = file;
            this.output = output;
        }
    }

    @Override public boolean onCreate() {
        Identity identity = identity(getContext());
        targetUid = identity.target;
        testUid = identity.test;
        authority = identity.authority;
        base = new File(getContext().getNoBackupFilesDir(), "chooser-archives-v1");
        HandlerThread callbacks = new HandlerThread("chooser-fixture-close");
        callbacks.start();
        closeCallbacks = new Handler(callbacks.getLooper());
        return true;
    }

    @Override public Bundle call(String method, String arg, Bundle extras) {
        // Mandatory superclass dispatch preserves platform create/isChild/grant checks.
        Bundle framework = super.call(method, arg, extras);
        if (framework != null || method.startsWith("android:")) return framework;
        int caller = Binder.getCallingUid();
        if (caller != targetUid && caller != testUid) {
            throw new SecurityException("Fixture control denied");
        }
        if (arg != null) throw new IllegalArgumentException("Fixture arguments invalid");
        if ("configure".equals(method)) return configure(extras);
        if ("stats".equals(method)) {
            if (extras != null && !extras.isEmpty()) {
                throw new IllegalArgumentException("Fixture arguments invalid");
            }
            return stats();
        }
        throw new IllegalArgumentException("Fixture operation unsupported");
    }

    @SuppressWarnings("deprecation")
    private static byte[] bytes(Bundle extras, String key) {
        Object value = extras.get(key);
        if (!(value instanceof byte[]) || ((byte[]) value).length > LIMIT) {
            throw new IllegalArgumentException("Fixture bytes invalid");
        }
        return ((byte[]) value).clone();
    }
    private static byte[][] configuration(Bundle extras) {
        try {
            if (extras == null || !extras.keySet().equals(new HashSet<>(Arrays.asList(
                    "archive", "future", "malformed")))) {
                throw new IllegalArgumentException("Fixture arguments invalid");
            }
            return new byte[][] { bytes(extras, "archive"), bytes(extras, "future"), bytes(extras, "malformed") };
        } catch (RuntimeException failure) {
            throw new IllegalArgumentException("Fixture arguments invalid");
        }
    }
    private Bundle configure(Bundle extras) {
        byte[][] data = configuration(extras);
        Run run;
        synchronized (gate) {
            for (Run previous : runs) {
                if (previous.active.get() != 0 || previous.closeFailures.get() != 0) {
                    throw new IllegalStateException("Fixture descriptors not drained");
                }
            }
            try {
                if (!Files.exists(base.toPath(), LinkOption.NOFOLLOW_LINKS)) {
                    Files.createDirectory(base.toPath());
                }
                realDirectory(base);
                int count = 0;
                try (DirectoryStream<Path> entries = Files.newDirectoryStream(base.toPath())) {
                    for (Path entry : entries) {
                        if (!entry.getFileName().toString().matches("run-[0-9a-f]{32}")) {
                            throw new IOException("Fixture directory invalid");
                        }
                        realDirectory(entry.toFile());
                        if (++count >= MAX_RUNS) throw new IOException("Fixture capacity reached");
                    }
                }
                String token = UUID.randomUUID().toString().replace("-", "");
                File directory = new File(base, "run-" + token);
                Files.createDirectory(directory.toPath()); // Never adopt an earlier run.
                run = new Run(token, directory);
                source(run, "valid", "Valid archive.json", "valid.json", data[0]);
                source(run, "future", "Future archive.json", "future.json", data[1]);
                source(run, "malformed", "Malformed archive.json", "malformed.json", data[2]);
                // Publish only a completely written synthetic run; failed/partial runs stay retained.
                for (Entry entry : run.entries) documents.put(entry.id, entry);
                runs.add(run);
                latest = run;
            } catch (IOException failure) {
                throw new IllegalStateException("Fixture setup failed");
            }
        }
        notifyChildren();
        getContext().getContentResolver().notifyChange(DocumentsContract.buildRootsUri(authority), null);
        Bundle reply = new Bundle();
        reply.putString("run", run.token);
        return reply;
    }
    private static void source(Run run, String suffix, String title, String leaf, byte[] bytes)
            throws IOException {
        File file = new File(run.directory, leaf);
        if (!file.createNewFile()) throw new IOException("Fixture leaf exists");
        try (FileOutputStream output = new FileOutputStream(file)) {
            output.write(bytes);
            output.getFD().sync();
        }
        run.entries.add(new Entry(run, suffix, title, file, false));
    }
    private Bundle stats() {
        synchronized (gate) {
            Run run = configured();
            Bundle reply = new Bundle();
            byte[] bytes = new byte[0];
            if (run.lastOutput != null) {
                try {
                    bytes = boundedBytes(run.lastOutput.file);
                } catch (IOException failure) {
                    throw new IllegalStateException("Fixture readback failed");
                }
            }
            reply.putByteArray("created_bytes", bytes);
            reply.putInt("created_count", run.created);
            reply.putInt("read_count", run.reads);
            reply.putInt("write_count", run.writes);
            reply.putInt("opened_count", run.opened.get());
            reply.putInt("closed_count", run.closed.get());
            reply.putInt("active_count", run.active.get());
            reply.putInt("close_failure_count", run.closeFailures.get());
            return reply;
        }
    }

    @Override public Cursor queryRoots(String[] projection) {
        String[] columns = projection == null ? ROOT_COLUMNS : projection;
        MatrixCursor cursor = new MatrixCursor(columns);
        MatrixCursor.RowBuilder row = cursor.newRow();
        for (String column : columns) {
            Object value = null;
            if (Root.COLUMN_ROOT_ID.equals(column)) value = ROOT_ID;
            if (Root.COLUMN_DOCUMENT_ID.equals(column)) value = ROOT_DOCUMENT;
            if (Root.COLUMN_TITLE.equals(column)) value = TITLE;
            if (Root.COLUMN_FLAGS.equals(column)) value = Root.FLAG_LOCAL_ONLY
                    | Root.FLAG_SUPPORTS_CREATE | Root.FLAG_SUPPORTS_IS_CHILD;
            if (Root.COLUMN_MIME_TYPES.equals(column)) value = MIME;
            if (Root.COLUMN_ICON.equals(column)) value = android.R.drawable.ic_menu_save;
            row.add(value);
        }
        return cursor;
    }
    @Override public Cursor queryDocument(String documentId, String[] projection)
            throws FileNotFoundException {
        synchronized (gate) {
            MatrixCursor cursor = new MatrixCursor(projection == null ? DOCUMENT_COLUMNS : projection);
            if (ROOT_DOCUMENT.equals(documentId)) add(cursor, null);
            else add(cursor, entry(documentId));
            return cursor;
        }
    }
    @Override public Cursor queryChildDocuments(String parentDocumentId, String[] projection,
            String sortOrder) throws FileNotFoundException {
        if (!ROOT_DOCUMENT.equals(parentDocumentId)) throw unavailable();
        synchronized (gate) {
            MatrixCursor cursor = new MatrixCursor(projection == null ? DOCUMENT_COLUMNS : projection);
            if (latest != null) for (Entry entry : latest.entries) add(cursor, entry);
            if (getContext() != null) cursor.setNotificationUri(getContext().getContentResolver(),
                    DocumentsContract.buildChildDocumentsUri(authority, ROOT_DOCUMENT));
            return cursor;
        }
    }
    @Override public boolean isChildDocument(String parentDocumentId, String documentId) {
        synchronized (gate) {
            Entry entry = documents.get(documentId);
            return ROOT_DOCUMENT.equals(parentDocumentId) && entry != null && entry.run == latest;
        }
    }
    private void add(MatrixCursor cursor, Entry entry) throws FileNotFoundException {
        BasicFileAttributes attributes = null;
        if (entry != null) {
            try { attributes = regular(entry.file); }
            catch (IOException failure) { throw unavailable(); }
        }
        MatrixCursor.RowBuilder row = cursor.newRow();
        for (String column : cursor.getColumnNames()) {
            Object value = null;
            if (Document.COLUMN_DOCUMENT_ID.equals(column)) value = entry == null ? ROOT_DOCUMENT : entry.id;
            if (Document.COLUMN_DISPLAY_NAME.equals(column)) value = entry == null ? TITLE : entry.title;
            if (Document.COLUMN_MIME_TYPE.equals(column)) value = entry == null ? Document.MIME_TYPE_DIR : MIME;
            if (Document.COLUMN_FLAGS.equals(column)) value = entry == null ? Document.FLAG_DIR_SUPPORTS_CREATE
                    : entry.output && !entry.writeOpened ? Document.FLAG_SUPPORTS_WRITE : 0;
            if (Document.COLUMN_SIZE.equals(column)) value = attributes == null ? 0L : attributes.size();
            if (Document.COLUMN_LAST_MODIFIED.equals(column)) value = attributes == null ? 0L
                    : attributes.lastModifiedTime().toMillis();
            row.add(value);
        }
    }
    @Override public String createDocument(String parentDocumentId, String mimeType, String displayName)
            throws FileNotFoundException {
        if (!ROOT_DOCUMENT.equals(parentDocumentId) || !MIME.equals(mimeType)
                || !OUTPUT_TITLE.equals(displayName)) throw unavailable();
        String id;
        synchronized (gate) {
            Run run = configured();
            if (run.created >= MAX_OUTPUTS) throw unavailable();
            int ordinal = run.created + 1;
            File file = new File(run.directory, "output-" + ordinal + ".json");
            try {
                realDirectory(run.directory);
                if (!file.createNewFile()) throw unavailable();
                regular(file);
            } catch (IOException failure) { throw unavailable(); }
            Entry entry = new Entry(run, "output-" + ordinal, OUTPUT_TITLE, file, true);
            run.entries.add(entry);
            run.created = ordinal;
            run.lastOutput = entry;
            documents.put(entry.id, entry);
            id = entry.id;
        }
        notifyChildren();
        return id;
    }
    @Override public ParcelFileDescriptor openDocument(String documentId, String mode,
            CancellationSignal signal) throws FileNotFoundException {
        if (signal != null) signal.throwIfCanceled();
        if (!"r".equals(mode) && !"rw".equals(mode)) throw unavailable();
        synchronized (gate) {
            Entry entry = entry(documentId);
            try {
                BasicFileAttributes attributes = regular(entry.file);
                if ("rw".equals(mode) && (!entry.output || entry.writeOpened || attributes.size() != 0)) {
                    throw unavailable();
                }
                int flags = "r".equals(mode) ? ParcelFileDescriptor.MODE_READ_ONLY
                        : ParcelFileDescriptor.MODE_READ_WRITE;
                Run run = entry.run;
                // A real seekable regular FD; no create/truncate/append and no pipe/file bridge.
                ParcelFileDescriptor descriptor = ParcelFileDescriptor.open(entry.file, flags,
                        closeCallbacks, error -> {
                            if (error != null) run.closeFailures.incrementAndGet();
                            run.closed.incrementAndGet();
                            run.active.decrementAndGet();
                        });
                run.opened.incrementAndGet();
                run.active.incrementAndGet();
                if ("r".equals(mode)) run.reads++;
                else { run.writes++; entry.writeOpened = true; }
                return descriptor;
            } catch (IOException failure) { throw unavailable(); }
        }
    }
    private Run configured() {
        if (latest == null) throw new IllegalStateException("Fixture not configured");
        return latest;
    }
    private Entry entry(String id) throws FileNotFoundException {
        Entry entry = documents.get(id);
        if (entry == null) throw unavailable();
        return entry;
    }
    private static FileNotFoundException unavailable() {
        return new FileNotFoundException("Fixture document unavailable");
    }
    private static void realDirectory(File file) throws IOException {
        BasicFileAttributes attributes = Files.readAttributes(file.toPath(), BasicFileAttributes.class,
                LinkOption.NOFOLLOW_LINKS);
        if (!attributes.isDirectory() || attributes.isSymbolicLink()) throw new IOException("Fixture directory invalid");
    }
    private static BasicFileAttributes regular(File file) throws IOException {
        realDirectory(file.getParentFile());
        BasicFileAttributes attributes = Files.readAttributes(file.toPath(), BasicFileAttributes.class,
                LinkOption.NOFOLLOW_LINKS);
        if (!attributes.isRegularFile() || attributes.isSymbolicLink() || attributes.size() > LIMIT) {
            throw new IOException("Fixture document invalid");
        }
        return attributes;
    }
    private static byte[] boundedBytes(File file) throws IOException {
        regular(file);
        try (FileInputStream input = new FileInputStream(file);
                ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int count;
            while ((count = input.read(buffer)) != -1) {
                if (output.size() + count > LIMIT) throw new IOException("Fixture document too large");
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
    private void notifyChildren() {
        if (getContext() != null) getContext().getContentResolver().notifyChange(
                DocumentsContract.buildChildDocumentsUri(authority, ROOT_DOCUMENT), null);
    }
}
