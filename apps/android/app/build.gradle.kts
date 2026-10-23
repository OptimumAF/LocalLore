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
require(archiveVerification != "true" || archiveCapacity != "true") {
    "Archive verification and capacity verification are separate installations."
}
require(archiveCapacity != "true" || gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "The synthetic capacity fixture is for local debug verification only."
}
if (archiveVerification == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-archive-verification"))
} else if (archiveCapacity == "true") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build-archive-capacity"))
}
val verificationSuffix = when {
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
            versionNameSuffix = if (archiveCapacity == "true") "-archive-capacity" else "-archive-verification"
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
        if (archiveCapacity == "true") it.enable = false
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
