import java.security.MessageDigest
import java.util.zip.ZipFile
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

// Explicit local instrumentation variant; leave the user's installed demo/data intact.
val archiveVerification = providers.gradleProperty("localLoreArchiveVerification").orNull
require(archiveVerification == null || archiveVerification == "true")
val archiveCapacity = providers.gradleProperty("localLoreArchiveCapacityVerification").orNull
require(archiveCapacity == null || archiveCapacity == "true")
val storyDeletion = providers.gradleProperty("localLoreStoryDeletionVerification").orNull
require(storyDeletion == null || storyDeletion == "true")
val timelineVerification = providers.gradleProperty("localLoreTimelineVerification").orNull
require(timelineVerification == null || timelineVerification == "true")
val parentRetention = providers.gradleProperty("localLoreParentRetentionVerification").orNull
require(parentRetention == null || parentRetention == "true")
val liteRt = providers.gradleProperty("localLoreLiteRtVerification").orNull
require(liteRt == null || liteRt == "true")
val modelSetup = providers.gradleProperty("localLoreModelSetupVerification").orNull
require(modelSetup == null || modelSetup == "true")
require(modelSetup != "true" || liteRt == "true") { "Model setup verification requires the LiteRT candidate profile." }
val modelPicker = providers.gradleProperty("localLoreModelPickerVerification").orNull
require(modelPicker == null || modelPicker == "true") { "Model picker verification must be explicitly true or absent." }
require(modelPicker != "true" || modelSetup == "true") { "Model picker fixtures require the explicit model setup candidate profile." }
val modelVolume = providers.gradleProperty("localLoreModelVolumeVerification").orNull
require(modelVolume == null || modelVolume == "true") { "Model volume verification must be explicitly true or absent." }
require(modelVolume != "true" || modelSetup == "true") { "Model volume verification requires model setup and LiteRT candidate profiles." }
require(modelVolume != "true" || modelPicker != "true") { "Model volume and picker fixtures are separate installations." }
val modelReceipt = providers.gradleProperty("localLoreModelReceiptVerification").orNull
require(modelReceipt == null || modelReceipt == "true") { "Model receipt verification must be explicitly true or absent." }
require(modelReceipt != "true" || modelVolume == "true") { "Model receipt verification requires the explicit model volume, setup and LiteRT profiles." }
if (liteRt == "true") {
    val finiteCodecBytes = file("src/litert/java/org/locallore/app/FiniteSchemaRegex.kt").readText()
        .replace("\r\n", "\n").toByteArray(Charsets.UTF_8)
    val finiteCodecHash = MessageDigest.getInstance("SHA-256").digest(finiteCodecBytes)
        .joinToString("") { "%02x".format(it) }
    require(finiteCodecHash == "b89ba9aa332529a629e0f532f5d8e55997eef8f68229665f898eae53010af96f") {
        "Review the finite-schema codec and its worker provenance before building changed source."
    }
    require(file("src/litert/java/org/locallore/app/LiteRtRoleWorker.kt").readText()
        .contains("// Finite-schema codec source SHA-256: $finiteCodecHash")) {
        "The worker source identity must bind the reviewed finite-schema codec."
    }
    val workerBytes = file("src/litert/java/org/locallore/app/LiteRtRoleWorker.kt").readText()
        .replace("\r\n", "\n").toByteArray(Charsets.UTF_8)
    val workerHash = MessageDigest.getInstance("SHA-256").digest(workerBytes)
        .joinToString("") { "%02x".format(it) }
    require(workerHash == "db4d5f18318b7b5d67fbeb33bddee7781ddce7adc41477d9c17808e92c23df27") {
        "Update and review the trusted candidate worker provenance before building changed worker source."
    }
}
val externalInference = providers.gradleProperty("localLoreExternalInferenceVerification").orNull
require(externalInference == null || externalInference == "true")
val cancelAckVerification = providers.gradleProperty("localLoreCancelAckVerification").orNull
require(cancelAckVerification == null || cancelAckVerification == "true")
require(listOf(archiveVerification, archiveCapacity, storyDeletion, timelineVerification, parentRetention, cancelAckVerification, externalInference, liteRt).count { it == "true" } <= 1) {
    "Verification installations must be selected individually."
}
require(archiveVerification != "true" || archiveCapacity != "true") {
    "Archive verification and capacity verification are separate installations."
}
val capacityProjectCache = rootProject.file(".gradle-archive-capacity").canonicalFile
val selectedProjectCache = (gradle.startParameter.projectCacheDir ?: rootProject.file(".gradle")).canonicalFile
require((liteRt == "true") == (selectedProjectCache == rootProject.file(".gradle-litert-worker").canonicalFile)) {
    "LiteRT worker verification requires its exclusive .gradle-litert-worker project cache."
}
require(liteRt != "true" || gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "LiteRT worker verification is for local debug verification only."
}
require(liteRt != "true" || providers.gradleProperty("android.experimental.lint.version").orNull == "9.4.1") {
    "LiteRT worker verification requires the independently audited 32.4.1 analyzer via android.experimental.lint.version=9.4.1."
}
require(liteRt != "true" || providers.gradleProperty("org.gradle.java.installations.auto-download").orNull == "false") {
    "LiteRT worker verification must not download Java toolchains."
}
require((externalInference == "true") == (selectedProjectCache == rootProject.file(".gradle-external-inference").canonicalFile)) {
    "External inference verification requires its exclusive .gradle-external-inference project cache."
}
require(externalInference != "true" || gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "External inference verification is for local debug verification only."
}
require((cancelAckVerification == "true") == (selectedProjectCache == rootProject.file(".gradle-cancel-ack").canonicalFile)) {
    "Cancellation acknowledgement verification requires its exclusive .gradle-cancel-ack project cache."
}
require(cancelAckVerification != "true" || gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "Cancellation acknowledgement verification is for local debug verification only."
}
require((parentRetention == "true") == (selectedProjectCache == rootProject.file(".gradle-parent-retention").canonicalFile)) {
    "Parent retention verification requires its exclusive .gradle-parent-retention project cache."
}
require(parentRetention != "true" || gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "Parent retention verification is for local debug verification only."
}
require((timelineVerification == "true") == (selectedProjectCache == rootProject.file(".gradle-timeline").canonicalFile)) {
    "Timeline verification requires its exclusive .gradle-timeline project cache."
}
require(timelineVerification != "true" || gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "Timeline verification is for local debug verification only."
}
require((storyDeletion == "true") == (selectedProjectCache == rootProject.file(".gradle-story-deletion").canonicalFile)) {
    "Story deletion verification requires its exclusive .gradle-story-deletion project cache."
}
require(storyDeletion != "true" || gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "Story deletion verification is for local debug verification only."
}
require((archiveCapacity == "true") == (selectedProjectCache == capacityProjectCache)) {
    "Capacity verification requires its exclusive .gradle-archive-capacity project cache."
}
require(archiveCapacity != "true" || gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "The synthetic capacity fixture is for local debug verification only."
}
if (liteRt == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir(when {
        modelReceipt == "true" -> "build-model-receipt"
        modelVolume == "true" -> "build-model-volume"
        modelPicker == "true" -> "build-model-picker"
        else -> "build-litert-worker"
    }))
} else if (externalInference == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-external-inference"))
} else if (archiveVerification == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-archive-verification"))
} else if (archiveCapacity == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-archive-capacity"))
} else if (storyDeletion == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-story-deletion"))
} else if (timelineVerification == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-timeline"))
} else if (parentRetention == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-parent-retention"))
} else if (cancelAckVerification == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-cancel-ack"))
}
val verificationSuffix = when {
    modelVolume == "true" -> ".modelvolumeverify"
    modelPicker == "true" -> ".modelpickerverify"
    modelSetup == "true" -> ".modelverify"
    liteRt == "true" -> ".litertverify"
    externalInference == "true" -> ".externalverify"
    cancelAckVerification == "true" -> ".cancelack"
    parentRetention == "true" -> ".parentverify"
    timelineVerification == "true" -> ".timelineverify"
    storyDeletion == "true" -> ".storydelete"
    archiveCapacity == "true" -> ".archivecapacity"
    archiveVerification == "true" -> ".archiveverify"
    else -> ""
}
// Explicit test binary; never change the ordinary application's SQLite limit.
val capacityOption = providers.gradleProperty("locallore.capacityTest").orNull
require(capacityOption == null || capacityOption == "false" || capacityOption == "true") {
    "locallore.capacityTest must be absent, false or true"
}
require(providers.environmentVariable("LIBSQLITE3_FLAGS").orNull.isNullOrEmpty()) {
    "Unset LIBSQLITE3_FLAGS: Android SQLite compiler options are owned by the reviewed build profile"
}
val capacityTest = capacityOption == "true"
val reliefOption = providers.gradleProperty("locallore.capacityReliefTest").orNull
require(reliefOption == null || reliefOption == "false" || reliefOption == "true") {
    "locallore.capacityReliefTest must be absent, false or true"
}
val reliefFaultOption = providers.gradleProperty("locallore.capacityReliefFaultTest").orNull
require(reliefFaultOption == null || reliefFaultOption == "false" || reliefFaultOption == "true") {
    "locallore.capacityReliefFaultTest must be absent, false or true"
}
val reliefFaultTest = reliefFaultOption == "true"
require(!(reliefFaultTest && reliefOption == "true")) { "Relief and helper-fault modes are mutually exclusive" }
val reliefTest = reliefOption == "true" || reliefFaultTest
require(!(capacityTest && reliefTest)) { "Capacity and capacity-relief modes are mutually exclusive" }
require(listOf(archiveVerification, archiveCapacity, storyDeletion, timelineVerification, parentRetention, cancelAckVerification, externalInference, liteRt).none { it == "true" } || !(capacityTest || reliefTest)) {
    "Archive verification and capacity modes are mutually exclusive"
}
val capacityCache = rootProject.file(".gradle-capacity-v4").canonicalFile
val reliefCache = rootProject.file(".gradle-capacity-relief-v4").canonicalFile
val reliefFaultCache = rootProject.file(".gradle-capacity-faults-v4").canonicalFile
val selectedCache = gradle.startParameter.projectCacheDir?.canonicalFile
val historicalCapacityCaches = setOf(rootProject.file(".gradle-capacity").canonicalFile,
    rootProject.file(".gradle-capacity-relief").canonicalFile,
    rootProject.file(".gradle-capacity-v3").canonicalFile,
    rootProject.file(".gradle-capacity-relief-v3").canonicalFile,
    rootProject.file(".gradle-capacity-faults-v3").canonicalFile)
require(selectedCache !in historicalCapacityCaches) {
    "Historical capacity caches must remain untouched; use the exclusive schema4 v4 cache."
}
require(when {
    capacityTest -> selectedCache == capacityCache
    reliefFaultTest -> selectedCache == reliefFaultCache
    reliefTest -> selectedCache == reliefCache
    else -> selectedCache !in setOf(capacityCache, reliefCache, reliefFaultCache)
}) {
    "Capacity modes require their separate project caches; use the corresponding scripts/android_capacity*_probe.py build"
}
val capacityProfile = Properties().apply {
    rootProject.file("capacity-profile.properties").inputStream().use { load(it) }
}
require(capacityProfile == Properties().apply {
    setProperty("sqlite.maxPageCount", "23")
    setProperty("fixture.prefixTurns", "0")
    setProperty("fixture.format", "3")
    setProperty("database.schemaVersion", "4")
}) { "Capacity profile changed; recalibrate and review the fixed test binary before updating this guard" }
val reliefProfile = Properties().apply {
    rootProject.file("capacity-relief-profile.properties").inputStream().use { load(it) }
}
require(reliefProfile == Properties().apply {
    setProperty("sqlite.maxPageCount", "32")
    setProperty("fixture.format", "3")
    setProperty("database.schemaVersion", "4")
    setProperty("fixture.initialPages", "23")
    setProperty("fixture.paddingRows", "8")
}) { "Relief profile changed; recalibrate and review the fixed test binary before updating this guard" }
extra["localloreCapacityTest"] = capacityTest || reliefTest
extra["localloreCapacityMode"] = when { capacityTest -> "full"; reliefFaultTest -> "faults"; reliefTest -> "relief"; else -> "ordinary" }
extra["localloreCapacityPages"] = when { capacityTest -> 23; reliefTest -> 32; else -> 0 }
if (capacityTest) layout.buildDirectory.set(layout.projectDirectory.dir("build-capacity-v4"))
if (reliefTest) layout.buildDirectory.set(layout.projectDirectory.dir(
    if (reliefFaultTest) "build-capacity-faults-v4" else "build-capacity-relief-v4"))

android {
    namespace = "org.locallore.app"
    compileSdk = 36
    buildToolsVersion = "35.0.0"
    ndkVersion = "29.0.14206865"
    sourceSets["main"].jniLibs.srcDir(layout.buildDirectory.dir("generated/rustJniLibs"))

    defaultConfig {
        buildConfigField("boolean", "MODEL_VOLUME_VERIFICATION", (modelVolume == "true").toString())
        buildConfigField("boolean", "MODEL_RECEIPT_VERIFICATION", (modelReceipt == "true").toString())
        applicationId = when {
            capacityTest -> "org.locallore.app.capacityv4"
            reliefFaultTest -> "org.locallore.app.capacityfaultsv4"
            reliefTest -> "org.locallore.app.capacityreliefv4"
            else -> "org.locallore.app"
        }
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-shell"
        manifestPlaceholders["diagnosticTestAuthority"] = "org.locallore.app$verificationSuffix.test.diagnostics"
        manifestPlaceholders["archiveTestAuthority"] = "org.locallore.app$verificationSuffix.test.archives"
        manifestPlaceholders["chooserTestAuthority"] = "org.locallore.app$verificationSuffix.test.chooser"
        manifestPlaceholders["modelPickerTestAuthority"] = "org.locallore.app$verificationSuffix.test.modelpicker"
        if (verificationSuffix.isNotEmpty()) {
            applicationIdSuffix = verificationSuffix
            versionNameSuffix = when { liteRt == "true" -> "-litert-worker"; externalInference == "true" -> "-external-inference"; cancelAckVerification == "true" -> "-cancel-ack-verification"; parentRetention == "true" -> "-parent-retention"; timelineVerification == "true" -> "-timeline-verification"; storyDeletion == "true" -> "-story-deletion"; archiveCapacity == "true" -> "-archive-capacity"; else -> "-archive-verification" }
        }
        ndk { abiFilters += listOf("x86_64", "arm64-v8a") }
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    if (liteRt == "true") {
        packaging { jniLibs.keepDebugSymbols += "**/liblitertlm_jni.so" }
        sourceSets["main"].java.srcDir("src/litert/java")
        if (modelSetup == "true") sourceSets["debug"].manifest.srcFile("src/litert/AndroidManifest.xml")
        sourceSets["test"].java.srcDir("src/litertTest/java")
        sourceSets["androidTest"].java.srcDir("src/litertAndroidTest/java")
        if (modelVolume == "true") {
            sourceSets["debug"].java.srcDir("src/modelVolume/java")
            sourceSets["debug"].manifest.srcFile("src/modelVolume/AndroidManifest.xml")
            sourceSets["androidTest"].java.srcDir("src/modelVolumeAndroidTest/java")
            if (modelReceipt == "true") {
                sourceSets["debug"].java.srcDir("src/modelReceipt/java")
                sourceSets["debug"].manifest.srcFile("src/modelReceipt/AndroidManifest.xml")
                sourceSets["androidTest"].java.srcDir("src/modelReceiptAndroidTest/java")
                sourceSets["test"].java.srcDir("src/modelReceiptTest/java")
            }
        }
        if (modelPicker == "true") {
            sourceSets["debug"].java.srcDir("src/modelPicker/java")
            sourceSets["debug"].manifest.srcFile("src/modelPicker/AndroidManifest.xml")
            sourceSets["androidTest"].java.srcDir("src/modelPickerAndroidTest/java")
            sourceSets["androidTest"].manifest.srcFile("src/modelPickerAndroidTest/AndroidManifest.xml")
        }
    }
    buildFeatures { compose = true; buildConfig = true }
    lint { abortOnError = true; if (liteRt == "true") checkDependencies = true }
    if (capacityTest) {
        sourceSets["debug"].manifest.srcFile("src/capacityTest/CapacityAppManifest.xml")
        sourceSets["androidTest"].apply {
            setRoot("src/capacityTest")
        }
    }
    if (reliefTest) {
        sourceSets["debug"].manifest.srcFile(if (reliefFaultTest)
            "src/capacityReliefTest/FaultsAppManifest.xml" else "src/capacityReliefTest/ReliefAppManifest.xml")
        sourceSets["androidTest"].setRoot("src/capacityReliefTest")
    }
}

androidComponents {
    beforeVariants(selector().all()) { variant ->
        if ((capacityTest || reliefTest) && variant.buildType != "debug") variant.enable = false
    }
}

androidComponents {
    beforeVariants(selector().withBuildType("release")) {
        if (archiveCapacity == "true" || storyDeletion == "true" || timelineVerification == "true" || parentRetention == "true" || externalInference == "true" || liteRt == "true" || cancelAckVerification == "true") it.enable = false
    }
}

apply(from = rootProject.file("native-build.gradle.kts"))

kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }

dependencyLocking {
    lockAllConfigurations()
    if (liteRt == "true") lockFile.set(file("gradle-litert.lockfile"))
}

if (liteRt == "true") {
    kotlin { jvmToolchain(21) }
    tasks.withType<Test>().configureEach {
        javaLauncher.set(javaToolchains.launcherFor { languageVersion = JavaLanguageVersion.of(21) })
    }
}
val inferenceCoroutines = if (liteRt == "true") "1.11.0" else "1.10.2"
val analyzerAuditClasspath = if (liteRt == "true") configurations.create("analyzerAuditClasspath") {
    isCanBeConsumed = false
    isCanBeResolved = true
} else null

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2025.05.01")
    implementation(composeBom)
    androidTestImplementation(composeBom)
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:$inferenceCoroutines")
    if (liteRt == "true") {
        implementation("com.google.ai.edge.litertlm:litertlm-android:0.18.1")
        implementation("com.google.code.gson:gson:2.14.0")
        implementation("org.jetbrains.kotlin:kotlin-reflect:2.4.0")
        add(checkNotNull(analyzerAuditClasspath).name, "com.android.tools.lint:lint-gradle:32.4.1")
    }

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:$inferenceCoroutines")
    androidTestImplementation("androidx.test:runner:1.6.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}

// Candidate-only notices and audit graphs never enter the ordinary app.
if (liteRt == "true") {
    fun digest(bytes: ByteArray) = MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it.toInt() and 0xff) }
    val sdkAar = providers.provider {
        configurations.getByName("debugRuntimeClasspath").resolvedConfiguration.resolvedArtifacts.single {
            it.moduleVersion.id.toString() == "com.google.ai.edge.litertlm:litertlm-android:0.18.1"
        }.file
    }
    val noticeDirectory = layout.buildDirectory.dir("generated/litert-notices")
    val prepareNotices = tasks.register("prepareLiteRtNotices") {
        inputs.file(sdkAar)
        outputs.dir(noticeDirectory)
        doLast {
            check(digest(sdkAar.get().readBytes()) == "05c6bdc8acda834efcca12c0ad5d06d2cd8c83e60770f056d8d222f699f3012b")
            ZipFile(sdkAar.get()).use { archive ->
                mapOf("LICENSE" to "ec40a2da15ab0e8b44a9f787ab210203d3cad32572f5f99744a88eb90ff9ba4e",
                    "THIRD_PARTY_NOTICE.txt" to "52a70c82685debf85d4ea9d677615b8636ffd3b75435ce71f247bf5982fb2ba2").forEach { (name, hash) ->
                    val bytes = archive.getInputStream(checkNotNull(archive.getEntry(name))).use { it.readBytes() }
                    check(digest(bytes) == hash) { "SDK notice changed" }
                    val destination = noticeDirectory.get().file("notices/litertlm-0.18.1/$name").asFile
                    destination.parentFile.mkdirs()
                    destination.writeBytes(bytes)
                }
            }
        }
    }
    android.sourceSets["main"].assets.srcDir(noticeDirectory)
    tasks.named("preBuild").configure { dependsOn(prepareNotices) }
    tasks.register("auditLiteRtDependencies") {
        doLast {
            val artifacts = configurations.getByName("debugRuntimeClasspath").resolvedConfiguration.resolvedArtifacts
                .sortedBy { it.moduleVersion.id.toString() }.map {
                    mapOf("coordinate" to it.moduleVersion.id.toString(), "file" to it.file.name,
                        "bytes" to it.file.length(), "sha256" to digest(it.file.readBytes()))
                }
            val output = layout.buildDirectory.file("reports/litert-dependency-audit.json").get().asFile
            output.parentFile.mkdirs()
            output.writeText(groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(artifacts)) + "\n")
        }
    }
    tasks.register("auditLintAnalyzer") {
        dependsOn("lintAnalyzeDebug")
        doLast {
            val analysis = tasks.getByName("lintAnalyzeDebug") as com.android.build.gradle.internal.lint.AndroidLintAnalysisTask
            val actual = analysis.lintTool.classpath.files.map { it.canonicalFile }.toSet()
            val locked = checkNotNull(analyzerAuditClasspath).files.map { it.canonicalFile }.toSet()
            check(actual == locked) { "AGP analyzer classpath differs from locked candidate graph" }
            val artifacts = checkNotNull(analyzerAuditClasspath).resolvedConfiguration.resolvedArtifacts
                .sortedBy { it.moduleVersion.id.toString() }.map {
                    mapOf("coordinate" to it.moduleVersion.id.toString(), "file" to it.file.name,
                        "bytes" to it.file.length(), "sha256" to digest(it.file.readBytes()))
                }
            check(android.lint.checkDependencies) { "Candidate analyzer must check dependencies" }
            val modelRoot = analysis.lintModelDirectory.get().asFile
            val models = modelRoot.walkTopDown().filter { it.isFile && it.extension == "xml" }.toList()
            val modelText = models.joinToString("\n") { it.readText() }
            listOf("com.google.ai.edge.litertlm:litertlm-android:0.18.1", "org.jetbrains.kotlin:kotlin-reflect:2.4.0",
                "org.jetbrains.kotlin:kotlin-stdlib:2.4.0").forEach {
                check(modelText.contains(it)) { "Candidate lint model is missing a required SDK dependency" }
            }
            val modelHashes = models.sortedBy { it.path }.map {
                mapOf("file" to it.relativeTo(modelRoot).invariantSeparatorsPath,
                    "bytes" to it.length(), "sha256" to digest(it.readBytes()))
            }
            val report = mapOf("version" to 1, "check_dependencies" to android.lint.checkDependencies, "analyzer_version" to analysis.lintTool.versionKey.get(),
                "analysis_did_work" to analysis.state.didWork, "artifacts" to artifacts, "model_files" to modelHashes)
            val output = layout.buildDirectory.file("reports/litert-analyzer-audit.json").get().asFile
            output.parentFile.mkdirs()
            output.writeText(groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(report)) + "\n")
        }
    }
}
