/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app;

import android.os.Build;
import android.os.Process;
import android.os.SystemClock;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import dalvik.system.PathClassLoader;
import java.io.File;
import java.io.FileInputStream;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import org.json.JSONObject;

/** Test-only bootstrap. In particular, this loader has no application/native class references. */
public final class RetiredSelectionFixtureMain {
    static final String PRODUCT = "org.locallore.app.draftprocessverify";
    static final String SCOPE = "locallore_retired_fixture_v1";
    static final String LIBRARY = "lib/x86_64/liblocallore_android.so";
    private static final long APK_CAP = 128L * 1024 * 1024;
    private RetiredSelectionFixtureMain() { }

    public static void main(String[] args) {
        final long entered = SystemClock.uptimeMillis();
        Thread watchdog = new Thread(() -> {
            try { Thread.sleep(15_000); } catch (InterruptedException ignored) { return; }
            // Only this owned app_process is terminated. No process-name signalling or children.
            Runtime.getRuntime().halt(124);
        }, "retired-fixture-deadline");
        watchdog.setDaemon(true);
        watchdog.start();
        String stage = "ARGUMENTS";
        String result;
        try {
            require(args.length == 11);
            require(args[0].matches("load|probe|retire") && args[1].matches("[0-9a-f]{16}"));
            require(args[2].matches("[1-9][0-9]{0,8}") && Integer.parseInt(args[2]) == Process.myUid());
            require(args[3].matches("[0-9a-f]{64}") && args[4].matches("[0-9a-f]{64}"));
            for (int i = 6; i <= 9; i++) require(args[i].matches("[A-Za-z0-9_-]{1,64}"));
            require(args[10].matches("0|[1-9][0-9]{0,8}"));
            if (args[0].equals("load")) {
                require(Arrays.equals(Arrays.copyOfRange(args, 6, 11),
                    new String[] {"load_a", "load_b", "main", "load_child", "0"}));
            } else {
                require(args[6].compareTo(args[7]) < 0 && !args[8].equals(args[9]));
                require(Integer.parseInt(args[10]) > 0);
            }
            stage = "PLATFORM";
            require(Build.VERSION.SDK_INT == 35 && Build.SUPPORTED_ABIS.length > 0
                && Build.SUPPORTED_ABIS[0].equals("x86_64"));
            File home = new File("/data/user/0/" + PRODUCT);
            require(home.equals(home.getCanonicalFile())
                && new File(Os.readlink("/proc/self/cwd")).getCanonicalFile().equals(home));
            owned(home, true);
            stage = "CLASSPATH";
            String value = System.getenv("CLASSPATH");
            require(value != null && value.length() <= 4096);
            String[] paths = value.split(":", -1);
            require(paths.length == 2 && !paths[0].equals(paths[1]));
            File test = apk(paths[0], PRODUCT + ".test");
            File product = apk(paths[1], PRODUCT);
            require(args[5].equals(product.getPath() + "!/lib/x86_64"));
            stage = "APK_HASH";
            String testHash = hashFile(test, APK_CAP), productHash = hashFile(product, APK_CAP);
            require(productHash.equals(args[3]) && testHash.equals(args[4]));
            stage = "NATIVE_ZIP";
            requireStoredAligned(product);
            String libraryHash;
            try (ZipFile zip = new ZipFile(product)) {
                ZipEntry entry = zip.getEntry(LIBRARY);
                require(entry != null && entry.getMethod() == ZipEntry.STORED
                    && entry.getSize() > 0 && entry.getSize() <= 64L * 1024 * 1024
                    && entry.getSize() == entry.getCompressedSize());
                try (java.io.InputStream input = zip.getInputStream(entry)) {
                    libraryHash = hash(input, entry.getSize());
                }
            }
            require(hashFile(test, APK_CAP).equals(testHash) && hashFile(product, APK_CAP).equals(productHash));
            stage = "CHILD_LOADER";
            ClassLoader boot = ClassLoader.getSystemClassLoader().getParent();
            require(boot != null);
            PathClassLoader loader = new PathClassLoader(value, args[5], boot);
            Class<?> worker = Class.forName("org.locallore.app.RetiredSelectionFixtureWorker", true, loader);
            require(worker.getClassLoader() == loader);
            Object returned = worker.getMethod("run", String[].class, String.class, long.class)
                .invoke(null, args, libraryHash, entered);
            require(returned instanceof String);
            result = (String) returned;
            require(result.getBytes(StandardCharsets.UTF_8).length + 1 <= 4096 && !result.contains("\n")
                && !result.contains("\r"));
        } catch (Throwable ignored) {
            result = failure(args, stage);
        }
        System.out.println(result);
        System.out.flush();
        // app_process has no runner to keep alive; watchdog remains armed until actual process exit.
    }

    static String failure(String[] args, String stage) {
        try {
            String mode = args.length > 0 && args[0].matches("load|probe|retire") ? args[0] : "invalid";
            String run = args.length > 1 && args[1].matches("[0-9a-f]{16}") ? args[1] : "0000000000000000";
            return new JSONObject().put("version", 1).put("scope", SCOPE).put("mode", mode)
                .put("run_id", run).put("status", "failed").put("stage", stage).toString();
        } catch (Exception impossible) { return "{\"status\":\"failed\",\"stage\":\"ENCODING\"}"; }
    }

    static void require(boolean condition) { if (!condition) throw new IllegalStateException("fixture_refused"); }

    static File owned(File file, boolean directory) throws Exception {
        require(file.isAbsolute() && file.equals(file.getCanonicalFile()));
        StructStat stat = Os.lstat(file.getPath());
        require(stat.st_uid == Process.myUid() && (directory ? OsConstants.S_ISDIR(stat.st_mode)
            : OsConstants.S_ISREG(stat.st_mode)));
        return file;
    }

    private static File apk(String path, String packageName) throws Exception {
        File file = new File(path);
        require(file.isAbsolute() && file.equals(file.getCanonicalFile()) && file.getName().equals("base.apk"));
        File folder = file.getParentFile();
        require(folder != null && folder.getName().startsWith(packageName + "-")
            && folder.getPath().startsWith("/data/app/"));
        for (File part = file; part != null; part = part.getParentFile()) {
            require(!OsConstants.S_ISLNK(Os.lstat(part.getPath()).st_mode));
        }
        StructStat stat = Os.lstat(path);
        require(OsConstants.S_ISREG(stat.st_mode) && !file.canWrite() && stat.st_size > 0
            && stat.st_size <= APK_CAP && file.canRead());
        return file;
    }

    static String sha(byte[] bytes) throws Exception { return hex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
    static String hashFile(File file, long cap) throws Exception {
        StructStat before = Os.lstat(file.getPath());
        require(OsConstants.S_ISREG(before.st_mode) && before.st_size > 0 && before.st_size <= cap);
        String result;
        try (FileInputStream input = new FileInputStream(file)) {
            StructStat held = Os.fstat(input.getFD());
            require(held.st_dev == before.st_dev && held.st_ino == before.st_ino && held.st_size == before.st_size);
            result = hash(input, before.st_size);
            StructStat afterHeld = Os.fstat(input.getFD());
            require(afterHeld.st_dev == held.st_dev && afterHeld.st_ino == held.st_ino && afterHeld.st_size == held.st_size
                && afterHeld.st_mtime == held.st_mtime && afterHeld.st_ctime == held.st_ctime);
        }
        StructStat after = Os.lstat(file.getPath());
        require(after.st_dev == before.st_dev && after.st_ino == before.st_ino && after.st_size == before.st_size
            && after.st_mtime == before.st_mtime && after.st_ctime == before.st_ctime);
        return result;
    }
    private static String hash(java.io.InputStream input, long exact) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] buffer = new byte[16384]; long count = 0; int n;
        while ((n = input.read(buffer)) != -1) { count += n; require(count <= exact); digest.update(buffer, 0, n); }
        require(count == exact); return hex(digest.digest());
    }
    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(64);
        for (byte b : bytes) out.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
        return out.toString();
    }

    /** Inspect ZIP offsets, without extracting an executable into writable app data. */
    private static void requireStoredAligned(File apk) throws Exception {
        try (RandomAccessFile f = new RandomAccessFile(apk, "r")) {
            long length = f.length(), eocd = -1;
            require(length > 22);
            for (long at = length - 22; at >= Math.max(0, length - 65557); at--) {
                f.seek(at);
                if (u32(f) == 0x06054b50L) {
                    f.seek(at + 20); int comment = u16(f);
                    if (at + 22 + comment == length) { eocd = at; break; }
                }
            }
            require(eocd >= 0); f.seek(eocd + 4);
            require(u16(f) == 0 && u16(f) == 0);
            int diskCount = u16(f), count = u16(f);
            long size = u32(f), offset = u32(f);
            require(count > 0 && count < 65535 && count == diskCount && offset + size == eocd);
            long cursor = offset; int found = 0;
            for (int i = 0; i < count; i++) {
                require(cursor + 46 <= eocd); f.seek(cursor); require(u32(f) == 0x02014b50L);
                f.seek(cursor + 8); int flags = u16(f), method = u16(f);
                f.seek(cursor + 20); long compressed = u32(f), uncompressed = u32(f);
                int names = u16(f), extras = u16(f), comments = u16(f);
                f.seek(cursor + 42); long local = u32(f);
                require(names > 0 && cursor + 46L + names + extras + comments <= eocd);
                byte[] name = new byte[names]; f.readFully(name);
                if (Arrays.equals(name, LIBRARY.getBytes(StandardCharsets.US_ASCII))) {
                    found++; require((flags & 1) == 0 && method == 0 && compressed == uncompressed
                        && uncompressed > 0 && uncompressed <= 64L * 1024 * 1024 && local + 30 < offset);
                    f.seek(local); require(u32(f) == 0x04034b50L);
                    f.seek(local + 6); require((u16(f) & 1) == 0 && u16(f) == 0);
                    f.seek(local + 26); int localNames = u16(f), localExtras = u16(f);
                    require(localNames == names); byte[] localName = new byte[localNames]; f.readFully(localName);
                    long data = local + 30L + localNames + localExtras;
                    require(Arrays.equals(name, localName) && data % 4096 == 0 && data + uncompressed <= offset);
                }
                cursor += 46L + names + extras + comments;
            }
            require(found == 1 && cursor == offset + size);
        }
    }
    private static int u16(RandomAccessFile f) throws Exception { return f.readUnsignedByte() | f.readUnsignedByte() << 8; }
    private static long u32(RandomAccessFile f) throws Exception { return (long) u16(f) | (long) u16(f) << 16; }

    static JSONObject json(byte[] bytes, int cap) throws Exception {
        require(bytes.length > 0 && bytes.length <= cap);
        String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
        new Shape(text).document();
        return new JSONObject(text);
    }
    static void keys(JSONObject o, String... names) {
        Set<String> found = new HashSet<>(); java.util.Iterator<String> it = o.keys();
        while (it.hasNext()) found.add(it.next());
        require(found.equals(new HashSet<>(Arrays.asList(names))));
    }
    static long number(JSONObject o, String key) throws Exception {
        Object v = o.get(key); require(v instanceof Integer || v instanceof Long);
        long n = ((Number) v).longValue(); require(n >= 0); return n;
    }
    static String text(JSONObject o, String key) throws Exception { Object v = o.get(key); require(v instanceof String); return (String) v; }
    static boolean bool(JSONObject o, String key) throws Exception { Object v = o.get(key); require(v instanceof Boolean); return (Boolean) v; }

    /** Strict lexical JSON plus recursive duplicate-key refusal before JSONObject's coercive parser. */
    private static final class Shape {
        final String text; int at;
        Shape(String text) { this.text = text; }
        void document() throws Exception { ws(); value(0); ws(); require(at == text.length()); }
        void ws() { while (at < text.length() && " \t\r\n".indexOf(text.charAt(at)) >= 0) at++; }
        char take() { require(at < text.length()); return text.charAt(at++); }
        void value(int depth) throws Exception {
            require(depth <= 16); ws(); require(at < text.length()); char c = text.charAt(at);
            if (c == '{') {
                at++; ws(); Set<String> names = new HashSet<>();
                if (at < text.length() && text.charAt(at) == '}') { at++; return; }
                do { ws(); String key = string(); require(names.add(key)); ws(); require(take() == ':'); value(depth + 1); ws();
                    c = take(); if (c == '}') return; require(c == ',');
                } while (true);
            }
            if (c == '[') {
                at++; ws(); if (at < text.length() && text.charAt(at) == ']') { at++; return; }
                do { value(depth + 1); ws(); c = take(); if (c == ']') return; require(c == ','); } while (true);
            }
            if (c == '"') { string(); return; }
            int start = at;
            while (at < text.length() && ",]} \t\r\n".indexOf(text.charAt(at)) < 0) at++;
            String token = text.substring(start, at);
            require(token.matches("true|false|null|-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?"));
        }
        String string() throws Exception {
            require(take() == '"'); StringBuilder out = new StringBuilder();
            while (true) {
                char c = take(); if (c == '"') break; require(c >= 32);
                if (c == '\\') {
                    c = take();
                    switch (c) {
                        case '"': case '\\': case '/': break;
                        case 'b': c = '\b'; break; case 'f': c = '\f'; break;
                        case 'n': c = '\n'; break; case 'r': c = '\r'; break; case 't': c = '\t'; break;
                        case 'u':
                            int n = 0; for (int i = 0; i < 4; i++) {
                                char h = take(); int d = "0123456789abcdef".indexOf(Character.toLowerCase(h));
                                require(h <= 127 && d >= 0); n = n * 16 + d;
                            }
                            c = (char) n; break;
                        default: require(false);
                    }
                }
                out.append(c);
            }
            for (int i = 0; i < out.length(); i++) {
                char c = out.charAt(i);
                if (Character.isHighSurrogate(c)) require(++i < out.length() && Character.isLowSurrogate(out.charAt(i)));
                else require(!Character.isLowSurrogate(c));
            }
            return out.toString();
        }
    }
}
