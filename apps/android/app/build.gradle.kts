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
require(listOf(archiveVerification, archiveCapacity, storyDeletion, timelineVerification, parentRetention).count { it == "true" } <= 1) {
    "Verification installations must be selected individually."
}
require(archiveVerification != "true" || archiveCapacity != "true") {
    "Archive verification and capacity verification are separate installations."
}
val capacityProjectCache = rootProject.file(".gradle-archive-capacity").canonicalFile
val selectedProjectCache = (gradle.startParameter.projectCacheDir ?: rootProject.file(".gradle")).canonicalFile
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
if (archiveVerification == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-archive-verification"))
} else if (archiveCapacity == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-archive-capacity"))
} else if (storyDeletion == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-story-deletion"))
} else if (timelineVerification == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-timeline"))
} else if (parentRetention == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-parent-retention"))
}
val verificationSuffix = when {
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
require(listOf(archiveVerification, archiveCapacity, storyDeletion, timelineVerification, parentRetention).none { it == "true" } || !(capacityTest || reliefTest)) {
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
        if (verificationSuffix.isNotEmpty()) {
            applicationIdSuffix = verificationSuffix
            versionNameSuffix = when { parentRetention == "true" -> "-parent-retention"; timelineVerification == "true" -> "-timeline-verification"; storyDeletion == "true" -> "-story-deletion"; archiveCapacity == "true" -> "-archive-capacity"; else -> "-archive-verification" }
        }
        ndk { abiFilters += listOf("x86_64", "arm64-v8a") }
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures { compose = true }
    lint { abortOnError = true }
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
        if (archiveCapacity == "true" || storyDeletion == "true" || timelineVerification == "true" || parentRetention == "true") it.enable = false
    }
}

apply(from = rootProject.file("native-build.gradle.kts"))

kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }

dependencyLocking { lockAllConfigurations() }

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
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
    androidTestImplementation("androidx.test:runner:1.6.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
