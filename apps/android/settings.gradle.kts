pluginManagement {
    val liteRt = providers.gradleProperty("localLoreLiteRtVerification").orNull
    require(liteRt == null || liteRt == "true") { "LiteRT verification must be explicitly true or absent" }
    plugins {
        id("com.android.application") version "8.10.1"
        id("org.jetbrains.kotlin.android") version (if (liteRt == "true") "2.4.0" else "2.2.21")
        id("org.jetbrains.kotlin.plugin.compose") version (if (liteRt == "true") "2.4.0" else "2.2.21")
    }
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "LocalLore"
include(":app")
