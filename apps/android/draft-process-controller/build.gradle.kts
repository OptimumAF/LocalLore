plugins { id("com.android.application") }

require(providers.gradleProperty("localLoreInputProcessVerification").orNull == "true")
require(providers.gradleProperty("localLoreInputDraftVerification").orNull == "true")
require(gradle.startParameter.projectCacheDir?.canonicalFile == rootProject.file(".gradle-input-process").canonicalFile)
require(gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "The process controller is for isolated debug verification only."
}

android {
    namespace = "org.locallore.processverify"
    compileSdk = 36
    defaultConfig {
        applicationId = "org.locallore.app.draftprocesscontroller"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1-process-verification"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures { buildConfig = false }
    lint { abortOnError = true }
}
androidComponents {
    beforeVariants(selector().withBuildType("release")) { it.enable = false }
}
