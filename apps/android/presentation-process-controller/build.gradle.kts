plugins { id("com.android.application") }

require(providers.gradleProperty("localLorePresentationProcessVerification").orNull == "true")
require(providers.gradleProperty("localLoreInputDraftVerification").orNull == "true")
require(providers.gradleProperty("localLoreInputProcessVerification").orNull == null)
require(gradle.startParameter.projectCacheDir?.canonicalFile == rootProject.file(".gradle-presentation-process").canonicalFile)
require(gradle.startParameter.taskNames.none { it.contains("release", ignoreCase = true) }) {
    "The presentation process controller is for isolated debug verification only."
}

android {
    namespace = "org.locallore.presentationprocessverify"
    compileSdk = 36
    defaultConfig {
        applicationId = "org.locallore.app.presentationprocesscontroller"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "3-presentation-process-verification"
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
