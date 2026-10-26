/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.processverify;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.Activity;
import android.app.Instrumentation;
import android.app.UiAutomation;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.InstrumentationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.os.Bundle;
import android.os.Build;
import android.os.ParcelFileDescriptor;
import android.os.Process;
import android.os.SystemClock;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * A self-targeted, framework-only external oracle. It never instruments the
 * product, substitutes a factory or writes its files. Result observations and
 * the fixture are PRIVATE evidence: callers must not publish raw identities.
 */
public final class ProcessRestoreInstrumentation extends Instrumentation {
    private static final String SELF = "org.locallore.app.draftprocesscontroller";
    private static final String PRODUCT = "org.locallore.app.draftprocessverify";
    private static final String ACTIVITY = "org.locallore.app.MainActivity";
    private static final String CASE = "restore_non_default";
    private static final String CHILD_CASE = "restore_child_branch";
    private static final String RETIRED_CASE = "restore_retired_child";
    private static final String RETAINED_CASE = "restore_retained_parent";
    private static final String FIXTURE_TEST = PRODUCT + ".test";
    private static final String HELPER = "org.locallore.app.RetiredSelectionFixtureMain";
    private static final String HELPER_EXIT = "LL_RETIRED_HELPER_EXIT_V1=";
    private static final String UNAVAILABLE_NOTICE = "Previously selected timeline is unavailable. Review the library before sending.";
    private static final String RUN_EXTRA = "locallore.process.run_id";
    private static final String PROBE_SCOPE = "locallore_process_verify_v2";
    private static final String FIXTURE_SCOPE = "locallore_process_fixture_v1";
    private static final String RESULT_SCOPE = "locallore_process_controller_v1";
    private static final String DIALOGUE = "SYNTHETIC process-restoration dialogue: Mira, café and lanterns 🌊.\n"
            + "Still unsent until my explicit Send.";
    private static final String CHILD_DIALOGUE = "SYNTHETIC child-timeline draft: Mira, snow 雪 and café 🌊.\n"
            + "Unsent until one explicit child Send.";
    private static final String RETAINED_PREFIX = "SYNTHETIC retained-parent prefix: Mira, snow \u96ea and caf\u00e9 \ud83c\udf0a.\n"
            + "Keep this accepted statement in the retained child.";
    private static final String UNREACHABLE_TAIL = "SYNTHETIC unreachable-parent tail: Mira, this belongs only to the parent after the child fork.";
    private static final String PARENT_DRAFT = "SYNTHETIC retired-parent unsent draft: Mira, lanterns \ud83c\udf0a and snow \u96ea.\n"
            + "Never send or restore this after retirement.";
    private static final String TRANSPORT_CONTROL = "LocalLore transport: \"double\" and 'single', café 🌊.\n"
            + "Second original line; literal $value and backslash \\.";
    private static final long CASE_MS = 120_000;
    private static final int PROBE_CAP = 4096;
    private static final int SHELL_CAP = 131_072;
    private static final int NODE_CAP = 1024;
    private static final int WINDOW_CAP = 32;
    private static final String EXIT = "LL_PROCESS_EXIT_V1=";
    private static final String PENDING = "LL_PROCESS_PROBE_PENDING_V1\n";
    private static final Pattern ID = Pattern.compile("[A-Za-z0-9_-]{1,64}");
    private static final Pattern HEX16 = Pattern.compile("[0-9a-f]{16}");
    private static final Pattern HEX64 = Pattern.compile("[0-9a-f]{64}");
    private static final String[] OPS = {"workspace", "branches", "resume", "create", "open", "play_snapshot",
            "free_text", "submit", "prepare", "commit", "cancel", "other", "story_template", "create_named"};
    // The producer explicitly ignores ONLY these known non-gameplay wire ops:
    // close, capabilities, model_status. Every arbitrary unknown op is "other".
    private static final String[] GAME = {"free_text", "submit", "prepare", "commit", "cancel", "other"};

    private enum Stage { ARGUMENTS, IDENTITY, TRANSPORT, FIXTURE, LAUNCH, CATALOG, PARENT_SEND, FORK_SETUP, EDIT, FIRST_SAVE,
        FIRST_KILL, FIRST_RESTORE, NATIVE_REREAD, SEND, SECOND_SAVE, SECOND_KILL,
        SECOND_RESTORE, CANONICAL_REREAD, HELPER_LOAD, HELPER_PROBE, HELPER_RETIRE, DONE }
    private enum Reason { NONE, ARGUMENTS, IDENTITY, SIGNATURE, APK, FIXTURE, CATALOG,
        UI, DEADLINE, SHELL_IO, SHELL_TIMEOUT, SHELL_REFUSED, PROBE, SAVED_ACK,
        TASK_NOT_STOPPED, PROCESS, SCOPE, DRAFT, AUTOMATIC_OPERATION, CANONICAL,
        PROOF_SIZE, HELPER, INTERNAL }
    private static final class Refused extends RuntimeException {
        final Reason reason;
        Refused(Reason reason) { super(reason.name()); this.reason = reason; }
    }
    private interface Condition { boolean ready() throws Exception; }
    private enum WorkspaceRead { MISSING, EMPTY, VALID, MALFORMED_NONEMPTY }

    private Bundle arguments;
    private UiAutomation automation;
    private long deadline;
    private String runId;
    private String productSha;
    private boolean reuse;
    private boolean childCase;
    private boolean retiredCase;
    private boolean retainedCase;
    private String caseName = CASE;
    private Workspace childScope;
    private Workspace retainedParent, retainedChild;
    private String retainedPreservedSha;
    private JSONObject childFixture;
    private String fixtureTestSha, productApk, fixtureTestApk, librarySha;
    private int fixtureTestUid;
    private String lastHelperSha;
    private Integer lastHelperExit;
    private Workspace retiredRestoreHint;
    private JSONObject loadGate;
    private final JSONArray retirementHelpers = new JSONArray();
    private final JSONArray retainedHelpers = new JSONArray();
    private final Set<String> helperDispatches = new HashSet<>();
    private int productUid;
    private int controllerUid;
    private String signatureSha;
    private volatile Stage stage = Stage.ARGUMENTS;
    private final AtomicBoolean finished = new AtomicBoolean();
    private int checks;
    private int deaths;
    // Text-free, independently sampled diagnostics; not an atomic UI snapshot.
    private volatile WorkspaceRead lastWorkspaceRead = WorkspaceRead.MISSING;
    private volatile int lastWorkspaceUtf16Length;
    private Fixture fixture;
    private final JSONArray observations = new JSONArray();
    private final JSONArray terminalObservations = new JSONArray();

    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        arguments = args == null ? new Bundle() : new Bundle(args);
        start();
    }

    @Override public void onStart() {
        deadline = SystemClock.uptimeMillis() + CASE_MS;
        ScheduledExecutorService watchdog = Executors.newSingleThreadScheduledExecutor(task -> {
            Thread thread = new Thread(task, "process-proof-deadline"); thread.setDaemon(true); return thread;
        });
        watchdog.schedule(() -> finishResult(false, Reason.DEADLINE), CASE_MS, TimeUnit.MILLISECONDS);
        Reason reason = Reason.NONE;
        boolean passed = false;
        try {
            parseArguments();
            stage = Stage.IDENTITY;
            guardInstallation();
            automation = getUiAutomation(UiAutomation.FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES);
            need(automation != null, Reason.IDENTITY);
            AccessibilityServiceInfo info = automation.getServiceInfo();
            need(info != null, Reason.IDENTITY);
            info.flags |= AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
                    | AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
            automation.setServiceInfo(info);
            stage = Stage.TRANSPORT;
            checked(shell("printf '%s\\n' " + quote(TRANSPORT_CONTROL), 1024)
                    .equals(TRANSPORT_CONTROL + "\n"), Reason.SHELL_IO);
            Workspace parserControl = decodeWorkspace("Rules · fantasy_v1 · synthetic_story / main · head 0");
            checked(parserControl.story.equals("synthetic_story") && parserControl.branch.equals("main")
                    && parserControl.head == 0, Reason.CANONICAL);
            checked(workspaceHeadControl(), Reason.CANONICAL);
            checked(stoppedTaskControls(), Reason.TASK_NOT_STOPPED);
            if (retiredCase || retainedCase) {
                stage = Stage.HELPER_LOAD;
                JSONObject loaded = runHelper("load", 0);
                loadGate = new JSONObject().put("proof_sha256", lastHelperSha).put("pid", loaded.get("pid"))
                        .put("uid", loaded.get("uid")).put("started_uptime_ms", loaded.get("started_uptime_ms"));
            }
            stage = Stage.FIXTURE;
            File stored = fixtureFile();
            if (reuse) fixture = readFixture(stored);
            else need(!stored.exists() && !Files.isSymbolicLink(stored.toPath()), Reason.FIXTURE);
            stage = Stage.LAUNCH;
            launch();
            Probe initial = awaitCreated(null, false);
            observe(initial);
            if (reuse) readyProduct();
            else readyEmptyProduct(initial);
            // Receipts are cumulative in a live product process. An owned
            // failed pre-Send attempt may already have created this exact pair.
            long initialCreates = creationAttempts(latest(initial));
            checked(initialCreates == 0 || (reuse && initialCreates == 2), Reason.CATALOG);
            if (retainedCase) {
                runRetained(stored, initial);
                passed = true;
            } else if (childCase) {
                runChild(stored, initial);
                passed = true;
            } else {
            stage = Stage.CATALOG;
            if (reuse) verifyFixtureCatalog();
            else createFixture(stored, initial);
            checked(fixture != null && fixture.a.story.compareTo(fixture.b.story) < 0, Reason.FIXTURE);
            Workspace chosen = select(fixture.b.story);
            checked(chosen.same(fixture.b, 0), Reason.CANONICAL);
            stage = Stage.EDIT;
            selectDialogue();
            setDraft();
            verifyDraft();
            Probe unsubmitted = latest(initial);
            checked(creationAttempts(unsubmitted) == initialCreates + (reuse ? 0 : 2), Reason.CATALOG);
            noGameplay(unsubmitted);
            stage = Stage.FIRST_SAVE;
            Probe saved = backgroundAndSave(initial, fixture.b);
            stage = Stage.FIRST_KILL;
            killSaved(saved);
            stage = Stage.FIRST_RESTORE;
            launch();
            Probe first = awaitCreated(saved, true);
            observe(first);
            readyProduct();
            checked(workspace().same(fixture.b, 0), Reason.SCOPE);
            verifyDraft();
            Probe firstUnsubmitted = latest(first);
            checked(creationAttempts(firstUnsubmitted) == 0, Reason.AUTOMATIC_OPERATION);
            noGameplay(firstUnsubmitted);
            stage = Stage.NATIVE_REREAD;
            Probe beforeReselect = latest(first);
            checked(select(fixture.b.story).same(fixture.b, 0), Reason.CANONICAL);
            Probe reread = awaitReadIncrease(first, beforeReselect);
            noGameplay(reread);
            verifyDraft();
            stage = Stage.SEND;
            click("play-send"); // The sole Send action in the entire two-death case.
            waitUntil(() -> {
                Workspace w = maybeRevealedWorkspace();
                return w != null && w.same(fixture.b, 1);
            }, 15_000, Reason.CANONICAL);
            readyProduct(); // Do not HOME while the legitimate post-commit UI is busy.
            verifyDraft();
            Probe sent = latest(first);
            checked(sent.op("free_text") == 1 && sent.op("submit") == 0
                    && sent.op("prepare") == 1 && sent.op("commit") == 1
                    && sent.op("cancel") == 0 && sent.op("other") == 0,
                    Reason.AUTOMATIC_OPERATION);
            stage = Stage.SECOND_SAVE;
            Probe savedAgain = backgroundAndSave(first, fixture.b);
            stage = Stage.SECOND_KILL;
            killSaved(savedAgain);
            stage = Stage.SECOND_RESTORE;
            launch();
            Probe second = awaitCreated(savedAgain, true);
            observe(second);
            readyProduct();
            checked(workspace().same(fixture.b, 1), Reason.SCOPE);
            verifyDraft();
            Probe secondUnsubmitted = latest(second);
            checked(creationAttempts(secondUnsubmitted) == 0, Reason.AUTOMATIC_OPERATION);
            noGameplay(secondUnsubmitted);
            stage = Stage.CANONICAL_REREAD;
            List<String> ids = catalog();
            checked(ids.equals(fixture.ids()), Reason.CATALOG);
            verifyMenuHead(fixture.a.story, 0);
            verifyMenuHead(fixture.b.story, 1);
            // Reading A's fresh native catalog head does not navigate away and
            // intentionally discard B's editor under the product's scope policy.
            checked(select(fixture.b.story).same(fixture.b, 1), Reason.CANONICAL);
            verifyDraft();
            noGameplay(latest(second));
            guardInstallation();
            checked(deaths == 2, Reason.PROCESS);
            stage = Stage.DONE;
            passed = true;
            }
        } catch (Refused failure) {
            reason = failure.reason;
        } catch (Throwable failure) {
            // Never expose Throwable text, classes, causes, stack traces or UI dumps.
            reason = Reason.INTERNAL;
        }
        finishResult(passed, reason);
        watchdog.shutdownNow();
    }

    private void finishResult(boolean passed, Reason reason) {
        if (passed && SystemClock.uptimeMillis() >= deadline) { passed = false; reason = Reason.DEADLINE; }
        if (!finished.compareAndSet(false, true)) return;
        Bundle result = new Bundle();
        try {
            String json = proof(passed, reason).toString();
            need(json.getBytes(StandardCharsets.UTF_8).length <= PROBE_CAP, Reason.PROOF_SIZE);
            result.putString("proof", json);
        } catch (Throwable failure) {
            passed = false;
            result.putString("proof", "{\"version\":1,\"scope\":\"" + RESULT_SCOPE
                    + "\",\"case\":\"" + caseName + "\",\"run_id\":null,\"status\":\"failed\","
                    + "\"stage\":\"" + stage.name() + "\",\"reason\":\"PROOF_SIZE\",\"checks\":0,\"process_deaths\":0}");
        }
        finish(passed ? Activity.RESULT_OK : Activity.RESULT_CANCELED, result);
    }

    private void parseArguments() throws Exception {
        Object c = arguments.get("case"), r = arguments.get("run_id"), h = arguments.get("product_sha256"), group = arguments.get("cohort");
        Set<String> keys = new HashSet<>(Arrays.asList("case", "run_id", "product_sha256", "cohort"));
        if (RETIRED_CASE.equals(c) || RETAINED_CASE.equals(c)) keys.add("fixture_test_sha256");
        need(arguments.keySet().equals(keys), Reason.ARGUMENTS);
        need((CASE.equals(c) || CHILD_CASE.equals(c) || RETIRED_CASE.equals(c) || RETAINED_CASE.equals(c)) && r instanceof String && HEX16.matcher((String) r).matches()
                && h instanceof String && HEX64.matcher((String) h).matches()
                && ("create".equals(group) || "reuse".equals(group)), Reason.ARGUMENTS);
        runId = (String) r; productSha = (String) h; reuse = "reuse".equals(group);
        retiredCase = RETIRED_CASE.equals(c); retainedCase = RETAINED_CASE.equals(c);
        childCase = CHILD_CASE.equals(c) || retiredCase || retainedCase;
        caseName = retainedCase ? RETAINED_CASE : retiredCase ? RETIRED_CASE : childCase ? CHILD_CASE : CASE;
        need(!childCase || !reuse, Reason.ARGUMENTS);
        if (retiredCase || retainedCase) {
            Object pin = arguments.get("fixture_test_sha256");
            need(pin instanceof String && HEX64.matcher((String) pin).matches(), Reason.ARGUMENTS);
            fixtureTestSha = (String) pin;
        }
        checked(DIALOGUE.getBytes(StandardCharsets.UTF_8).length < 2048, Reason.ARGUMENTS);
        need(CHILD_DIALOGUE.getBytes(StandardCharsets.UTF_8).length < 2048, Reason.ARGUMENTS);
        if (retainedCase) {
            need(digest(DIALOGUE.getBytes(StandardCharsets.UTF_8)).equals("a8cb95c8145359ad7fadad52d0df311551fab161e1e386a66c87d29fa50a3a55")
                    && digest(RETAINED_PREFIX.getBytes(StandardCharsets.UTF_8)).equals("d0e88260d20e867ca12440419d4c32fed67d07d9ef45da74251c0ab38869cc5a")
                    && digest(UNREACHABLE_TAIL.getBytes(StandardCharsets.UTF_8)).equals("d07a57c72b9f4a81eedf539fbfdc184ba40fa416dc92f67261c9e54e1a55f9e4")
                    && digest(PARENT_DRAFT.getBytes(StandardCharsets.UTF_8)).equals("4bbd7fc7d2efea6368acc0fd343b01d8fcb5e38a6af3ae4eb847a197e64b54cb"), Reason.ARGUMENTS);
            need(RETAINED_PREFIX.getBytes(StandardCharsets.UTF_8).length < 2048 && UNREACHABLE_TAIL.length() < 2048
                    && PARENT_DRAFT.getBytes(StandardCharsets.UTF_8).length < 2048, Reason.ARGUMENTS);
        }
    }

    @SuppressWarnings("deprecation")
    private void guardInstallation() throws Exception {
        need(SELF.equals(getContext().getPackageName()) && SELF.equals(getTargetContext().getPackageName()), Reason.IDENTITY);
        controllerUid = Process.myUid();
        need(controllerUid >= 10_000 && controllerUid < 100_000, Reason.IDENTITY);
        PackageManager pm = getContext().getPackageManager();
        InstrumentationInfo instrument = pm.getInstrumentationInfo(
                new ComponentName(SELF, ProcessRestoreInstrumentation.class.getName()), 0);
        need(SELF.equals(instrument.targetPackage) && SELF.equals(instrument.packageName), Reason.IDENTITY);
        ApplicationInfo own = pm.getApplicationInfo(SELF, 0);
        ApplicationInfo product = pm.getApplicationInfo(PRODUCT, 0);
        need(own.uid == controllerUid && product.uid != controllerUid && product.uid >= 10_000
                && product.uid < 100_000 && (own.flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0
                && (product.flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0,
                Reason.IDENTITY);
        if (productUid != 0) need(productUid == product.uid, Reason.IDENTITY);
        productUid = product.uid;
        need(pm.checkSignatures(SELF, PRODUCT) == PackageManager.SIGNATURE_MATCH, Reason.SIGNATURE);
        PackageInfo ownInfo = pm.getPackageInfo(SELF, PackageManager.GET_SIGNATURES);
        PackageInfo productInfo = pm.getPackageInfo(PRODUCT, PackageManager.GET_SIGNATURES);
        Signature[] ownSignatures = ownInfo.signatures, productSignatures = productInfo.signatures;
        need(ownSignatures != null && ownSignatures.length == 1 && productSignatures != null
                && productSignatures.length == 1 && ownSignatures[0].equals(productSignatures[0]), Reason.SIGNATURE);
        String observedSignature = digest(ownSignatures[0].toByteArray());
        if (signatureSha != null) need(signatureSha.equals(observedSignature), Reason.SIGNATURE);
        signatureSha = observedSignature;
        need(product.splitSourceDirs == null || product.splitSourceDirs.length == 0, Reason.APK);
        File apk = new File(product.sourceDir).getCanonicalFile();
        need(apk.isFile() && apk.length() > 0 && apk.length() <= 128L * 1024 * 1024, Reason.APK);
        long size = apk.length(), modified = apk.lastModified();
        MessageDigest sha = MessageDigest.getInstance("SHA-256");
        try (FileInputStream input = new FileInputStream(apk)) {
            byte[] block = new byte[1024 * 1024]; long left = size;
            while (left > 0) {
                timeLeft(); int n = input.read(block, 0, (int) Math.min(left, block.length));
                need(n > 0, Reason.APK); sha.update(block, 0, n); left -= n;
            }
            need(input.read() == -1, Reason.APK);
        }
        checked(size == apk.length() && modified == apk.lastModified() && hex(sha.digest()).equals(productSha), Reason.APK);
        if (retiredCase || retainedCase) guardFixtureTest(pm, product, apk, ownSignatures[0]);
    }

    private void launch() {
        timeLeft();
        Intent intent = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
                .setComponent(new ComponentName(PRODUCT, ACTIVITY)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra(RUN_EXTRA, runId);
        getContext().startActivity(intent);
    }

    @SuppressWarnings("deprecation")
    private void guardFixtureTest(PackageManager pm, ApplicationInfo product, File apk, Signature signature) throws Exception {
        checked(Build.VERSION.SDK_INT == 35 && Process.is64Bit() && Build.SUPPORTED_64_BIT_ABIS.length > 0
                && "x86_64".equals(Build.SUPPORTED_64_BIT_ABIS[0]), Reason.IDENTITY);
        need((product.flags & ApplicationInfo.FLAG_EXTRACT_NATIVE_LIBS) == 0
                && new File(product.sourceDir).getAbsoluteFile().equals(apk) && !apk.canWrite(), Reason.APK);
        ApplicationInfo test = pm.getApplicationInfo(FIXTURE_TEST, 0);
        need(test.uid >= 10_000 && test.uid < 100_000 && test.uid != productUid && test.uid != controllerUid
                && (test.flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0
                && (test.splitSourceDirs == null || test.splitSourceDirs.length == 0), Reason.IDENTITY);
        need(fixtureTestUid == 0 || fixtureTestUid == test.uid, Reason.IDENTITY); fixtureTestUid = test.uid;
        PackageInfo info = pm.getPackageInfo(FIXTURE_TEST, PackageManager.GET_SIGNATURES);
        need(pm.checkSignatures(SELF, FIXTURE_TEST) == PackageManager.SIGNATURE_MATCH
                && info.signatures != null && info.signatures.length == 1 && signature.equals(info.signatures[0]), Reason.SIGNATURE);
        File testApk = new File(test.sourceDir).getCanonicalFile();
        need(new File(test.sourceDir).getAbsoluteFile().equals(testApk) && !testApk.canWrite(), Reason.APK);
        checked(apkHash(testApk).equals(fixtureTestSha), Reason.APK);
        String appPath = apk.getAbsolutePath(), testPath = testApk.getAbsolutePath();
        need((productApk == null || productApk.equals(appPath)) && (fixtureTestApk == null || fixtureTestApk.equals(testPath)), Reason.APK);
        String nativeSha;
        try (ZipFile zip = new ZipFile(apk)) {
            ZipEntry entry = zip.getEntry("lib/x86_64/liblocallore_android.so");
            need(entry != null && !entry.isDirectory() && entry.getMethod() == ZipEntry.STORED
                    && entry.getSize() > 0 && entry.getSize() <= 128L * 1024 * 1024, Reason.APK);
            MessageDigest sha = MessageDigest.getInstance("SHA-256");
            try (InputStream input = zip.getInputStream(entry)) {
                byte[] block = new byte[1024 * 1024]; long left = entry.getSize();
                while (left > 0) {
                    timeLeft(); int n = input.read(block, 0, (int) Math.min(left, block.length));
                    need(n > 0, Reason.APK); sha.update(block, 0, n); left -= n;
                }
                need(input.read() == -1, Reason.APK);
            }
            nativeSha = hex(sha.digest());
        }
        need(librarySha == null || librarySha.equals(nativeSha), Reason.APK);
        productApk = appPath; fixtureTestApk = testPath; librarySha = nativeSha;
    }

    private String apkHash(File file) throws Exception {
        need(file.isFile() && !Files.isSymbolicLink(file.toPath()) && file.length() > 0
                && file.length() <= 128L * 1024 * 1024, Reason.APK);
        long size = file.length(), modified = file.lastModified();
        MessageDigest sha = MessageDigest.getInstance("SHA-256");
        try (InputStream input = new FileInputStream(file)) {
            byte[] block = new byte[1024 * 1024]; long left = size;
            while (left > 0) {
                timeLeft(); int n = input.read(block, 0, (int) Math.min(left, block.length));
                need(n > 0, Reason.APK); sha.update(block, 0, n); left -= n;
            }
            need(input.read() == -1, Reason.APK);
        }
        need(size == file.length() && modified == file.lastModified(), Reason.APK);
        return hex(sha.digest());
    }

    private JSONObject runHelper(String mode, int savedPid) throws Exception {
        need((retiredCase || retainedCase) && Arrays.asList("load", "probe", "retire").contains(mode)
                && helperDispatches.add(mode), Reason.HELPER);
        lastHelperExit = null; // This attempt has no observed exit until its exact footer is parsed.
        need(!anyProductProcess() && (savedPid == 0 || !pidExists(savedPid)), Reason.PROCESS);
        String a = mode.equals("load") ? "load_a" : fixture.a.story;
        String b = mode.equals("load") ? "load_b" : fixture.b.story;
        String parent = mode.equals("load") ? "main" : fixture.b.branch;
        String child = mode.equals("load") ? "load_child" : retainedCase ? retainedParent.branch : childScope.branch;
        String retained = mode.equals("load") ? "load_retained" : retainedCase ? retainedChild.branch : null;
        need(mode.equals("load") ? savedPid == 0 : savedPid > 0, Reason.HELPER);
        String scopeSha = digest(((retainedCase ? "2\n" : "1\n") + a + "\n" + b + "\n" + parent + "\n" + child + "\n"
                + (retainedCase ? retained + "\n3\n2\n" : "")).getBytes(StandardCharsets.UTF_8));
        String nativePath = productApk + "!/lib/x86_64";
        File output = helperEvidence(mode);
        need(!output.exists() && !Files.isSymbolicLink(output.toPath()), Reason.FIXTURE);
        File transportOutput = new File(output.getParentFile(), mode + "-transport-v1.bin");
        need(!transportOutput.exists() && !Files.isSymbolicLink(transportOutput.toPath()), Reason.FIXTURE);
        String[] args = {mode, runId, Integer.toString(productUid), productSha, fixtureTestSha, nativePath,
                a, b, parent, child, Integer.toString(savedPid)};
        StringBuilder invocation = new StringBuilder("export CLASSPATH=").append(quote(fixtureTestApk + ":" + productApk))
                .append("; exec /system/bin/app_process / --nice-name=").append(PRODUCT)
                .append(retainedCase ? ":retained-parent-fixture " : ":retirement-fixture ").append(HELPER);
        for (String arg : args) invocation.append(' ').append(quote(arg));
        if (retainedCase) invocation.append(' ').append(quote(retained)).append(" '3' '2'");
        String command = "( run-as " + PRODUCT + " --user 0 sh -c " + quote(invocation.toString())
                + " 2>&1; helper_rc=$?; printf '\\n" + HELPER_EXIT + "%d\\n' \"$helper_rc\"; exit 0 )";
        long began = SystemClock.uptimeMillis();
        String raw = shell(command, PROBE_CAP + 64, transportOutput);
        String marker = "\n" + HELPER_EXIT;
        int footer = raw.indexOf(marker);
        need(footer >= 0 && footer == raw.lastIndexOf(marker), Reason.HELPER);
        String body = raw.substring(0, footer), exit = raw.substring(footer + marker.length());
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        need(bytes.length <= PROBE_CAP, Reason.HELPER);
        persistHelperBytes(output, bytes, PROBE_CAP);
        lastHelperSha = digest(bytes); // Exact single-line merged body, including its original final LF.
        need(exit.matches("[0-9]{1,3}\\n"), Reason.HELPER);
        int observedExit = Integer.parseInt(exit.substring(0, exit.length() - 1));
        need(observedExit <= 255, Reason.HELPER); lastHelperExit = observedExit;
        need(observedExit == 0, Reason.HELPER);
        need(body.endsWith("\n") && body.indexOf('\n') == body.length() - 1 && body.indexOf('\r') < 0, Reason.HELPER);
        JSONObject proof = strictObject(bytes);
        exact(proof, "version", "scope", "mode", "run_id", "status", "stage", "pid", "uid", "started_uptime_ms",
                "product_sha256", "test_sha256", "library_sha256", "scope_sha256", "commit_attempts", "archive_closed", "workspace_closed", "before", "after");
        String expectedStage = mode.equals("load") ? "LOAD_COMPLETE" : mode.equals("probe") ? "PROBE_CLOSED" : "RETIRED_CLOSED";
        need(number(proof, "version", 1, 1) == 1 && (retainedCase ? "locallore_retained_parent_fixture_v1" : "locallore_retired_fixture_v1").equals(proof.get("scope"))
                && mode.equals(proof.get("mode")) && runId.equals(proof.get("run_id")) && "passed".equals(proof.get("status"))
                && expectedStage.equals(proof.get("stage")) && productSha.equals(proof.get("product_sha256"))
                && fixtureTestSha.equals(proof.get("test_sha256")) && librarySha.equals(proof.get("library_sha256"))
                && scopeSha.equals(proof.get("scope_sha256")) && number(proof, "uid", 10_000, 99_999) == productUid
                && bool(proof, "archive_closed") && bool(proof, "workspace_closed"), Reason.HELPER);
        int pid = (int) number(proof, "pid", 1, Integer.MAX_VALUE);
        need(pid != Process.myPid() && pid != savedPid, Reason.PROCESS);
        // This is the entry clock, not OS process-start attestation.
        number(proof, "started_uptime_ms", began, SystemClock.uptimeMillis());
        number(proof, "commit_attempts", mode.equals("retire") ? 1 : 0, mode.equals("retire") ? 1 : 0);
        if (mode.equals("load")) need(proof.get("before") == JSONObject.NULL && proof.get("after") == JSONObject.NULL, Reason.HELPER);
        else {
            if (retainedCase) {
                retainedHelperState(proof.getJSONObject("before"), false);
                retainedHelperState(proof.getJSONObject("after"), mode.equals("retire"));
            } else {
                helperState(proof.getJSONObject("before"), false);
                helperState(proof.getJSONObject("after"), mode.equals("retire"));
            }
        }
        checked(!pidExists(pid) && !anyProductProcess() && (savedPid == 0 || !pidExists(savedPid)), Reason.PROCESS);
        if (!mode.equals("load")) {
            if (retainedCase) retainedHelpers.put(new JSONObject().put("mode", mode).put("pid", pid).put("uid", productUid)
                    .put("started_uptime_ms", proof.get("started_uptime_ms")).put("proof_sha256", lastHelperSha));
            else retirementHelpers.put(proof);
        }
        return proof;
    }

    private File helperEvidence(String mode) throws Exception {
        File root = fixtureFile().getParentFile();
        File directory = new File(root, "helpers-" + runId);
        if (!directory.exists()) Files.createDirectory(directory.toPath());
        need(!Files.isSymbolicLink(directory.toPath()) && Files.isDirectory(directory.toPath(), LinkOption.NOFOLLOW_LINKS)
                && directory.getCanonicalFile().getParentFile().equals(root), Reason.FIXTURE);
        return new File(directory, mode + "-v1.json");
    }

    private void persistHelperBytes(File output, byte[] bytes, int cap) throws Exception {
        need(bytes.length <= cap && (cap == PROBE_CAP || cap == PROBE_CAP + 64), Reason.HELPER);
        try (FileChannel channel = FileChannel.open(output.toPath(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(bytes);
            while (buffer.hasRemaining()) { timeLeft(); channel.write(buffer); }
            channel.force(true);
        }
    }

    private static void helperState(JSONObject state, boolean retired) throws Exception {
        exact(state, "other_head", "parent_head", "target_head", "target_active");
        number(state, "other_head", 0, 0); number(state, "parent_head", 1, 1);
        need(bool(state, "target_active") == !retired, Reason.HELPER);
        if (retired) need(state.get("target_head") == JSONObject.NULL, Reason.HELPER);
        else number(state, "target_head", 1, 1);
    }

    private void retainedHelperState(JSONObject state, boolean retired) throws Exception {
        exact(state, "other_head", "root_head", "target_head", "target_physical_head", "target_active",
                "retained_head", "retained_active", "preserved_sha256");
        number(state, "other_head", 0, 0); number(state, "root_head", 1, 1);
        number(state, "target_physical_head", retired ? 2 : 3, retired ? 2 : 3);
        number(state, "retained_head", 2, 2);
        need(bool(state, "target_active") == !retired && bool(state, "retained_active"), Reason.HELPER);
        if (retired) need(state.get("target_head") == JSONObject.NULL, Reason.HELPER);
        else number(state, "target_head", 3, 3);
        String preserved = string(state, "preserved_sha256"); need(HEX64.matcher(preserved).matches(), Reason.HELPER);
        if (retainedPreservedSha == null) retainedPreservedSha = preserved;
        else need(retainedPreservedSha.equals(preserved), Reason.HELPER);
    }

    private void readyProduct() throws Exception {
        readyHeader();
        AccessibilityNodeInfo provider = tag("inference-provider");
        try { checked(nodeText(provider).equals("Local Rust engine · fake inference"), Reason.UI); }
        finally { provider.recycle(); }
    }

    private void readyHeader() throws Exception {
        waitUntil(() -> findAndRecycle("story-list"), 8_000, Reason.UI);
        AccessibilityNodeInfo resetTag = tag("reset-demo"); resetTag.recycle();
        waitUntil(() -> {
            AccessibilityNodeInfo reset = find("reset-demo");
            if (reset == null) return false;
            try { return reset.isEnabled(); } finally { reset.recycle(); }
        }, 10_000, Reason.UI);
    }

    private void readyEmptyProduct(Probe identity) throws Exception {
        readyHeader();
        AccessibilityNodeInfo provider = tag("inference-provider");
        try { checked(nodeText(provider).equals("Local Rust engine · text inference unavailable"), Reason.UI); }
        finally { provider.recycle(); }
        checked(maybeWorkspace() == null && !findAndRecycle("saved-library"), Reason.FIXTURE);
        AccessibilityNodeInfo empty = tag("empty-library");
        try { checked(nodeText(empty).equals("No saved stories. Choose New story to begin."), Reason.FIXTURE); }
        finally { empty.recycle(); }
        Probe initial = latest(identity);
        checked(creationAttempts(initial) == 0, Reason.AUTOMATIC_OPERATION);
        noGameplay(initial);
    }

    private void createFixture(File file, Probe identity) throws Exception {
        need(findAndRecycle("saved-library") == false && maybeWorkspace() == null, Reason.FIXTURE);
        createThroughReview(identity);
        Workspace first = awaitWorkspace(null, 0);
        readyProduct();
        checked(catalog().equals(Collections.singletonList(first.story)), Reason.CATALOG);
        checked(select(first.story).same(first, 0), Reason.CANONICAL);
        createThroughReview(identity);
        Workspace second = awaitWorkspace(first.story, 0);
        List<String> ids = catalog();
        checked(ids.size() == 2 && ids.contains(first.story) && ids.contains(second.story), Reason.CATALOG);
        Workspace a = select(ids.get(0)), b = select(ids.get(1));
        checked(a.head == 0 && b.head == 0 && !a.story.equals(b.story), Reason.CANONICAL);
        fixture = new Fixture(a, b, runId, productSha, controllerUid, productUid, signatureSha);
        if (file != null) writeFixture(file, fixture.json());
    }

    /** New UI consent only; the original diagnostic check count is unchanged. */
    private void createThroughReview(Probe identity) throws Exception {
        Probe before = latest(identity);
        click("reset-demo"); // Existing counted action, exactly once.
        waitUntil(() -> {
            if (!findAndRecycle("story-creation-dialog")) return false;
            if (findAndRecycle("story-creation-preview")) return true;
            AccessibilityNodeInfo content = find("story-creation-content");
            if (content == null) return false;
            try { if (content.isScrollable()) content.performAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD); }
            finally { content.recycle(); }
            return false;
        }, 5_000, Reason.UI);
        AccessibilityNodeInfo revealed = tag("story-creation-confirm"); revealed.recycle();
        waitUntil(() -> {
            AccessibilityNodeInfo node = find("story-creation-confirm");
            if (node == null) return false;
            try { return node.isEnabled() && productNode(node); } finally { node.recycle(); }
        }, 5_000, Reason.UI);
        need(sameCreations(before, latest(identity)), Reason.AUTOMATIC_OPERATION);
        AccessibilityNodeInfo confirm = tag("story-creation-confirm");
        try {
            need(confirm.isEnabled() && confirm.isVisibleToUser() && productNode(confirm), Reason.UI);
            need(confirm.performAction(AccessibilityNodeInfo.ACTION_CLICK), Reason.UI);
        } finally { confirm.recycle(); }
        waitUntil(() -> !findAndRecycle("story-creation-dialog"), 5_000, Reason.UI);
    }

    private void writeFixture(File file, JSONObject value) throws Exception {
        byte[] bytes = value.toString().getBytes(StandardCharsets.UTF_8);
        need(bytes.length <= PROBE_CAP, Reason.FIXTURE);
        try (FileChannel channel = FileChannel.open(file.toPath(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(bytes);
            while (buffer.hasRemaining()) channel.write(buffer);
            channel.force(true);
        }
    }

    private void verifyFixtureCatalog() throws Exception {
        checked(catalog().equals(fixture.ids()), Reason.FIXTURE);
        checked(select(fixture.a.story).same(fixture.a, 0), Reason.FIXTURE);
        checked(select(fixture.b.story).same(fixture.b, 0), Reason.FIXTURE);
    }

    /** Child setup is create-only. Any partial mutation requires a new owned cohort. */
    private void runChild(File stored, Probe initial) throws Exception {
        stage = Stage.CATALOG;
        checked(!reuse && creationAttempts(latest(initial)) == 0, Reason.FIXTURE);
        createFixture(null, initial);
        checked(fixture != null && fixture.a.story.compareTo(fixture.b.story) < 0, Reason.FIXTURE);
        checked(select(fixture.b.story).same(fixture.b, 0), Reason.CANONICAL);
        stage = Stage.PARENT_SEND;
        selectDialogue();
        setDraft(DIALOGUE);
        checked(workspace().same(fixture.b, 0), Reason.CANONICAL);
        noGameplay(latest(initial));
        click("play-send"); // One parent setup Send; never replayed after a failure.
        awaitScopeHead(fixture.b, 1);
        readyProduct();
        acceptedText("message-body-1", DIALOGUE);
        Probe parent = latest(initial);
        checked(creationAttempts(parent) == 2, Reason.CATALOG);
        normalSendGameplay(parent);
        childScope = forkThroughUi(fixture.b, 1);
        String child = childScope.branch;
        stage = Stage.EDIT;
        selectDialogue();
        setDraft();
        verifyDraft();
        acceptedText("message-body-1", DIALOGUE);
        Probe setup = latest(initial);
        checked(creationAttempts(setup) == 2, Reason.CATALOG);
        setupGameplay(setup);
        // roots_at_creation records historical observations, not current B's head.
        JSONObject value = fixture.json();
        Object roots = value.remove("stories");
        value.put("scope", retiredCase ? "locallore_retired_process_fixture_v1" : "locallore_child_process_fixture_v1")
                .put("case", caseName)
                .put("roots_at_creation", roots)
                .put("parent", new Workspace(fixture.b.story, fixture.b.branch, 1).json())
                .put("child", childScope.json())
                .put("parent_text_sha256", digest(DIALOGUE.getBytes(StandardCharsets.UTF_8)))
                .put("child_draft_sha256", digest(CHILD_DIALOGUE.getBytes(StandardCharsets.UTF_8)));
        if (retiredCase) value.put("fixture_test_sha256", fixtureTestSha);
        writeFixture(stored, value);
        childFixture = value;
        if (retiredCase) { runRetired(initial); return; }
        stage = Stage.FIRST_SAVE;
        Probe saved = backgroundAndSave(initial, childScope);
        stage = Stage.FIRST_KILL;
        killSaved(saved);
        stage = Stage.FIRST_RESTORE;
        launch();
        Probe first = awaitCreated(saved, true);
        observe(first);
        readyProduct();
        checked(workspace().same(childScope, 1), Reason.SCOPE);
        verifyDraft();
        acceptedText("message-body-1", DIALOGUE);
        Probe restored = latest(first);
        checked(creationAttempts(restored) == 0, Reason.AUTOMATIC_OPERATION);
        noGameplay(restored);
        stage = Stage.NATIVE_REREAD;
        Probe beforeReselect = latest(first);
        checked(selectTimeline(child).same(childScope, 1), Reason.CANONICAL);
        noGameplay(awaitReadIncrease(first, beforeReselect));
        verifyDraft();
        stage = Stage.SEND;
        click("play-send"); // The sole child Send, in a fresh process.
        awaitScopeHead(childScope, 2);
        readyProduct();
        verifyDraft();
        acceptedText("message-body-1", DIALOGUE);
        acceptedText("message-body-3", CHILD_DIALOGUE);
        normalSendGameplay(latest(first));
        stage = Stage.SECOND_SAVE;
        Probe savedAgain = backgroundAndSave(first, childScope);
        stage = Stage.SECOND_KILL;
        killSaved(savedAgain);
        stage = Stage.SECOND_RESTORE;
        launch();
        Probe second = awaitCreated(savedAgain, true);
        observe(second);
        readyProduct();
        checked(workspace().same(childScope, 2), Reason.SCOPE);
        verifyDraft();
        acceptedText("message-body-1", DIALOGUE);
        acceptedText("message-body-3", CHILD_DIALOGUE);
        Probe finalState = latest(second);
        checked(creationAttempts(finalState) == 0, Reason.AUTOMATIC_OPERATION);
        noGameplay(finalState);
        stage = Stage.CANONICAL_REREAD;
        checked(catalog().equals(fixture.ids()), Reason.CATALOG);
        verifyMenuHead(fixture.a.story, 0);
        verifyMenuHead(fixture.b.story, 1);
        dismissMenu(); // Never select B's parent merely to inspect its head.
        checked(workspace().same(childScope, 2), Reason.SCOPE);
        verifyTimelineHeads(child);
        Probe beforeFinalReselect = latest(second);
        checked(selectTimeline(child).same(childScope, 2), Reason.CANONICAL);
        noGameplay(awaitReadIncrease(second, beforeFinalReselect));
        verifyDraft();
        acceptedText("message-body-1", DIALOGUE);
        acceptedText("message-body-3", CHILD_DIALOGUE);
        noGameplay(latest(second));
        guardInstallation();
        checked(deaths == 2, Reason.PROCESS);
        stage = Stage.DONE;
    }

    private void runRetained(File stored, Probe initial) throws Exception {
        stage = Stage.CATALOG;
        checked(!reuse && creationAttempts(latest(initial)) == 0, Reason.FIXTURE);
        createFixture(null, initial);
        checked(fixture != null && fixture.a.story.compareTo(fixture.b.story) < 0, Reason.FIXTURE);
        checked(select(fixture.b.story).same(fixture.b, 0), Reason.CANONICAL);
        stage = Stage.PARENT_SEND;
        selectDialogue(); setDraft(DIALOGUE);
        checked(workspace().same(fixture.b, 0), Reason.CANONICAL);
        noGameplay(latest(initial));
        click("play-send");
        awaitScopeHead(fixture.b, 1); readyProduct();
        acceptedText("message-body-1", DIALOGUE);
        normalSendGameplay(latest(initial));
        retainedParent = forkThroughUi(fixture.b, 1);
        forgetConfirmedForkThroughUi(fixture.b, retainedParent, initial);
        stage = Stage.SEND;
        selectDialogue(); setDraft(RETAINED_PREFIX);
        click("play-send");
        awaitScopeHead(retainedParent, 2); readyProduct();
        acceptedText("message-body-1", DIALOGUE); acceptedText("message-body-3", RETAINED_PREFIX);
        retainedChild = forkThroughUi(retainedParent, 2);
        checked(!retainedChild.branch.equals(fixture.b.branch) && !retainedChild.branch.equals(retainedParent.branch), Reason.SCOPE);
        Probe beforeParent = latest(initial);
        checked(selectTimeline(retainedParent.branch).same(retainedParent, 2), Reason.CANONICAL);
        awaitReadIncrease(initial, beforeParent); readyProduct();
        stage = Stage.SEND;
        selectDialogue(); setDraft(UNREACHABLE_TAIL);
        click("play-send");
        awaitScopeHead(retainedParent, 3); readyProduct();
        retainedParent = new Workspace(fixture.b.story, retainedParent.branch, 3);
        acceptedText("message-body-1", DIALOGUE); acceptedText("message-body-3", RETAINED_PREFIX);
        acceptedText("message-body-5", UNREACHABLE_TAIL);
        openTimelines();
        List<String> active = new ArrayList<>(Arrays.asList(fixture.b.branch, retainedParent.branch, retainedChild.branch));
        Collections.sort(active); checked(timelineIds().equals(active), Reason.CATALOG);
        checked(label("timeline-" + fixture.b.branch).equals(fixture.b.branch + " · original · revision 1 · 0 uncommitted"), Reason.CANONICAL);
        checked(label("timeline-" + retainedParent.branch).equals(retainedParent.branch + " · from " + fixture.b.branch + " at 1 · revision 3 · 0 uncommitted"), Reason.CANONICAL);
        checked(label("timeline-" + retainedChild.branch).equals(retainedChild.branch + " · from " + retainedParent.branch + " at 2 · revision 2 · 0 uncommitted"), Reason.CANONICAL);
        Probe beforeDraft = latest(initial);
        checked(selectTimeline(retainedParent.branch).same(retainedParent, 3), Reason.SCOPE);
        awaitReadIncrease(initial, beforeDraft); readyProduct();
        stage = Stage.EDIT;
        selectDialogue(); setDraft(); verifyDraft();
        checked(workspace().same(retainedParent, 3), Reason.CANONICAL);
        Probe setup = latest(initial);
        checked(creationAttempts(setup) == 2, Reason.CATALOG); retainedSetupGameplay(setup);
        JSONObject value = fixture.json(); Object roots = value.remove("stories");
        value.put("scope", "locallore_retained_parent_process_fixture_v1").put("case", RETAINED_CASE)
                .put("fixture_test_sha256", fixtureTestSha).put("roots_at_creation", roots)
                .put("root", new Workspace(fixture.b.story, fixture.b.branch, 1).json())
                .put("parent", retainedParent.json()).put("retained_child", retainedChild.json())
                .put("root_text_sha256", digest(DIALOGUE.getBytes(StandardCharsets.UTF_8)))
                .put("retained_prefix_sha256", digest(RETAINED_PREFIX.getBytes(StandardCharsets.UTF_8)))
                .put("unreachable_tail_sha256", digest(UNREACHABLE_TAIL.getBytes(StandardCharsets.UTF_8)))
                .put("parent_draft_sha256", digest(PARENT_DRAFT.getBytes(StandardCharsets.UTF_8)));
        writeFixture(stored, value); childFixture = value;
        runUnavailableFallback(initial, retainedParent);
    }

    private void awaitScopeHead(Workspace expected, long head) throws Exception {
        waitUntil(() -> { Workspace w = maybeRevealedWorkspace(); return w != null && w.same(expected, head); },
                15_000, Reason.CANONICAL);
        checked(workspace().same(expected, head), Reason.CANONICAL);
    }

    /** Forget only the exact confirmed recovery hint, with its separate consent. */
    private void forgetConfirmedForkThroughUi(Workspace parent, Workspace child, Probe initial) throws Exception {
        Probe before = latest(initial);
        setupGameplay(before);
        click("fork-timeline");
        waitUntil(() -> findAndRecycle("fork-dialog") && findAndRecycle("fork-lookup-only"), 5_000, Reason.UI);
        checked(label("fork-parent").equals("Requested parent: " + parent.story + " / " + parent.branch), Reason.SCOPE);
        checked(label("fork-child").equals("Fixed child ID: " + child.branch), Reason.SCOPE);
        click("fork-forget-consent");
        waitUntil(() -> {
            AccessibilityNodeInfo node = find("fork-forget-consent");
            if (node == null) return false;
            try { return node.isCheckable() && node.isChecked(); } finally { node.recycle(); }
        }, 5_000, Reason.UI);
        click("fork-forget");
        waitUntil(() -> findAndRecycle("fork-boundary") && findAndRecycle("fork-review-boundary")
                && !findAndRecycle("fork-lookup-only") && !findAndRecycle("fork-forget"), 5_000, Reason.UI);
        checked(label("fork-review-boundary").equals("Prepare new request"), Reason.UI);
        click("fork-close");
        waitUntil(() -> !findAndRecycle("fork-dialog"), 5_000, Reason.UI);
        readyProduct();
        checked(workspace().same(child, 1), Reason.CANONICAL);
        acceptedText("message-body-1", DIALOGUE);
        Probe after = latest(initial);
        checked(sameGame(before, after) && sameCreations(before, after), Reason.AUTOMATIC_OPERATION);
        setupGameplay(after);
    }

    /** Only the two source-fixed fixture boundaries are permitted; no boundary edit. */
    private Workspace forkThroughUi(Workspace parent, int head) throws Exception {
        need(head == 1 || head == 2, Reason.ARGUMENTS);
        stage = Stage.FORK_SETUP;
        click("fork-timeline");
        waitUntil(() -> findAndRecycle("fork-dialog") && findAndRecycle("fork-scroll"), 5_000, Reason.UI);
        checked(label("fork-parent").equals("Requested parent: " + parent.story + " / " + parent.branch), Reason.SCOPE);
        AccessibilityNodeInfo boundary = tag("fork-boundary");
        try { checked(nodeText(boundary).equals(Integer.toString(head)), Reason.CANONICAL); }
        finally { boundary.recycle(); }
        String childLabel = label("fork-child");
        String prefix = "Fixed child ID: ";
        checked(childLabel.startsWith(prefix), Reason.CANONICAL);
        String child = childLabel.substring(prefix.length());
        checked(ID.matcher(child).matches() && !child.equals(parent.branch), Reason.CANONICAL);
        click("fork-review-boundary");
        checked(label("fork-child").equals(childLabel), Reason.SCOPE);
        click("fork-consent");
        waitUntil(() -> {
            AccessibilityNodeInfo node = find("fork-consent");
            if (node == null) return false;
            try { return node.isCheckable() && node.isChecked(); } finally { node.recycle(); }
        }, 5_000, Reason.UI);
        AccessibilityNodeInfo consent = tag("fork-consent");
        try { checked(consent.isCheckable() && consent.isChecked(), Reason.UI); }
        finally { consent.recycle(); }
        click("fork-confirm");
        final String outcome = "Fork confirmed: " + parent.story + " / " + child + " · fork " + head + " · current head " + head;
        waitUntil(() -> {
            AccessibilityNodeInfo node = find("fork-outcome");
            if (node == null) { scrollOnce("fork-scroll", AccessibilityNodeInfo.ACTION_SCROLL_FORWARD); return false; }
            try { return menuItemLabel(node).equals(outcome); } finally { node.recycle(); }
        }, 15_000, Reason.CANONICAL);
        checked(label("fork-outcome").equals(outcome), Reason.CANONICAL);
        click("fork-resume");
        Workspace childScope = new Workspace(parent.story, child, head);
        awaitScopeHead(childScope, head);
        readyProduct();
        return childScope;
    }

    private void runRetired(Probe initial) throws Exception {
        runUnavailableFallback(initial, childScope);
    }

    private void runUnavailableFallback(Probe initial, Workspace unavailable) throws Exception {
        retiredRestoreHint = unavailable;
        stage = Stage.FIRST_SAVE;
        Probe saved = backgroundAndSave(initial, unavailable);
        stage = Stage.FIRST_KILL;
        killSaved(saved);
        stage = Stage.HELPER_PROBE;
        runHelper("probe", saved.pid); // Prepare/close only; a new helper owns the actual commit.
        stage = Stage.HELPER_RETIRE;
        runHelper("retire", saved.pid); // Exactly one commit; any uncertainty exits this case.
        stage = Stage.FIRST_RESTORE;
        launch();
        Probe first = awaitCreated(saved, true);
        observe(first);
        readyProduct();
        checked(workspace().same(fixture.a, 0), Reason.SCOPE);
        checked(label("notice").equals(UNAVAILABLE_NOTICE), Reason.SCOPE);
        verifyBlank();
        noAcceptedMessages();
        Probe fallback = latest(first);
        checked(creationAttempts(fallback) == 0, Reason.AUTOMATIC_OPERATION);
        noGameplay(fallback);
        stage = Stage.NATIVE_REREAD;
        Probe beforeRead = latest(first);
        checked(select(fixture.a.story).same(fixture.a, 0), Reason.CANONICAL);
        noGameplay(awaitReadIncrease(first, beforeRead));
        readyProduct();
        checked(!label("notice").equals(UNAVAILABLE_NOTICE), Reason.SCOPE);
        verifyBlank();
        noAcceptedMessages();
        retiredRestoreHint = fixture.a;
        stage = Stage.SECOND_SAVE;
        Probe savedAgain = backgroundAndSave(first, fixture.a);
        stage = Stage.SECOND_KILL;
        killSaved(savedAgain);
        stage = Stage.SECOND_RESTORE;
        launch();
        Probe second = awaitCreated(savedAgain, true);
        observe(second);
        readyProduct();
        checked(workspace().same(fixture.a, 0), Reason.SCOPE);
        checked(!label("notice").equals(UNAVAILABLE_NOTICE), Reason.SCOPE);
        verifyBlank();
        noAcceptedMessages();
        Probe reopened = latest(second);
        checked(creationAttempts(reopened) == 0, Reason.AUTOMATIC_OPERATION);
        noGameplay(reopened);
        stage = Stage.CANONICAL_REREAD;
        checked(catalog().equals(fixture.ids()), Reason.CATALOG);
        verifyMenuHead(fixture.a.story, 0); verifyMenuHead(fixture.b.story, 1);
        checked(select(fixture.b.story).same(fixture.b, 1), Reason.CANONICAL);
        acceptedText("message-body-1", DIALOGUE);
        openTimelines();
        if (retainedCase) {
            List<String> active = new ArrayList<>(Arrays.asList(fixture.b.branch, retainedChild.branch)); Collections.sort(active);
            checked(timelineIds().equals(active), Reason.CATALOG);
            checked(label("timeline-" + fixture.b.branch).equals(fixture.b.branch + " · original · revision 1 · 0 uncommitted"), Reason.CANONICAL);
            checked(label("timeline-" + retainedChild.branch).equals(retainedChild.branch + " · from " + retainedParent.branch + " at 2 · revision 2 · 0 uncommitted"), Reason.CANONICAL);
            Probe beforeRetained = latest(second);
            checked(selectTimeline(retainedChild.branch).same(retainedChild, 2), Reason.CANONICAL);
            noGameplay(awaitReadIncrease(second, beforeRetained)); readyProduct();
            acceptedText("message-body-1", DIALOGUE); acceptedText("message-body-3", RETAINED_PREFIX);
            scanMessageBodies(new HashSet<>(Arrays.asList("message-body-1", "message-body-2", "message-body-3", "message-body-4")));
            acceptedText("message-body-1", DIALOGUE); acceptedText("message-body-3", RETAINED_PREFIX);
        } else {
            checked(timelineIds().equals(Collections.singletonList(fixture.b.branch)), Reason.CATALOG);
            checked(label("timeline-" + fixture.b.branch).equals(fixture.b.branch + " · original · revision 1 · 0 uncommitted"), Reason.CANONICAL);
            Probe beforeParent = latest(second);
            checked(selectTimeline(fixture.b.branch).same(fixture.b, 1), Reason.CANONICAL);
            noGameplay(awaitReadIncrease(second, beforeParent));
            readyProduct();
            acceptedText("message-body-1", DIALOGUE);
        }
        Probe beforeReturn = latest(second);
        checked(select(fixture.a.story).same(fixture.a, 0), Reason.CANONICAL);
        noGameplay(awaitReadIncrease(second, beforeReturn));
        readyProduct(); verifyBlank(); noAcceptedMessages();
        checked(!label("notice").equals(UNAVAILABLE_NOTICE), Reason.SCOPE);
        noGameplay(latest(second));
        guardInstallation();
        checked(deaths == 2 && (retainedCase ? retainedHelpers.length() : retirementHelpers.length()) == 2 && loadGate != null, Reason.PROCESS);
        stage = Stage.DONE;
    }

    private void verifyBlank() throws Exception {
        AccessibilityNodeInfo input = tag("play-input"); input.recycle();
        waitUntil(() -> {
            AccessibilityNodeInfo text = find("play-input"), action = find("play-kind-action"), dialogue = find("play-kind-dialogue");
            try { return text != null && text.isEditable() && text.isEnabled() && nodeText(text).isEmpty()
                    && action != null && selected(action) && dialogue != null && !selected(dialogue); }
            finally { if (text != null) text.recycle(); if (action != null) action.recycle(); if (dialogue != null) dialogue.recycle(); }
        }, 5_000, Reason.DRAFT);
        checked(true, Reason.DRAFT);
    }

    private void noAcceptedMessages() throws Exception {
        scanMessageBodies(Collections.emptySet());
    }

    private void scanMessageBodies(Set<String> allowed) throws Exception {
        // Prove both bounded scroll edges rather than equating a virtualized,
        // off-screen row with an absent row. Canonical head0 is checked separately.
        for (int direction : new int[]{AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD, AccessibilityNodeInfo.ACTION_SCROLL_FORWARD}) {
            boolean edge = false;
            for (int i = 0; i < 12; i++) {
                timeLeft(); need(!visibleUnexpectedMessage(allowed), Reason.CANONICAL);
                AccessibilityNodeInfo list = find("story-list"); need(list != null, Reason.UI);
                boolean moved;
                try { moved = list.isScrollable() && list.performAction(direction); } finally { list.recycle(); }
                SystemClock.sleep(Math.min(100, timeLeft()));
                need(!visibleUnexpectedMessage(allowed), Reason.CANONICAL);
                if (!moved) { edge = true; break; }
            }
            need(edge, Reason.UI);
        }
        checked(true, Reason.CANONICAL);
    }

    private boolean visibleUnexpectedMessage(Set<String> allowed) throws Exception {
        List<AccessibilityNodeInfo> nodes = productNodes();
        try {
            for (AccessibilityNodeInfo node : nodes) {
                String id = node.getViewIdResourceName();
                if (id != null && id.startsWith("message-body-") && node.isVisibleToUser() && !allowed.contains(id)) return true;
            }
            return false;
        } finally { recycle(nodes); }
    }

    private void normalSendGameplay(Probe probe) {
        checked(probe.op("free_text") == 1 && probe.op("submit") == 0 && probe.op("prepare") == 1
                && probe.op("commit") == 1 && probe.op("cancel") == 0 && probe.op("other") == 0,
                Reason.AUTOMATIC_OPERATION);
    }

    private void setupGameplay(Probe probe) {
        checked(probe.op("free_text") == 1 && probe.op("submit") == 0 && probe.op("prepare") == 1
                && probe.op("commit") == 1 && probe.op("cancel") == 0 && probe.op("other") == 2,
                Reason.AUTOMATIC_OPERATION);
    }

    private void retainedSetupGameplay(Probe probe) {
        checked(probe.op("free_text") == 3 && probe.op("submit") == 0 && probe.op("prepare") == 3
                && probe.op("commit") == 3 && probe.op("cancel") == 0 && probe.op("other") == 4,
                Reason.AUTOMATIC_OPERATION);
    }

    private String label(String id) throws Exception {
        AccessibilityNodeInfo node = tag(id);
        try { return menuItemLabel(node); } finally { node.recycle(); }
    }

    private void acceptedText(String id, String text) throws Exception {
        checked(label(id).equals(text), Reason.CANONICAL);
    }

    private void scrollOnce(String id, int direction) throws Exception {
        timeLeft(); AccessibilityNodeInfo list = find(id);
        if (list == null) return;
        try { if (list.isScrollable() && list.isEnabled()) list.performAction(direction); }
        finally { list.recycle(); }
    }

    private List<String> timelineIds() throws Exception {
        List<AccessibilityNodeInfo> nodes = productNodes(); List<String> ids = new ArrayList<>();
        try {
            for (AccessibilityNodeInfo node : nodes) {
                String id = node.getViewIdResourceName();
                if (id != null && id.startsWith("timeline-") && !id.equals("timeline-library") && node.isVisibleToUser()) {
                    String branch = id.substring("timeline-".length());
                    need(ID.matcher(branch).matches(), Reason.CATALOG); ids.add(branch);
                }
            }
        } finally { recycle(nodes); }
        need(ids.size() <= (retainedCase ? 3 : 2) && new HashSet<>(ids).size() == ids.size(), Reason.CATALOG);
        Collections.sort(ids); return ids;
    }

    private void openTimelines() throws Exception {
        if (!timelineIds().isEmpty()) return;
        click("timeline-library");
        waitUntil(() -> !timelineIds().isEmpty(), 5_000, Reason.CATALOG);
    }

    private Workspace selectTimeline(String branch) throws Exception {
        need(ID.matcher(branch).matches(), Reason.CATALOG); openTimelines();
        click("timeline-" + branch);
        waitUntil(() -> { Workspace w = maybeRevealedWorkspace(); return w != null && w.story.equals(fixture.b.story)
                && w.branch.equals(branch); }, 15_000, Reason.SCOPE);
        readyProduct(); return workspace();
    }

    private void verifyTimelineHeads(String child) throws Exception {
        openTimelines();
        List<String> expected = new ArrayList<>(Arrays.asList(fixture.b.branch, child)); Collections.sort(expected);
        checked(timelineIds().equals(expected), Reason.CATALOG);
        checked(label("timeline-" + fixture.b.branch).equals(fixture.b.branch + " · original · revision 1 · 0 uncommitted"), Reason.CANONICAL);
        checked(label("timeline-" + child).equals(child + " · from " + fixture.b.branch + " at 1 · revision 2 · 0 uncommitted"), Reason.CANONICAL);
    }

    private void dismissMenu() throws Exception {
        timeLeft(); need(automation.performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK), Reason.UI);
        waitUntil(() -> menuIds().isEmpty(), 5_000, Reason.UI);
    }

    private File fixtureFile() throws Exception {
        File anchor = getContext().getNoBackupFilesDir().getCanonicalFile();
        File directory = new File(anchor, retainedCase ? "process-controller-retained-parent-v1" : retiredCase ? "process-controller-retired-v1"
                : childCase ? "process-controller-child-v1" : "process-controller-v1");
        if (!directory.exists()) Files.createDirectory(directory.toPath());
        need(!Files.isSymbolicLink(directory.toPath()) && Files.isDirectory(directory.toPath(), LinkOption.NOFOLLOW_LINKS)
                && directory.getCanonicalFile().getParentFile().equals(anchor), Reason.FIXTURE);
        return new File(directory, "fixture-v1.json");
    }

    private Fixture readFixture(File file) throws Exception {
        need(!Files.isSymbolicLink(file.toPath()) && Files.isRegularFile(file.toPath(), LinkOption.NOFOLLOW_LINKS)
                && file.length() > 0 && file.length() <= PROBE_CAP, Reason.FIXTURE);
        JSONObject value = strictObject(readFile(file, PROBE_CAP));
        exact(value, "version", "scope", "case", "controller_uid", "product_uid", "signature_sha256",
                "origin_run_id", "origin_product_sha256", "stories");
        need(number(value, "version", 1, 1) == 1 && FIXTURE_SCOPE.equals(value.get("scope"))
                && CASE.equals(value.get("case")) && number(value, "controller_uid", 10_000, 99_999) == controllerUid
                && number(value, "product_uid", 10_000, 99_999) == productUid
                && signatureSha.equals(value.get("signature_sha256")), Reason.FIXTURE);
        String originRun = string(value, "origin_run_id"), originApk = string(value, "origin_product_sha256");
        need(HEX16.matcher(originRun).matches() && HEX64.matcher(originApk).matches(), Reason.FIXTURE);
        JSONArray stories = value.getJSONArray("stories"); need(stories.length() == 2, Reason.FIXTURE);
        Workspace a = storedWorkspace(stories.getJSONObject(0)), b = storedWorkspace(stories.getJSONObject(1));
        need(a.story.compareTo(b.story) < 0 && a.head == 0 && b.head == 0, Reason.FIXTURE);
        return new Fixture(a, b, originRun, originApk, controllerUid, productUid, signatureSha);
    }

    private Workspace storedWorkspace(JSONObject value) throws Exception {
        exact(value, "story", "branch", "head");
        String story = string(value, "story"), branch = string(value, "branch");
        need(ID.matcher(story).matches() && ID.matcher(branch).matches(), Reason.FIXTURE);
        return new Workspace(story, branch, number(value, "head", 0, 0));
    }

    private List<String> catalog() throws Exception {
        List<String> ids = menuIds();
        if (ids.isEmpty()) { click("saved-library"); waitUntil(() -> !menuIds().isEmpty(), 5_000, Reason.CATALOG); ids = menuIds(); }
        need(ids.size() >= 1 && ids.size() <= 2 && new HashSet<>(ids).size() == ids.size(), Reason.CATALOG);
        Collections.sort(ids); return ids;
    }

    private List<String> menuIds() throws Exception {
        List<AccessibilityNodeInfo> nodes = productNodes();
        List<String> ids = new ArrayList<>();
        try {
            for (AccessibilityNodeInfo node : nodes) {
                String id = node.getViewIdResourceName();
                if (id != null && id.startsWith("saved-story-") && node.isVisibleToUser()) {
                    String story = id.substring("saved-story-".length()); need(ID.matcher(story).matches(), Reason.CATALOG);
                    ids.add(story);
                }
            }
        } finally { recycle(nodes); }
        return ids;
    }

    private Workspace select(String story) throws Exception {
        need(ID.matcher(story).matches(), Reason.CATALOG);
        if (!findAndRecycle("saved-story-" + story)) catalog();
        click("saved-story-" + story);
        waitUntil(() -> { Workspace w = maybeRevealedWorkspace(); return w != null && w.story.equals(story); }, 15_000, Reason.CATALOG);
        readyProduct();
        return workspace();
    }

    private void verifyMenuHead(String story, long head) throws Exception {
        AccessibilityNodeInfo node = tag("saved-story-" + story);
        try { checked(menuItemLabel(node).endsWith(" · " + story + " · revision " + head), Reason.CANONICAL); }
        finally { node.recycle(); }
    }

    private String menuItemLabel(AccessibilityNodeInfo root) throws Exception {
        ArrayDeque<AccessibilityNodeInfo> pending = new ArrayDeque<>();
        ArrayDeque<Integer> depths = new ArrayDeque<>();
        pending.add(AccessibilityNodeInfo.obtain(root)); depths.add(0);
        String label = null;
        int seen = 0;
        try {
            while (!pending.isEmpty()) {
                timeLeft();
                AccessibilityNodeInfo node = pending.removeFirst();
                int depth = depths.removeFirst();
                try {
                    need(++seen <= 32 && depth <= 8 && productNode(node) && node.isVisibleToUser(), Reason.CANONICAL);
                    String text = nodeText(node);
                    need(text.length() <= 4096, Reason.CANONICAL);
                    if (!text.isEmpty()) {
                        need(label == null || label.equals(text), Reason.CANONICAL);
                        label = text; // Identical merged parent/child copies are unambiguous.
                    }
                    int children = node.getChildCount();
                    need(children <= 32 - seen - pending.size() && (children == 0 || depth < 8), Reason.CANONICAL);
                    for (int i = 0; i < children; i++) {
                        AccessibilityNodeInfo child = node.getChild(i);
                        need(child != null, Reason.CANONICAL);
                        pending.addLast(child); depths.addLast(depth + 1);
                    }
                } finally { node.recycle(); }
            }
            need(label != null, Reason.CANONICAL);
            return label;
        } finally { while (!pending.isEmpty()) pending.removeFirst().recycle(); }
    }

    private Workspace awaitWorkspace(String different, long head) throws Exception {
        // Match the existing actual-Activity native UI tests' 15-second readiness
        // allowance. The whole two-death case retains its independent 120s cap.
        waitUntil(() -> { Workspace w = maybeRevealedWorkspace(); return w != null && w.head == head && (different == null || !different.equals(w.story)); }, 15_000, Reason.CANONICAL);
        return workspace();
    }

    private Workspace workspace() throws Exception {
        AccessibilityNodeInfo node = tag("workspace-detail");
        try { Workspace value = readWorkspace(node); need(value != null, Reason.CANONICAL); return value; }
        finally { node.recycle(); }
    }

    private Workspace maybeWorkspace() throws Exception {
        AccessibilityNodeInfo node = find("workspace-detail");
        if (node == null) { lastWorkspaceUtf16Length = 0; lastWorkspaceRead = WorkspaceRead.MISSING; return null; }
        try { return readWorkspace(node); } finally { node.recycle(); }
    }

    private Workspace maybeRevealedWorkspace() throws Exception {
        Workspace value = maybeWorkspace();
        if (value != null || lastWorkspaceRead != WorkspaceRead.MISSING) return value;
        // LazyColumn can retain a lower anchor after an item disappears or Send
        // is clicked. Reveal only the fixed product header, once per bounded poll.
        timeLeft();
        AccessibilityNodeInfo list = find("story-list");
        if (list != null) {
            try {
                if (list.isScrollable() && list.isEnabled())
                    list.performAction(AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD);
            } finally { list.recycle(); }
        }
        return null; // Reacquire nodes on the next existing deadline-clipped poll.
    }

    private Workspace readWorkspace(AccessibilityNodeInfo node) {
        String text = nodeText(node);
        lastWorkspaceUtf16Length = text.length();
        if (text.isEmpty()) { lastWorkspaceRead = WorkspaceRead.EMPTY; return null; }
        lastWorkspaceRead = WorkspaceRead.MALFORMED_NONEMPTY;
        Workspace value = decodeWorkspace(text); // Nonempty malformed text still fails immediately.
        lastWorkspaceRead = WorkspaceRead.VALID;
        return value;
    }

    private Workspace decodeWorkspace(String value) {
        Matcher match = Pattern.compile("^Rules · [^\\r\\n]* · ([A-Za-z0-9_-]{1,64}) / ([A-Za-z0-9_-]{1,64}) · head ([0-9]{1,10})$").matcher(value);
        need(match.matches(), Reason.CANONICAL);
        long head;
        try { head = Long.parseLong(match.group(3)); } catch (NumberFormatException failure) { throw new Refused(Reason.CANONICAL); }
        need(head <= (retainedCase ? 3 : childCase && !retiredCase ? 2 : 1), Reason.CANONICAL);
        return new Workspace(match.group(1), match.group(2), head);
    }

    private boolean workspaceHeadControl() {
        int limit = retainedCase ? 3 : childCase && !retiredCase ? 2 : 1;
        String prefix = "Rules · fantasy_v1 · synthetic_story / main · head ";
        Workspace accepted = decodeWorkspace(prefix + limit);
        boolean refused = false;
        try { decodeWorkspace(prefix + (limit + 1)); }
        catch (Refused failure) { refused = failure.reason == Reason.CANONICAL; }
        return accepted.head == limit && refused;
    }

    private void selectDialogue() throws Exception {
        click("play-kind-dialogue"); // Exactly one action; observe the new frame before editing text.
        waitUntil(() -> {
            AccessibilityNodeInfo dialogue = null, action = null;
            try {
                dialogue = find("play-kind-dialogue"); action = find("play-kind-action");
                return dialogue != null && action != null && dialogue.isVisibleToUser() && action.isVisibleToUser()
                        && dialogue.isEnabled() && action.isEnabled() && selected(dialogue) && !selected(action);
            }
            finally { if (dialogue != null) dialogue.recycle(); if (action != null) action.recycle(); }
        }, 5_000, Reason.DRAFT);
    }

    private void setDraft() throws Exception {
        setDraft(retainedCase ? PARENT_DRAFT : childCase ? CHILD_DIALOGUE : DIALOGUE);
    }

    private void setDraft(String expected) throws Exception {
        AccessibilityNodeInfo node = tag("play-input");
        try {
            need(node.isEditable() && node.isEnabled(), Reason.DRAFT);
            Bundle text = new Bundle(); text.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, expected);
            checked(node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, text), Reason.DRAFT);
        } finally { node.recycle(); }
        waitUntil(() -> draftMatches(expected), 5_000, Reason.DRAFT);
    }

    private boolean draftMatches() throws Exception {
        return draftMatches(retainedCase ? PARENT_DRAFT : childCase ? CHILD_DIALOGUE : DIALOGUE);
    }

    private boolean draftMatches(String expected) throws Exception {
        AccessibilityNodeInfo input = find("play-input"), dialogue = find("play-kind-dialogue"), action = find("play-kind-action");
        try { return input != null && dialogue != null && action != null && expected.contentEquals(nodeText(input))
                && selected(dialogue) && !selected(action); }
        finally { if (input != null) input.recycle(); if (dialogue != null) dialogue.recycle(); if (action != null) action.recycle(); }
    }

    private void verifyDraft() throws Exception {
        // Bring the fixed editor into view without retaining a node across scrolling.
        AccessibilityNodeInfo input = tag("play-input"); input.recycle();
        waitUntil(this::draftMatches, 5_000, Reason.DRAFT);
        checked(true, Reason.DRAFT);
    }

    private static boolean selected(AccessibilityNodeInfo node) {
        return node.isSelected() || (node.isCheckable() && node.isChecked());
    }

    private Probe awaitCreated(Probe old, boolean restored) throws Exception {
        final Probe[] found = new Probe[1];
        waitUntil(() -> {
            Probe probe = readProbe("created.json");
            if (probe == null || probe.factory != 1 || !productAlive(probe.pid)) return false;
            if (old != null && (probe.sameProcess(old) || probe.task != old.task)) return false;
            if (restored && (!probe.restored || !probe.hintPresent || !probe.hint.equals(hint(retiredCase || retainedCase ? retiredRestoreHint : childCase ? childScope : fixture.b)))) return false;
            if (!restored && !reuse && probe.restored) return false;
            found[0] = probe; return true;
        }, 10_000, Reason.PROCESS);
        checked(found[0] != null, Reason.PROCESS); return found[0];
    }

    private Probe latest(Probe identity) throws Exception {
        final Probe[] found = new Probe[1];
        waitUntil(() -> {
            Probe current = readProbe("commands.json"), created = readProbe("created.json");
            if (created == null || !created.sameIdentity(identity) || created.factory != 1
                    || current == null || !current.sameIdentity(identity) || current.factory != 1) return false;
            found[0] = current.sequence < created.sequence ? created : current;
            return true;
        }, 3_000, Reason.PROBE);
        return found[0];
    }

    private void noGameplay(Probe probe) {
        for (String op : GAME) need(probe.op(op) == 0, Reason.AUTOMATIC_OPERATION);
        checked(true, Reason.AUTOMATIC_OPERATION);
    }

    private Probe awaitReadIncrease(Probe identity, Probe before) throws Exception {
        final Probe[] current = new Probe[1];
        waitUntil(() -> { Probe value = latest(identity); if (value.op("resume") > before.op("resume")
                && value.op("play_snapshot") > before.op("play_snapshot")) { current[0] = value; return true; } return false; }, 5_000, Reason.PROBE);
        checked(current[0] != null, Reason.PROBE); return current[0];
    }

    private Probe backgroundAndSave(Probe identity, Workspace expected) throws Exception {
        Probe before = latest(identity);
        if ((retiredCase || retainedCase) && deaths == 1) noGameplay(before);
        else if (retainedCase && deaths == 0) retainedSetupGameplay(before);
        else if (childCase && deaths == 0) setupGameplay(before);
        else if (deaths == 0) noGameplay(before);
        else {
            need(deaths == 1 && before.op("free_text") == 1 && before.op("submit") == 0
                    && before.op("prepare") == 1 && before.op("commit") == 1
                    && before.op("cancel") == 0 && before.op("other") == 0,
                    Reason.AUTOMATIC_OPERATION);
        }
        Probe previous = readProbe("saved.json");
        long sequence = Math.max(before.sequence, previous != null && previous.sameIdentity(identity) ? previous.sequence : 0);
        need(automation.performGlobalAction(AccessibilityService.GLOBAL_ACTION_HOME), Reason.UI);
        final Probe[] saved = new Probe[1];
        waitUntil(() -> {
            Probe p = readProbe("saved.json");
            if (p == null || !p.sameIdentity(identity) || p.sequence <= sequence || !p.hintPresent || !p.hint.equals(hint(expected)) || p.factory != 1) return false;
            need(sameGame(p, before) && sameCreations(p, before), Reason.AUTOMATIC_OPERATION);
            if (!taskStopped(identity.task)) return false;
            saved[0] = p; return true;
        }, 10_000, Reason.SAVED_ACK);
        checked(saved[0] != null, Reason.SAVED_ACK); return saved[0];
    }

    private void killSaved(Probe saved) throws Exception {
        need(saved.event.equals("saved_after_super") && taskStopped(saved.task) && productAlive(saved.pid), Reason.TASK_NOT_STOPPED);
        need(shell("am kill --user 0 " + PRODUCT, 1024).isEmpty(), Reason.SHELL_REFUSED);
        waitUntil(() -> !pidExists(saved.pid) && !anyProductProcess(), 8_000, Reason.PROCESS);
        deaths++;
        // The old producer is now gone, so its final records cannot race a
        // concurrent writer or be replaced by the new process's zero counters.
        Probe finalSaved = readProbe("saved.json"), finalCommands = readProbe("commands.json");
        checked(finalSaved != null && finalCommands != null && finalSaved.sameIdentity(saved)
                && finalCommands.sameIdentity(saved) && finalSaved.sequence >= saved.sequence
                && finalSaved.hintPresent && finalSaved.hint.equals(saved.hint)
                && finalSaved.factory == 1 && finalCommands.factory == 1, Reason.PROBE);
        terminalObservations.put(new JSONObject().put("pid", saved.pid).put("start", saved.start).put("task", saved.task)
                .put("saved_sequence", finalSaved.sequence).put("commands_sequence", finalCommands.sequence)
                .put("saved_game", gameJson(finalSaved)).put("commands_game", gameJson(finalCommands)));
        checked(sameGame(finalSaved, saved) && sameGame(finalCommands, saved)
                && sameCreations(finalSaved, saved) && sameCreations(finalCommands, saved), Reason.AUTOMATIC_OPERATION);
        checked(true, Reason.PROCESS);
    }

    private boolean taskStopped(int task) throws Exception {
        return stoppedTaskDump(shell("dumpsys activity activities", SHELL_CAP), task);
    }

    private static boolean stoppedTaskDump(String value, int task) {
        String[] lines = value.split("\n", -1);
        Pattern header = Pattern.compile(".*\\* Hist {1,2}#[0-9]+: ActivityRecord\\{[^}]*\\bu0 "
                + Pattern.quote(PRODUCT) + "/(?:" + Pattern.quote(ACTIVITY) + "|\\.MainActivity) t" + task + "(?:[ }].*)?");
        for (int i = 0; i < lines.length; i++) {
            if (!header.matcher(lines[i]).matches()) continue;
            int indent = indentation(lines[i]);
            for (int j = i + 1; j < lines.length && j <= i + 512; j++) {
                if (!lines[j].trim().isEmpty() && indentation(lines[j]) <= indent) break;
                if (lines[j].trim().matches("(?:mState|state)=STOPPED(?:\\s.*)?")) return true;
            }
        }
        return false;
    }

    private static boolean stoppedTaskControls() {
        String one = "    * Hist #0: ActivityRecord{control u0 " + PRODUCT + "/" + ACTIVITY + " t7}\n"
                + "      state=STOPPED delayedResume=false finishing=false\n";
        return stoppedTaskDump(one, 7)
                && stoppedTaskDump(one.replace("Hist #", "Hist  #"), 7)
                && !stoppedTaskDump(one, 8)
                && !stoppedTaskDump(one.replace(PRODUCT, "org.locallore.synthetic.other"), 7)
                && !stoppedTaskDump(one.replace(" u0 ", " u1 "), 7)
                && !stoppedTaskDump(one.replace("      state=", "    state="), 7)
                && !stoppedTaskDump(one.replace("STOPPED", "PAUSED"), 7)
                && !stoppedTaskDump(one.replace("Hist #", "Hist#"), 7)
                && !stoppedTaskDump(one.replace("Hist #", "Hist   #"), 7)
                && !stoppedTaskDump(one.replace("Hist #", "Hist\t#"), 7);
    }

    private static int indentation(String line) {
        int i = 0; while (i < line.length() && line.charAt(i) == ' ') i++; return i;
    }

    private static boolean sameGame(Probe left, Probe right) {
        for (String op : GAME) if (left.op(op) != right.op(op)) return false;
        return true;
    }

    private static long creationAttempts(Probe probe) {
        return probe.op("create") + probe.op("create_named");
    }

    private static boolean sameCreations(Probe left, Probe right) {
        return left.op("create") == right.op("create") && left.op("create_named") == right.op("create_named");
    }

    private static JSONObject gameJson(Probe probe) throws JSONException {
        JSONObject result = new JSONObject();
        for (String name : GAME) result.put(name, probe.op(name));
        return result;
    }

    private List<String[]> ps() throws Exception {
        String[] lines = shell("ps -A -o PID,UID,NAME", SHELL_CAP).split("\n");
        need(lines.length > 0 && Arrays.equals(lines[0].trim().split("\\s+"), new String[]{"PID", "UID", "NAME"}), Reason.PROCESS);
        List<String[]> rows = new ArrayList<>();
        for (int i = 1; i < lines.length; i++) {
            if (lines[i].trim().isEmpty()) continue;
            String[] fields = lines[i].trim().split("\\s+");
            need(fields.length == 3 && fields[0].matches("[1-9][0-9]{0,9}") && fields[1].matches("[0-9]{1,10}"), Reason.PROCESS);
            rows.add(fields);
        }
        return rows;
    }

    private boolean pidExists(int pid) throws Exception {
        for (String[] row : ps()) if (row[0].equals(Integer.toString(pid))) return true;
        return false;
    }

    private boolean anyProductProcess() throws Exception {
        for (String[] row : ps()) if (row[2].equals(PRODUCT) || row[2].startsWith(PRODUCT + ":")) return true;
        return false;
    }

    private boolean productAlive(int pid) throws Exception {
        for (String[] row : ps()) if (row[0].equals(Integer.toString(pid)))
            return row[1].equals(Integer.toString(productUid)) && row[2].equals(PRODUCT);
        return false;
    }

    private Probe readProbe(String leaf) throws Exception {
        need(leaf.equals("created.json") || leaf.equals("saved.json") || leaf.equals("commands.json"), Reason.PROBE);
        String root = "no_backup/process-verify-v1/" + runId;
        String path = root + "/" + leaf;
        String body = "test $(id -u) -eq " + productUid + " || exit 40; "
                + "if test ! -e " + path + " && test ! -L " + path + "; then printf 'LL_PROCESS_PROBE_PENDING_V1\\n'; else "
                + "test -d no_backup && test ! -L no_backup && test -d no_backup/process-verify-v1 && test ! -L no_backup/process-verify-v1 && "
                + "test -d " + root + " && test ! -L " + root + " && test $(stat -c %u " + root + ") -eq " + productUid
                + " && test -f " + path + " && test ! -L " + path + " && test $(stat -c %u " + path + ") -eq " + productUid
                + " && test $(wc -c < " + path + ") -gt 0 && test $(wc -c < " + path + ") -le 4096 && cat " + path + "; fi";
        String value = shell("run-as " + PRODUCT + " --user 0 sh -c " + quote(body), PROBE_CAP + 64);
        if (value.equals(PENDING)) return null;
        JSONObject json = strictObject(value.getBytes(StandardCharsets.UTF_8));
        exact(json, "version", "scope", "run_id", "pid", "uid", "task_id", "sequence", "process_start_uptime_ms", "event",
                "restored_state", "factory_creations", "hint_present", "hint_sha256", "operations");
        need(number(json, "version", 2, 2) == 2 && PROBE_SCOPE.equals(json.get("scope")) && runId.equals(json.get("run_id")), Reason.PROBE);
        String event = leaf.equals("created.json") ? "created" : leaf.equals("saved.json") ? "saved_after_super" : "command";
        need(event.equals(json.get("event")), Reason.PROBE);
        int pid = (int) number(json, "pid", 1, Integer.MAX_VALUE);
        need(number(json, "uid", 10_000, 99_999) == productUid, Reason.PROBE);
        int task = (int) number(json, "task_id", 0, Integer.MAX_VALUE);
        long seq = number(json, "sequence", 1, Long.MAX_VALUE), start = number(json, "process_start_uptime_ms", 0, Long.MAX_VALUE);
        int factory = (int) number(json, "factory_creations", 0, 16);
        boolean restored = bool(json, "restored_state"), hasHint = bool(json, "hint_present");
        Object hint = json.get("hint_sha256");
        need(hasHint ? hint instanceof String && HEX64.matcher((String) hint).matches() : hint == JSONObject.NULL, Reason.PROBE);
        JSONObject operations = json.getJSONObject("operations"); exact(operations, OPS);
        long[] counts = new long[OPS.length];
        for (int i = 0; i < OPS.length; i++) counts[i] = number(operations, OPS[i], 0, 4096);
        return new Probe(pid, start, task, seq, restored, factory, hasHint, hasHint ? (String) hint : "", event, counts);
    }

    private String shell(String command, int cap) throws Exception {
        return shell(command, cap, null);
    }

    private String shell(String command, int cap, File helperCapture) throws Exception {
        timeLeft(); need(cap > 0 && cap <= SHELL_CAP, Reason.SHELL_IO);
        need(helperCapture == null || ((retiredCase || retainedCase) && cap == PROBE_CAP + 64), Reason.HELPER);
        final int wireCap = helperCapture == null ? cap + 64 : PROBE_CAP + 64;
        String script = command + "; rc=$?; printf '\\n" + EXIT + "%d\\n' \"$rc\"";
        final String transport = shellTransport(script);
        AtomicReference<ParcelFileDescriptor> owned = new AtomicReference<>();
        AtomicBoolean abandoned = new AtomicBoolean();
        ExecutorService executor = Executors.newSingleThreadExecutor(task -> {
            Thread thread = new Thread(task, "process-proof-shell"); thread.setDaemon(true); return thread;
        });
        Future<byte[]> future = executor.submit(new Callable<byte[]>() {
            @Override public byte[] call() throws Exception {
                ParcelFileDescriptor fd = automation.executeShellCommand(transport);
                need(fd != null, Reason.SHELL_IO); owned.set(fd);
                if (abandoned.get()) { fd.close(); owned.compareAndSet(fd, null); throw new Refused(Reason.SHELL_TIMEOUT); }
                try (ParcelFileDescriptor.AutoCloseInputStream input = new ParcelFileDescriptor.AutoCloseInputStream(fd)) {
                    ByteArrayOutputStream output = new ByteArrayOutputStream(); byte[] block = new byte[1024]; int n;
                    while ((n = input.read(block)) != -1) {
                        need(output.size() + n <= wireCap, Reason.SHELL_IO); output.write(block, 0, n);
                    }
                    return output.toByteArray();
                } finally { owned.compareAndSet(fd, null); }
            }
        });
        try {
            byte[] bytes = future.get(Math.min(10_000, timeLeft()), TimeUnit.MILLISECONDS);
            if (helperCapture != null) persistHelperBytes(helperCapture, bytes, PROBE_CAP + 64);
            String value = utf8(bytes);
            if (helperCapture == null) value = value.replace("\r\n", "\n");
            need(value.indexOf('\r') < 0 && value.indexOf('\u000b') < 0 && value.indexOf('\u000c') < 0, Reason.SHELL_IO);
            int index = value.lastIndexOf("\n" + EXIT);
            need(index >= 0 && value.indexOf(EXIT) == index + 1 && value.endsWith("\n"), Reason.SHELL_IO);
            need(value.substring(index + 1).equals(EXIT + "0\n"), Reason.SHELL_REFUSED);
            String result = value.substring(0, index);
            need(result.getBytes(StandardCharsets.UTF_8).length <= cap, Reason.SHELL_IO);
            return result;
        } catch (TimeoutException failure) {
            throw new Refused(Reason.SHELL_TIMEOUT);
        } catch (ExecutionException failure) {
            throw new Refused(Reason.SHELL_IO);
        } finally {
            abandoned.set(true);
            ParcelFileDescriptor fd = owned.getAndSet(null);
            if (fd != null) try { fd.close(); } catch (IOException ignored) { }
            future.cancel(true); executor.shutdownNow();
        }
    }

    private static String quote(String value) { return "'" + value.replace("'", "'\\''") + "'"; }

    /**
     * UiAutomationConnection uses Runtime.exec(String), not a shell tokenizer.
     * Its third token must therefore contain no literal ASCII whitespace. The
     * fixed POSIX printf decodes UTF-8 octals, and eval receives that whole
     * decoded script as one quoted argument. This is not a selectable transport.
     */
    private static String shellTransport(String script) {
        need(script.length() <= 8192, Reason.SHELL_IO);
        byte[] bytes = script.getBytes(StandardCharsets.UTF_8);
        need(bytes.length > 0 && bytes.length <= 8192, Reason.SHELL_IO);
        StringBuilder encoded = new StringBuilder(bytes.length * 4);
        for (byte raw : bytes) {
            int value = raw & 255; need(value != 0, Reason.SHELL_IO);
            encoded.append('\\').append((char) ('0' + ((value >>> 6) & 7)))
                    .append((char) ('0' + ((value >>> 3) & 7))).append((char) ('0' + (value & 7)));
        }
        String token = "eval${IFS}\"$(printf${IFS}'" + encoded + "')\"";
        need(token.length() <= 33_024, Reason.SHELL_IO);
        for (int i = 0; i < token.length(); i++) need(token.charAt(i) > 32 && token.charAt(i) < 127, Reason.SHELL_IO);
        return "sh -c " + token;
    }

    private void click(String id) throws Exception {
        AccessibilityNodeInfo node = tag(id);
        try { need(node.isEnabled() && node.isVisibleToUser() && productNode(node), Reason.UI);
            checked(node.performAction(AccessibilityNodeInfo.ACTION_CLICK), Reason.UI); }
        finally { node.recycle(); }
    }

    private AccessibilityNodeInfo tag(String id) throws Exception {
        AccessibilityNodeInfo node = find(id); if (node != null) return node;
        for (int direction : new int[]{AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD, AccessibilityNodeInfo.ACTION_SCROLL_FORWARD}) {
            for (int i = 0; i < 12; i++) {
                timeLeft(); AccessibilityNodeInfo list = find(id.startsWith("story-creation-") ? "story-creation-content"
                        : id.startsWith("fork-") && !id.equals("fork-timeline") ? "fork-scroll" : "story-list");
                if (list == null) break;
                boolean moved;
                try { moved = list.isScrollable() && list.performAction(direction); }
                finally { list.recycle(); }
                SystemClock.sleep(Math.min(100, timeLeft()));
                node = find(id); if (node != null) return node;
                if (!moved) break;
            }
        }
        throw new Refused(Reason.UI);
    }

    private boolean findAndRecycle(String id) throws Exception {
        AccessibilityNodeInfo node = find(id); if (node == null) return false; node.recycle(); return true;
    }

    private AccessibilityNodeInfo find(String id) throws Exception {
        List<AccessibilityNodeInfo> nodes = productNodes(); AccessibilityNodeInfo found = null;
        for (AccessibilityNodeInfo node : nodes) {
            if (id.equals(node.getViewIdResourceName()) && node.isVisibleToUser()) {
                if (found != null) { found.recycle(); recycle(nodes); throw new Refused(Reason.UI); }
                found = AccessibilityNodeInfo.obtain(node);
            }
        }
        recycle(nodes); return found;
    }

    private List<AccessibilityNodeInfo> productNodes() throws Exception {
        timeLeft(); List<AccessibilityNodeInfo> nodes = new ArrayList<>();
        // Fresh objects alone can still originate in UiAutomation's cached tree.
        // This clears this connection's cache, never app data or OS settings.
        if (Build.VERSION.SDK_INT >= 34) need(automation.clearCache(), Reason.UI);
        List<AccessibilityWindowInfo> windows = automation.getWindows();
        need(windows != null && windows.size() <= WINDOW_CAP, Reason.UI);
        ArrayDeque<AccessibilityNodeInfo> pending = new ArrayDeque<>();
        try {
            for (AccessibilityWindowInfo window : windows) {
                AccessibilityNodeInfo root = window.getRoot();
                if (root != null) {
                    if (productNode(root)) pending.add(root); else root.recycle();
                }
            }
            while (!pending.isEmpty()) {
                timeLeft(); need(nodes.size() + pending.size() <= NODE_CAP, Reason.UI);
                AccessibilityNodeInfo node = pending.removeFirst();
                if (!productNode(node)) { node.recycle(); continue; }
                nodes.add(node);
                need(node.getChildCount() <= NODE_CAP, Reason.UI);
                for (int i = 0; i < node.getChildCount(); i++) {
                    AccessibilityNodeInfo child = node.getChild(i); if (child != null) pending.add(child);
                }
            }
            return nodes;
        } catch (Throwable failure) {
            recycle(nodes); throw failure;
        } finally {
            while (!pending.isEmpty()) pending.removeFirst().recycle();
            for (AccessibilityWindowInfo window : windows) window.recycle();
        }
    }

    private static void recycle(List<AccessibilityNodeInfo> nodes) { for (AccessibilityNodeInfo node : nodes) node.recycle(); }

    private static boolean productNode(AccessibilityNodeInfo node) {
        CharSequence name = node.getPackageName(); return name != null && PRODUCT.contentEquals(name);
    }

    private String nodeText(AccessibilityNodeInfo node) {
        CharSequence value = node.getText();
        return value == null ? "" : value.toString();
    }

    private void waitUntil(Condition condition, long budget, Reason reason) throws Exception {
        long until = Math.min(deadline, SystemClock.uptimeMillis() + budget);
        do {
            timeLeft(); if (condition.ready()) return;
            SystemClock.sleep(Math.min(100, Math.max(1, until - SystemClock.uptimeMillis())));
        } while (SystemClock.uptimeMillis() < until);
        throw new Refused(reason);
    }

    private long timeLeft() {
        long left = deadline - SystemClock.uptimeMillis(); need(!finished.get() && left > 0, Reason.DEADLINE); return left;
    }

    private static void need(boolean value, Reason reason) { if (!value) throw new Refused(reason); }
    private void checked(boolean value, Reason reason) { need(value, reason); checks++; }

    private static void exact(JSONObject value, String... names) throws JSONException {
        Set<String> keys = new HashSet<>(); Iterator<String> iterator = value.keys();
        while (iterator.hasNext()) keys.add(iterator.next());
        need(keys.equals(new HashSet<>(Arrays.asList(names))) && value.length() == names.length, Reason.PROBE);
    }

    private static long number(JSONObject value, String name, long low, long high) throws JSONException {
        Object raw = value.get(name); need(raw instanceof Integer || raw instanceof Long, Reason.PROBE);
        long n = ((Number) raw).longValue(); need(n >= low && n <= high, Reason.PROBE); return n;
    }

    private static boolean bool(JSONObject value, String name) throws JSONException {
        Object raw = value.get(name); need(raw instanceof Boolean, Reason.PROBE); return (Boolean) raw;
    }

    private static String string(JSONObject value, String name) throws JSONException {
        Object raw = value.get(name); need(raw instanceof String, Reason.PROBE); return (String) raw;
    }

    private static JSONObject strictObject(byte[] bytes) throws Exception {
        need(bytes.length > 0 && bytes.length <= PROBE_CAP, Reason.PROBE);
        String text = utf8(bytes); JsonShape scanner = new JsonShape(text); scanner.value(0); scanner.space();
        need(scanner.pos == text.length(), Reason.PROBE);
        return new JSONObject(text);
    }

    /** Bounded strict syntax/decoded-key duplicate guard ahead of platform JSON. */
    private static final class JsonShape {
        final String text; int pos; int nodes;
        JsonShape(String text) { this.text = text; }
        void space() { while (pos < text.length() && " \t\r\n".indexOf(text.charAt(pos)) >= 0) pos++; }
        void value(int depth) throws Exception {
            need(depth <= 8 && ++nodes <= 256, Reason.PROBE); space(); need(pos < text.length(), Reason.PROBE);
            char c = text.charAt(pos);
            if (c == '{') {
                pos++; space(); Set<String> keys = new HashSet<>(); if (take('}')) return;
                do { space(); String key = literal(); need(keys.add(key), Reason.PROBE); space(); need(take(':'), Reason.PROBE); value(depth + 1); space(); if (take('}')) return; need(take(','), Reason.PROBE); } while (true);
            }
            if (c == '[') { pos++; space(); if (take(']')) return; do { value(depth + 1); space(); if (take(']')) return; need(take(','), Reason.PROBE); } while (true); }
            if (c == '"') { literal(); return; }
            for (String token : new String[]{"true", "false", "null"}) if (text.startsWith(token, pos)) { pos += token.length(); return; }
            int start = pos; if (take('-')) need(pos < text.length(), Reason.PROBE);
            if (take('0')) { need(pos == text.length() || !Character.isDigit(text.charAt(pos)), Reason.PROBE); }
            else { need(pos < text.length() && text.charAt(pos) >= '1' && text.charAt(pos) <= '9', Reason.PROBE); while (pos < text.length() && text.charAt(pos) >= '0' && text.charAt(pos) <= '9') pos++; }
            need(pos > start, Reason.PROBE); // This finite wire permits integral numbers only.
        }
        boolean take(char c) { if (pos < text.length() && text.charAt(pos) == c) { pos++; return true; } return false; }
        String literal() throws Exception {
            int start = pos; need(take('"'), Reason.PROBE);
            while (pos < text.length()) {
                char c = text.charAt(pos++); if (c == '"') return new org.json.JSONTokener(text.substring(start, pos)).nextValue().toString();
                need(c >= 32, Reason.PROBE);
                if (c == '\\') { need(pos < text.length(), Reason.PROBE); char escape = text.charAt(pos++); if (escape == 'u') { need(pos + 4 <= text.length(), Reason.PROBE); for (int i = 0; i < 4; i++) need("0123456789abcdefABCDEF".indexOf(text.charAt(pos++)) >= 0, Reason.PROBE); } else need("\"\\/bfnrt".indexOf(escape) >= 0, Reason.PROBE); }
            }
            throw new Refused(Reason.PROBE);
        }
    }

    private static byte[] readFile(File file, int cap) throws IOException {
        try (FileInputStream input = new FileInputStream(file)) {
            ByteArrayOutputStream output = new ByteArrayOutputStream(); byte[] block = new byte[1024]; int n;
            while ((n = input.read(block)) != -1) { need(output.size() + n <= cap, Reason.FIXTURE); output.write(block, 0, n); }
            return output.toByteArray();
        }
    }

    private static String utf8(byte[] value) throws CharacterCodingException {
        return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(value)).toString();
    }

    private static String digest(byte[] value) throws Exception { return hex(MessageDigest.getInstance("SHA-256").digest(value)); }
    private static String hex(byte[] value) { StringBuilder out = new StringBuilder(value.length * 2); for (byte b : value) out.append(String.format(java.util.Locale.ROOT, "%02x", b & 255)); return out.toString(); }
    private static String hint(Workspace w) throws Exception { return digest(("1\n" + w.story + "\n" + w.branch + "\n").getBytes(StandardCharsets.UTF_8)); }

    private void observe(Probe probe) throws JSONException {
        JSONObject value = new JSONObject().put("pid", probe.pid).put("uid", productUid).put("start", probe.start)
                .put("task", probe.task).put("restored", probe.restored).put("factory", probe.factory);
        observations.put(value);
    }

    private JSONObject proof(boolean passed, Reason reason) throws Exception {
        JSONObject result = new JSONObject().put("version", 1).put("scope", RESULT_SCOPE).put("case", caseName)
                .put("run_id", runId == null ? JSONObject.NULL : runId).put("status", passed ? "passed" : "failed")
                .put("stage", stage.name()).put("reason", reason.name()).put("checks", checks).put("process_deaths", deaths)
                .put("last_workspace_read", lastWorkspaceRead.name()).put("last_workspace_utf16_length", lastWorkspaceUtf16Length)
                .put("controller", new JSONObject().put("pid", Process.myPid()).put("uid", Process.myUid())
                        .put("start", Process.getStartUptimeMillis()))
                .put("observations", observations).put("terminal_observations", terminalObservations);
        result.put("fixture", childCase ? (childFixture == null ? JSONObject.NULL : childFixture)
                : (fixture == null ? JSONObject.NULL : fixture.json()));
        if (retiredCase) result.put("load_gate", loadGate == null ? JSONObject.NULL : loadGate)
                .put("retirement_helpers", retirementHelpers).put("last_helper_exit", lastHelperExit == null ? JSONObject.NULL : lastHelperExit);
        if (retainedCase) result.put("load_gate", loadGate == null ? JSONObject.NULL : loadGate)
                .put("retained_helpers", retainedHelpers).put("last_helper_exit", lastHelperExit == null ? JSONObject.NULL : lastHelperExit);
        return result;
    }

    private static final class Workspace {
        final String story, branch; final long head;
        Workspace(String story, String branch, long head) { this.story = story; this.branch = branch; this.head = head; }
        boolean same(Workspace other, long expected) { return story.equals(other.story) && branch.equals(other.branch) && head == expected; }
        JSONObject json() throws JSONException { return new JSONObject().put("story", story).put("branch", branch).put("head", head); }
    }

    /** Exact fixture keys are frozen here; no revision/text/request/turn is restorable authority. */
    private static final class Fixture {
        final Workspace a, b; final String originRun, originApk, signature; final int controllerUid, productUid;
        Fixture(Workspace a, Workspace b, String run, String apk, int controller, int product, String signature) {
            this.a = a; this.b = b; originRun = run; originApk = apk; controllerUid = controller; productUid = product; this.signature = signature;
        }
        List<String> ids() { return Arrays.asList(a.story, b.story); }
        JSONObject json() throws JSONException {
            return new JSONObject().put("version", 1).put("scope", FIXTURE_SCOPE).put("case", CASE)
                    .put("controller_uid", controllerUid).put("product_uid", productUid).put("signature_sha256", signature)
                    .put("origin_run_id", originRun).put("origin_product_sha256", originApk)
                    .put("stories", new JSONArray().put(a.json()).put(b.json()));
        }
    }

    private static final class Probe {
        final int pid, task, factory; final long start, sequence; final boolean restored, hintPresent;
        final String hint, event; final long[] operations;
        Probe(int pid, long start, int task, long seq, boolean restored, int factory, boolean hasHint, String hint, String event, long[] operations) {
            this.pid = pid; this.start = start; this.task = task; sequence = seq; this.restored = restored;
            this.factory = factory; hintPresent = hasHint; this.hint = hint; this.event = event; this.operations = operations.clone();
        }
        long op(String name) { for (int i = 0; i < OPS.length; i++) if (OPS[i].equals(name)) return operations[i]; throw new Refused(Reason.PROBE); }
        boolean sameProcess(Probe other) { return pid == other.pid && start == other.start; }
        boolean sameIdentity(Probe other) { return sameProcess(other) && task == other.task; }
    }
}
