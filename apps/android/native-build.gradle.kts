import java.util.Locale
import java.util.Properties

// Applied by :app after the Android application plugin. No downloaded build plugin.
val nativeNdkVersion = "29.0.14206865"
val nativeRustToolchain = "1.93.1"
val nativeMinSdk = 26
val archiveCapacityFixture = providers.gradleProperty("localLoreArchiveCapacityVerification").orNull == "true"
val nativeRepository = rootProject.projectDir.resolve("../..").canonicalFile
val nativeCargoOutput = layout.buildDirectory.dir("rust-target")
val nativeLibraries = layout.buildDirectory.dir("generated/rustJniLibs")
val nativeTools = layout.buildDirectory.dir("native-tools")
val nativeTargets = linkedMapOf(
    "x86_64-linux-android" to "x86_64",
    "aarch64-linux-android" to "arm64-v8a",
)

val buildRustAndroid = tasks.register("buildRustAndroid") {
    group = "build"
    description = "Build the pinned Rust engine JNI library for both supported Android ABIs."
    inputs.files(nativeRepository.resolve("Cargo.toml"), nativeRepository.resolve("Cargo.lock"),
        nativeRepository.resolve("rust-toolchain.toml"))
    inputs.files(fileTree(nativeRepository.resolve("crates")) {
        exclude("**/target/**")
    })
    inputs.files(fileTree(nativeRepository.resolve("fixtures")))
    inputs.file(rootProject.file("native-build.gradle.kts"))
    inputs.file(rootProject.file("native-linker.rs"))
    inputs.property("ndkVersion", nativeNdkVersion)
    inputs.property("rustToolchain", nativeRustToolchain)
    inputs.property("minSdk", nativeMinSdk)
    inputs.property("archiveCapacityFixture", archiveCapacityFixture)
    inputs.property("targets", nativeTargets.keys.toList())
    outputs.files(nativeTargets.values.map { abi ->
        nativeLibraries.map { it.file("$abi/liblocallore_android.so") }
    })

    doLast {
        fun runNativeCommand(command: List<String>, additionalEnvironment: Map<String, String> = emptyMap()) {
            val process = ProcessBuilder(command)
                .directory(nativeRepository)
                .redirectErrorStream(true)
            process.environment().putAll(additionalEnvironment)
            val child = process.start()
            val exitCode = try {
                child.outputStream.close()
                child.inputStream.bufferedReader().useLines { lines ->
                    lines.forEach { logger.lifecycle(it) }
                }
                child.waitFor()
            } catch (interrupted: InterruptedException) {
                child.destroyForcibly()
                Thread.currentThread().interrupt()
                throw GradleException("Rust Android build interrupted", interrupted)
            } catch (failure: Exception) {
                child.destroyForcibly()
                throw GradleException("Could not read native build output", failure)
            } finally {
                if (child.isAlive) child.destroyForcibly()
                child.inputStream.close()
                child.errorStream.close()
                child.outputStream.close()
            }
            if (exitCode != 0) throw GradleException("Native command failed (exit $exitCode): ${command.first()}")
        }

        val operatingSystem = System.getProperty("os.name").lowercase(Locale.ROOT)
        val windows = operatingSystem.contains("windows")
        val hostTag = when {
            windows -> "windows-x86_64"
            operatingSystem.contains("mac") || operatingSystem.contains("darwin") -> "darwin-x86_64"
            operatingSystem.contains("linux") -> "linux-x86_64"
            else -> throw GradleException("Unsupported native build host: $operatingSystem")
        }
        val localProperties = Properties().apply {
            val source = rootProject.file("local.properties")
            if (source.isFile) source.inputStream().use { load(it) }
        }
        val sdkPath = localProperties.getProperty("sdk.dir")
            ?: providers.environmentVariable("ANDROID_HOME").orNull
            ?: providers.environmentVariable("ANDROID_SDK_ROOT").orNull
            ?: throw GradleException("Set sdk.dir in local.properties or ANDROID_HOME for the Android SDK.")
        val ndk = rootProject.file(sdkPath).resolve("ndk/$nativeNdkVersion")
        val llvm = ndk.resolve("toolchains/llvm/prebuilt/$hostTag")
        val clang = llvm.resolve("bin/clang${if (windows) ".exe" else ""}")
        val archiver = llvm.resolve("bin/llvm-ar${if (windows) ".exe" else ""}")
        check(clang.isFile) {
            "Install NDK $nativeNdkVersion in the configured Android SDK before building Rust."
        }
        check(archiver.isFile) { "The configured NDK must include llvm-ar for bundled SQLite." }
        val cargo = if (windows) "cargo.exe" else "cargo"
        val linker = nativeTools.get().file("native-linker${if (windows) ".exe" else ""}").asFile
        linker.parentFile.mkdirs()
        runNativeCommand(listOf(if (windows) "rustc.exe" else "rustc", "+$nativeRustToolchain",
            "--edition=2021", "-O", rootProject.file("native-linker.rs").absolutePath,
            "-o", linker.absolutePath))
        for ((target, abi) in nativeTargets) {
            val command = mutableListOf(cargo, "+$nativeRustToolchain", "build", "--locked",
                "--release", "--package", "locallore-android", "--lib", "--target", target,
                "--target-dir", nativeCargoOutput.get().asFile.absolutePath)
            if (archiveCapacityFixture) command.addAll(listOf("--features", "archive-capacity-fixture"))
            if (gradle.startParameter.isOffline) command.add("--offline")
            // Each compiler argument remains one argument, including SDK paths with spaces.
            val rustFlags = listOf(
                "-C", "link-arg=--target=$target$nativeMinSdk",
                "-C", "link-arg=--sysroot=${llvm.resolve("sysroot").absolutePath}",
                "-C", "link-arg=-Wl,-z,max-page-size=16384",
            ).joinToString("\u001f")
            // Bundled SQLite is compiled by cc-rs, separately from rustc's linker. Its pinned
            // version supports shell-escaped flags; quote each flag so SDK spaces/apostrophes
            // remain part of one sysroot argument. Compiler/archiver paths are exact files.
            fun quoteCFlag(value: String) = "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
            val cFlags = listOf("--target=$target$nativeMinSdk", "--sysroot=${llvm.resolve("sysroot").absolutePath}")
                .joinToString(" ") { quoteCFlag(it) }
            logger.lifecycle("Building LocalLore Rust JNI: $target -> $abi")
            runNativeCommand(command, mapOf(
                "CARGO_TARGET_${target.uppercase(Locale.ROOT).replace('-', '_')}_LINKER" to linker.absolutePath,
                "LOCALLORE_ANDROID_CLANG" to clang.absolutePath,
                "CARGO_ENCODED_RUSTFLAGS" to rustFlags,
                "CC_$target" to clang.absolutePath,
                "AR_$target" to archiver.absolutePath,
                "CFLAGS_$target" to cFlags,
                "CC_SHELL_ESCAPED_FLAGS" to "1",
                // Explicit empty ordinary value prevents inherited test caps leaking into normal builds.
                "LIBSQLITE3_FLAGS" to if (archiveCapacityFixture) "SQLITE_MAX_PAGE_COUNT=96" else "",
            ))
            val library = nativeCargoOutput.get().file("$target/release/liblocallore_android.so").asFile
            check(library.isFile) { "Cargo did not produce ${library.name} for $target" }
            val destination = nativeLibraries.get().file("$abi/${library.name}").asFile
            destination.parentFile.mkdirs()
            library.copyTo(destination, overwrite = true)
        }
    }
}

tasks.named("preBuild").configure { dependsOn(buildRustAndroid) }
