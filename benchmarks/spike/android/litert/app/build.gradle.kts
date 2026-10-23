plugins { id("com.android.application") }
// The publisher SDK has classfile major 65. Compile our Java 17 source with an
// already installed Java 21 compiler; never download a toolchain automatically.
java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }
android {
    namespace = "org.locallore.runtimebench.litert"
    compileSdk = 36
    buildToolsVersion = "35.0.0"
    defaultConfig {
        applicationId = "org.locallore.runtimebench.litert"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.18.1-spike"
        ndk { abiFilters += listOf("x86_64", "arm64-v8a") }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    lint { abortOnError = true }
}
dependencyLocking { lockAllConfigurations() }
dependencies {
    implementation("com.google.ai.edge.litertlm:litertlm-android:0.18.1")
    // Exact declared SDK dependencies; this experiment has no Kotlin compiler plugin.
    implementation("com.google.code.gson:gson:2.14.0")
    implementation("org.jetbrains.kotlin:kotlin-reflect:2.4.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.11.0")
    testImplementation("junit:junit:4.13.2")
}
