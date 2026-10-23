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

android {
    namespace = "org.locallore.app"
    compileSdk = 36
    buildToolsVersion = "35.0.0"
    ndkVersion = "29.0.14206865"
    sourceSets["main"].jniLibs.srcDir(layout.buildDirectory.dir("generated/rustJniLibs"))

    defaultConfig {
        applicationId = "org.locallore.app"
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
