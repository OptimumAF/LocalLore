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
val capacityProfile = Properties().apply {
    rootProject.file("capacity-profile.properties").inputStream().use { load(it) }
}
require(capacityProfile == Properties().apply {
    setProperty("sqlite.maxPageCount", "15")
    setProperty("fixture.prefixTurns", "0")
}) { "Capacity profile changed; recalibrate and review the fixed test binary before updating this guard" }
extra["localloreCapacityTest"] = capacityTest
extra["localloreCapacityPages"] = if (capacityTest) 15 else 0
if (capacityTest) layout.buildDirectory.set(layout.projectDirectory.dir("build-capacity"))

android {
    namespace = "org.locallore.app"
    compileSdk = 36
    buildToolsVersion = "35.0.0"
    ndkVersion = "29.0.14206865"
    sourceSets["main"].jniLibs.srcDir(layout.buildDirectory.dir("generated/rustJniLibs"))

    defaultConfig {
        applicationId = if (capacityTest) "org.locallore.app.capacity" else "org.locallore.app"
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
}

androidComponents {
    beforeVariants(selector().all()) { variant ->
        if (capacityTest && variant.buildType != "debug") variant.enable = false
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
