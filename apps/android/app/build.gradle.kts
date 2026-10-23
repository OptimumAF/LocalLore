import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
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
val reliefTest = reliefOption == "true"
require(!(capacityTest && reliefTest)) { "Capacity and capacity-relief modes are mutually exclusive" }
val capacityCache = rootProject.file(".gradle-capacity").canonicalFile
val reliefCache = rootProject.file(".gradle-capacity-relief").canonicalFile
val selectedCache = gradle.startParameter.projectCacheDir?.canonicalFile
require(when {
    capacityTest -> selectedCache == capacityCache
    reliefTest -> selectedCache == reliefCache
    else -> selectedCache != capacityCache && selectedCache != reliefCache
}) {
    "Capacity modes require their separate project caches; use the corresponding scripts/android_capacity*_probe.py build"
}
val capacityProfile = Properties().apply {
    rootProject.file("capacity-profile.properties").inputStream().use { load(it) }
}
require(capacityProfile == Properties().apply {
    setProperty("sqlite.maxPageCount", "15")
    setProperty("fixture.prefixTurns", "0")
}) { "Capacity profile changed; recalibrate and review the fixed test binary before updating this guard" }
val reliefProfile = Properties().apply {
    rootProject.file("capacity-relief-profile.properties").inputStream().use { load(it) }
}
require(reliefProfile == Properties().apply {
    setProperty("sqlite.maxPageCount", "32")
    setProperty("fixture.format", "1")
}) { "Relief profile changed; recalibrate and review the fixed test binary before updating this guard" }
extra["localloreCapacityTest"] = capacityTest || reliefTest
extra["localloreCapacityMode"] = when { capacityTest -> "full"; reliefTest -> "relief"; else -> "ordinary" }
extra["localloreCapacityPages"] = when { capacityTest -> 15; reliefTest -> 32; else -> 0 }
if (capacityTest) layout.buildDirectory.set(layout.projectDirectory.dir("build-capacity"))
if (reliefTest) layout.buildDirectory.set(layout.projectDirectory.dir("build-capacity-relief"))

android {
    namespace = "org.locallore.app"
    compileSdk = 36
    buildToolsVersion = "35.0.0"
    ndkVersion = "29.0.14206865"
    sourceSets["main"].jniLibs.srcDir(layout.buildDirectory.dir("generated/rustJniLibs"))

    defaultConfig {
        applicationId = when {
            capacityTest -> "org.locallore.app.capacity"
            reliefTest -> "org.locallore.app.capacityrelief"
            else -> "org.locallore.app"
        }
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-shell"
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
        sourceSets["debug"].manifest.srcFile("src/capacityReliefTest/ReliefAppManifest.xml")
        sourceSets["androidTest"].setRoot("src/capacityReliefTest")
    }
}

androidComponents {
    beforeVariants(selector().all()) { variant ->
        if ((capacityTest || reliefTest) && variant.buildType != "debug") variant.enable = false
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
