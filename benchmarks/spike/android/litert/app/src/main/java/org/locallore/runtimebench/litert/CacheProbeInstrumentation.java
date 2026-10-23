// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import android.app.Activity;
import android.app.Instrumentation;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Process;
import android.os.Environment;
import android.os.Build;
import android.os.storage.StorageManager;
import android.os.storage.StorageVolume;
import android.system.Os;
import android.system.OsConstants;
import android.system.ErrnoException;
import android.system.StructStat;
import android.util.Base64;
import com.google.ai.edge.litertlm.ExperimentalFlags;
import com.google.ai.edge.litertlm.Engine;
import com.google.ai.edge.litertlm.LogSeverity;
import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.File;
import java.io.FileDescriptor;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** Explicit separate-package cache experiment; never installs/provisions or searches for a model. */
public final class CacheProbeInstrumentation extends Instrumentation {
    private String operation, uuid, session, playCase, profile;
    private final AtomicBoolean finished = new AtomicBoolean();
    private final AtomicInteger pulses = new AtomicInteger();
    private final Handler main = new Handler(Looper.getMainLooper());
    private final Runnable pulse = new Runnable() {
        @Override public void run() { if (!finished.get()) { pulses.incrementAndGet(); main.postDelayed(this, 10); } }
    };
    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        Bundle args = arguments == null ? new Bundle() : arguments;
        operation = args.getString("operation", ""); uuid = args.getString("volume_uuid");
        session = args.getString("session"); playCase = args.getString("play_case"); profile = args.getString("profile_base64");
        Thread watchdog = new Thread(() -> {
            try { Thread.sleep(90000); } catch (InterruptedException ignored) { return; }
            if (!finished.get()) Process.killProcess(Process.myPid());
        }, "cache-probe-watchdog");
        watchdog.setDaemon(true); watchdog.start(); main.post(pulse); start();
    }
    @Override public void onStart() {
        JsonObject report = new JsonObject(); report.addProperty("version", 1);
        report.addProperty("operation", Arrays.asList("inspect", "mmap", "play", "verify_model").contains(operation) ? operation : "invalid");
        report.addProperty("status", "error"); report.addProperty("error", "runtime_failed");
        JsonObject metrics = new JsonObject();
        for (String field : Arrays.asList("engines_opened", "engines_closed", "conversations_opened", "conversations_closed"))
            metrics.addProperty(field, 0);
        metrics.addProperty("cleanup_requires_process_termination", false);
        AtomicBoolean descriptorsUncertain = new AtomicBoolean();
        try (QuietDescriptors ignored = new QuietDescriptors(descriptorsUncertain)) {
            if (!CacheVolume.PACKAGE.equals(getTargetContext().getPackageName())
                    || Looper.myLooper() == Looper.getMainLooper()) throw new CacheVolume.Problem("identity_invalid");
            CacheVolume.request(operation, uuid, session, playCase, profile);
            // Canonicalize the trusted framework root, matching the original spike:
            // Android may expose it through the OS-owned /data/user/0 alias.
            File userdata = getTargetContext().getNoBackupFilesDir().getCanonicalFile();
            long userdataDevice = Os.stat(userdata.getPath()).st_dev;
            List<CacheVolume.Candidate> candidates = discover();
            JsonArray volumes = new JsonArray();
            for (CacheVolume.Candidate candidate : candidates) volumes.add(volume(candidate));
            report.add("volumes", volumes);
            CacheVolume.Candidate selected = CacheVolume.select(candidates, uuid, userdataDevice);
            CacheVolume.stable(selected, selected, userdataDevice, Os.stat(userdata.getPath()).st_dev);
            JsonObject before = sample(selected, userdataDevice, userdata.getUsableSpace()); report.add("sample", before);
            if (operation.equals("verify_model")) {
                CacheModelIdentity.Result identity = verifyModel(selected);
                CacheVolume.Candidate after = refresh(selected, userdata, userdataDevice);
                report.add("post_sample", sample(after, userdataDevice, userdata.getUsableSpace()));
                JsonObject receipt = new JsonObject(); receipt.addProperty("verified", identity.verified);
                receipt.addProperty("sha256", identity.sha256); receipt.addProperty("bytes", identity.bytes);
                receipt.addProperty("diagnostic", identity.diagnostic); report.add("model_identity", receipt);
            } else if (!operation.equals("inspect")) {
                CacheVolume.capacity(selected, userdata.getUsableSpace());
                Path cache = CacheVolume.freshSession(selected.cache, session);
                CacheVolume.capacity(refresh(selected, userdata, userdataDevice), userdata.getUsableSpace());
                CacheVolume.owner(cache);
                if (Os.stat(cache.toString()).st_dev != selected.device) throw new CacheVolume.Problem("volume_changed");
                if (operation.equals("mmap")) report.add("probe", mmap(cache));
                else {
                    File model = CacheVolume.model(selected);
                    if (Os.stat(model.getPath()).st_dev != selected.device) throw new CacheVolume.Problem("volume_changed");
                    byte[] encoded = Base64.decode(profile, Base64.DEFAULT);
                    if (encoded.length == 0 || encoded.length > 4096) throw new CacheVolume.Problem("invalid_request");
                    Path saves = CacheVolume.freshSession(userdata, session);
                    Engine.Companion.setNativeMinLogSeverity(LogSeverity.INFINITY);
                    ExperimentalFlags.INSTANCE.setEnableBenchmark(true);
                    ExperimentalFlags.INSTANCE.setEnableSpeculativeDecoding(false);
                    NativePlayProbe.Adapter probe = new NativePlayProbe.Adapter(saves.resolve("stories.sqlite3").toString(), encoded);
                    report.add("play_result", new PlayRunner(probe, () -> {
                        CacheVolume.Candidate current = refresh(selected, userdata, userdataDevice);
                        CacheVolume.capacity(current, userdata.getUsableSpace()); CacheVolume.owner(cache);
                        if (current.device != selected.device || Os.stat(cache.toString()).st_dev != selected.device
                                || Os.stat(CacheVolume.model(current).getPath()).st_dev != selected.device)
                            throw new CacheVolume.Problem("volume_changed");
                        return new CacheSdkModel(model, cache.toFile(), metrics, pulses);
                    }, metrics).run(playCase));
                    report.addProperty("explicit_cache_directory", true);
                }
                CacheVolume.Candidate after = refresh(selected, userdata, userdataDevice);
                report.add("post_sample", sample(after, userdataDevice, userdata.getUsableSpace()));
            }
            report.addProperty("status", "completed"); report.add("error", JsonNull.INSTANCE);
        } catch (WarmRunner.Undrained | CacheModelIdentity.OwnershipUnknown unknown) {
            // Abrupt own-process termination is not reported as successful resource disposal.
            Process.killProcess(Process.myPid()); return;
        } catch (CacheVolume.Problem problem) { report.addProperty("error", problem.category);
        } catch (UnsatisfiedLinkError | NoClassDefFoundError unavailable) { report.addProperty("error", "runtime_unavailable");
        } catch (Exception failure) { report.addProperty("error", "runtime_failed"); }
        // A body exception can suppress a TWR cleanup exception. The independent flag
        // also covers constructor rollback, so neither path can publish graceful completion.
        if (descriptorsUncertain.get()) { Process.killProcess(Process.myPid()); return; }
        finished.set(true); main.removeCallbacks(pulse);
        metrics.addProperty("main_pulses", pulses.get());
        metrics.addProperty("owners_balanced", metrics.get("engines_opened").equals(metrics.get("engines_closed"))
            && metrics.get("conversations_opened").equals(metrics.get("conversations_closed")));
        report.add("metrics", metrics);
        Bundle result = new Bundle(); result.putString("cache_result", report.toString());
        finish(Activity.RESULT_OK, result);
    }
    private CacheModelIdentity.Result verifyModel(CacheVolume.Candidate selected) throws Exception {
        Path parent = CacheVolume.realDirectory(selected.files);
        if (Os.stat(parent.toString()).st_dev != selected.device) throw new CacheVolume.Problem("volume_changed");
        String path = parent.resolve(CacheVolume.MODEL).toString();
        CacheModelIdentity.Source source = new CacheModelIdentity.Source() {
            @Override public CacheModelIdentity.Stamp path() throws IOException {
                try { return stamp(Os.lstat(path)); }
                catch (ErrnoException error) {
                    if (error.errno == OsConstants.ENOENT) return null;
                    throw new IOException("model_stat_failed");
                }
            }
            @Override public CacheModelIdentity.Handle open() throws IOException {
                final FileDescriptor descriptor;
                try { descriptor = Os.open(path, OsConstants.O_RDONLY | OsConstants.O_NOFOLLOW, 0); }
                catch (ErrnoException error) { throw new IOException("model_open_failed"); }
                return new CacheModelIdentity.Handle() {
                    @Override public CacheModelIdentity.Stamp stat() throws IOException {
                        try { return stamp(Os.fstat(descriptor)); }
                        catch (ErrnoException error) { throw new IOException("model_fstat_failed"); }
                    }
                    @Override public int read(byte[] buffer, int count) throws IOException {
                        try { int read = Os.read(descriptor, buffer, 0, count); return read == 0 ? -1 : read; }
                        catch (ErrnoException error) { throw new IOException("model_read_failed"); }
                    }
                    @Override public void close() throws IOException {
                        try { Os.close(descriptor); }
                        catch (ErrnoException error) { throw new IOException("model_close_failed"); }
                    }
                };
            }
        };
        return CacheModelIdentity.verify(source, selected.device);
    }
    private static CacheModelIdentity.Stamp stamp(StructStat value) {
        if (Build.VERSION.SDK_INT >= 27) {
            return new CacheModelIdentity.Stamp(value.st_dev, value.st_ino, value.st_size,
                value.st_mtim.tv_sec, value.st_mtim.tv_nsec, value.st_ctim.tv_sec, value.st_ctim.tv_nsec,
                value.st_mode, OsConstants.S_ISREG(value.st_mode), true);
        }
        return new CacheModelIdentity.Stamp(value.st_dev, value.st_ino, value.st_size,
            value.st_mtime, 0, value.st_ctime, 0, value.st_mode, OsConstants.S_ISREG(value.st_mode), false);
    }
    private CacheVolume.Candidate refresh(CacheVolume.Candidate selected, File userdata, long expectedDevice) throws Exception {
        long actualDevice = Os.stat(userdata.getPath()).st_dev;
        CacheVolume.Candidate current = CacheVolume.select(discover(), uuid, actualDevice);
        CacheVolume.stable(selected, current, expectedDevice, actualDevice);
        return current;
    }
    private List<CacheVolume.Candidate> discover() throws Exception {
        StorageManager manager = getTargetContext().getSystemService(StorageManager.class);
        if (manager == null) throw new CacheVolume.Problem("volume_invalid");
        // These framework calls may create/fix the package's directories. Inspect is not allocation-free.
        File[] caches = getTargetContext().getExternalCacheDirs();
        File[] files = getTargetContext().getExternalFilesDirs(null);
        if (caches.length > 16 || files.length > 16) throw new CacheVolume.Problem("volume_invalid");
        List<CacheVolume.Candidate> result = new ArrayList<>();
        for (File cache : caches) {
            if (cache == null) continue;
            StorageVolume volume = manager.getStorageVolume(cache);
            if (volume == null) continue;
            String id = volume.getUuid();
            if (id != null && !CacheVolume.uuid(id)) throw new CacheVolume.Problem("volume_invalid");
            boolean mounted = Environment.MEDIA_MOUNTED.equals(volume.getState());
            File matching = null;
            long device = 0, available = 0;
            if (mounted) {
                if (!volume.isPrimary() && !volume.isEmulated()) CacheVolume.realDirectory(cache);
                device = Os.stat(cache.getPath()).st_dev; available = cache.getUsableSpace();
                for (File file : files) {
                    if (file == null) continue;
                    StorageVolume fileVolume = manager.getStorageVolume(file);
                    if (fileVolume == null || id == null || !id.equals(fileVolume.getUuid())) continue;
                    if (matching != null) throw new CacheVolume.Problem("volume_ambiguous");
                    CacheVolume.realDirectory(file);
                    if (Os.stat(file.getPath()).st_dev != device) throw new CacheVolume.Problem("volume_invalid");
                    matching = file;
                }
            }
            result.add(new CacheVolume.Candidate(id, mounted, volume.isPrimary(), volume.isEmulated(),
                mounted && cache.canWrite() && matching != null && matching.canWrite(), device, available, cache, matching));
        }
        return result;
    }
    private static JsonObject volume(CacheVolume.Candidate candidate) {
        JsonObject result = new JsonObject();
        if (candidate.uuid == null) result.add("volume_uuid", JsonNull.INSTANCE); else result.addProperty("volume_uuid", candidate.uuid);
        result.addProperty("mounted", candidate.mounted); result.addProperty("primary", candidate.primary);
        result.addProperty("emulated", candidate.emulated); result.addProperty("writable", candidate.writable);
        result.addProperty("cache_device", candidate.device); result.addProperty("cache_free_bytes", candidate.free);
        return result;
    }
    private static JsonObject sample(CacheVolume.Candidate candidate, long userdataDevice, long userdataFree) throws Exception {
        JsonObject result = volume(candidate); result.addProperty("userdata_device", userdataDevice);
        result.addProperty("userdata_free_bytes", userdataFree);
        long[] budget = {0, 0};
        try (java.nio.file.DirectoryStream<Path> children = Files.newDirectoryStream(CacheVolume.realDirectory(candidate.cache))) {
            for (Path child : children) {
                if (++budget[0] > 4096) throw new CacheVolume.Problem("cache_inventory_limit");
                if (!child.getFileName().toString().matches("locallore-cache-probe-v1-[a-f0-9]{32}")) continue;
                CacheVolume.owner(child); size(child, 0, budget);
            }
        }
        result.addProperty("cache_bytes", budget[1]); return result;
    }
    private static void size(Path path, int depth, long[] budget) throws Exception {
        if (++budget[0] > 4096 || depth > 16 || Files.isSymbolicLink(path)) throw new CacheVolume.Problem("cache_inventory_limit");
        if (Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)) {
            try (java.nio.file.DirectoryStream<Path> children = Files.newDirectoryStream(path)) {
                for (Path child : children) size(child, depth + 1, budget);
            }
        } else if (Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) {
            budget[1] = Math.addExact(budget[1], Files.size(path));
        } else throw new CacheVolume.Problem("path_invalid");
    }
    private static JsonObject mmap(Path directory) throws Exception {
        Path path = directory.resolve("synthetic-mmap-v1.bin");
        FileDescriptor descriptor = null; long address = 0; boolean mapped = false, closed = false, verified = false;
        try {
            descriptor = Os.open(path.toString(), OsConstants.O_CREAT | OsConstants.O_EXCL | OsConstants.O_RDWR | OsConstants.O_NOFOLLOW, 0600);
            byte[] expected = new byte[CacheVolume.PROBE_BYTES];
            for (int i = 0; i < expected.length; i++) expected[i] = (byte) (i % 251);
            int offset = 0;
            while (offset < expected.length) { int count = Os.write(descriptor, expected, offset, expected.length - offset);
                if (count <= 0) throw new CacheVolume.Problem("probe_failed"); offset += count; }
            Os.fsync(descriptor); Os.lseek(descriptor, 0, OsConstants.SEEK_SET);
            byte[] actual = new byte[expected.length]; offset = 0;
            while (offset < actual.length) { int count = Os.read(descriptor, actual, offset, actual.length - offset);
                if (count <= 0) throw new CacheVolume.Problem("probe_failed"); offset += count; }
            if (!Arrays.equals(expected, actual) || Os.read(descriptor, new byte[1], 0, 1) != 0)
                throw new CacheVolume.Problem("probe_failed");
            verified = true;
            address = Os.mmap(0, expected.length, OsConstants.PROT_READ, OsConstants.MAP_SHARED, descriptor, 0); mapped = true;
        } finally {
            boolean clean = true;
            if (mapped) { try { Os.munmap(address, CacheVolume.PROBE_BYTES); } catch (Exception failure) { clean = false; } }
            if (descriptor != null) { try { Os.close(descriptor); closed = true; } catch (Exception failure) { clean = false; } }
            if (!clean) throw new WarmRunner.Undrained();
        }
        if (!verified || !mapped || !closed) throw new CacheVolume.Problem("probe_failed");
        Files.delete(path); // Only the fresh, exclusively created file; marked directory remains.
        JsonObject result = new JsonObject(); result.addProperty("bytes", CacheVolume.PROBE_BYTES);
        for (String key : Arrays.asList("content_verified", "mapped", "unmapped", "closed", "file_removed", "owner_directory_retained"))
            result.addProperty(key, true);
        result.addProperty("mapped_pointer_read", false); return result;
    }
    private static final class QuietDescriptors implements AutoCloseable {
        private FileDescriptor stdout, stderr;
        private final AtomicBoolean uncertain;
        QuietDescriptors(AtomicBoolean uncertain) throws Exception {
            this.uncertain = uncertain;
            try {
                System.out.flush(); System.err.flush(); stdout = Os.dup(FileDescriptor.out); stderr = Os.dup(FileDescriptor.err);
                FileDescriptor sink = Os.open("/dev/null", OsConstants.O_WRONLY, 0);
                try { Os.dup2(sink, 1); Os.dup2(sink, 2); }
                finally {
                    try { Os.close(sink); }
                    catch (Exception failure) { uncertain.set(true); throw failure; }
                }
            } catch (Exception failure) {
                try { close(); } catch (Exception cleanup) { failure.addSuppressed(cleanup); }
                throw failure;
            }
        }
        @Override public void close() throws Exception {
            System.out.flush(); System.err.flush(); Exception failed = null;
            FileDescriptor[] saved = {stdout, stderr}; stdout = null; stderr = null;
            for (int i = 0; i < saved.length; i++) if (saved[i] != null) {
                try { Os.dup2(saved[i], i + 1); } catch (Exception failure) { failed = failure; }
                try { Os.close(saved[i]); } catch (Exception failure) { failed = failure; }
            }
            if (failed != null) { uncertain.set(true); throw new WarmRunner.Undrained(); }
        }
    }
}
