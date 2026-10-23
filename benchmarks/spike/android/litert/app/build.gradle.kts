import java.security.MessageDigest

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
    // Optional Rust pump is built/staged by the explicit play-probe helper only.
    if (providers.gradleProperty("localLorePlayProbe").orNull == "true") {
        sourceSets["main"].jniLibs.srcDir(rootProject.file("../../../../target/android-play-probe/jniLibs"))
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    lint { abortOnError = true; checkDependencies = true; xmlReport = true }
}
dependencyLocking { lockAllConfigurations() }

// AGP resolves its lint implementation through a detached configuration. Mirror
// that exact graph in a named, locked configuration and compare the actual AGP
// task classpath to it; this configuration never enters the application APK.
val analyzerAuditClasspath = configurations.create("analyzerAuditClasspath") {
    isCanBeConsumed = false
    isCanBeResolved = true
}
dependencies {
    implementation("com.google.ai.edge.litertlm:litertlm-android:0.18.1")
    // Exact declared SDK dependencies; this experiment has no Kotlin compiler plugin.
    implementation("com.google.code.gson:gson:2.14.0")
    implementation("org.jetbrains.kotlin:kotlin-reflect:2.4.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.11.0")
    testImplementation("junit:junit:4.13.2")
    add(analyzerAuditClasspath.name, "com.android.tools.lint:lint-gradle:32.4.1")
}

tasks.register("auditLintAnalyzer") {
    dependsOn("lintAnalyzeDebug")
    doLast {
        val analysis = tasks.getByName("lintAnalyzeDebug") as com.android.build.gradle.internal.lint.AndroidLintAnalysisTask
        val actual = analysis.lintTool.classpath.files.map { it.canonicalFile }.toSet()
        val locked = analyzerAuditClasspath.files.map { it.canonicalFile }.toSet()
        check(actual == locked) { "AGP analyzer classpath differs from the locked audit graph" }
        val artifacts = analyzerAuditClasspath.resolvedConfiguration.resolvedArtifacts.sortedBy { it.moduleVersion.id.toString() }.map {
            linkedMapOf("coordinate" to it.moduleVersion.id.toString(), "file" to it.file.name,
                "bytes" to it.file.length(), "sha256" to MessageDigest.getInstance("SHA-256")
                    .digest(it.file.readBytes()).joinToString("") { byte -> "%02x".format(byte.toInt() and 0xff) })
        }
        val report = linkedMapOf("version" to 1, "analyzer_version" to analysis.lintTool.versionKey.get(),
            "analysis_did_work" to analysis.state.didWork, "check_dependencies" to android.lint.checkDependencies,
            "artifacts" to artifacts,
            "model_directory" to analysis.lintModelDirectory.get().asFile.relativeTo(projectDir).invariantSeparatorsPath)
        val output = layout.buildDirectory.file("reports/analyzer-audit.json").get().asFile
        output.parentFile.mkdirs()
        output.writeText(groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(report)) + "\n")
    }
}
