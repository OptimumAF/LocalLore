import java.util.Locale
import java.util.Properties

// Applied by :app after the Android application plugin. No downloaded build plugin.
val nativeNdkVersion = "29.0.14206865"
val nativeRustToolchain = "1.93.1"
val nativeMinSdk = 26
val nativeRepository = rootProject.projectDir.resolve("../..").canonicalFile
val nativeCargoOutput = layout.buildDirectory.dir("rust-target")
val nativeLibraries = layout.buildDirectory.dir("generated/rustJniLibs")
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
    inputs.property("ndkVersion", nativeNdkVersion)
    inputs.property("rustToolchain", nativeRustToolchain)
    inputs.property("minSdk", nativeMinSdk)
    inputs.property("targets", nativeTargets.keys.toList())
    outputs.files(nativeTargets.values.map { abi ->
        nativeLibraries.map { it.file("$abi/liblocallore_android.so") }
    })

    doLast {
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
        check(clang.isFile) {
            "Install NDK $nativeNdkVersion in the configured Android SDK before building Rust."
        }
        val cargo = if (windows) "cargo.exe" else "cargo"
        for ((target, abi) in nativeTargets) {
            val command = mutableListOf(cargo, "+$nativeRustToolchain", "build", "--locked",
                "--release", "--package", "locallore-android", "--lib", "--target", target,
                "--target-dir", nativeCargoOutput.get().asFile.absolutePath)
            if (gradle.startParameter.isOffline) command.add("--offline")
            // Each compiler argument remains one argument, including SDK paths with spaces.
            val rustFlags = listOf(
                "-C", "link-arg=--target=$target$nativeMinSdk",
                "-C", "link-arg=--sysroot=${llvm.resolve("sysroot").absolutePath}",
                "-C", "link-arg=-Wl,-z,max-page-size=16384",
            ).joinToString("\u001f")
            logger.lifecycle("Building LocalLore Rust JNI: $target -> $abi")
            val process = ProcessBuilder(command)
                .directory(nativeRepository)
                .redirectErrorStream(true)
            process.environment()["CARGO_TARGET_${target.uppercase(Locale.ROOT).replace('-', '_')}_LINKER"] =
                clang.absolutePath
            process.environment()["CARGO_ENCODED_RUSTFLAGS"] = rustFlags
            val child = process.start()
            val exitCode = try {
                // Gradle's daemon stdio is not a usable inherited console on all hosts.
                // Drain the merged pipe while Cargo runs so a full buffer cannot stall it.
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
                throw GradleException("Could not read Rust Android build output for $target", failure)
            } finally {
                if (child.isAlive) child.destroyForcibly()
                child.inputStream.close()
                child.errorStream.close()
                child.outputStream.close()
            }
            if (exitCode != 0) throw GradleException("Rust Android build failed for $target (exit $exitCode)")
            val library = nativeCargoOutput.get().file("$target/release/liblocallore_android.so").asFile
            check(library.isFile) { "Cargo did not produce ${library.name} for $target" }
            val destination = nativeLibraries.get().file("$abi/${library.name}").asFile
            destination.parentFile.mkdirs()
            library.copyTo(destination, overwrite = true)
        }
    }
}

tasks.named("preBuild").configure { dependsOn(buildRustAndroid) }
