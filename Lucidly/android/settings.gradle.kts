// android/settings.gradle.kts  (Kotlin DSL)

pluginManagement {
  repositories {
    gradlePluginPortal()
    google()
    mavenCentral()
  }
  // React Native & Expo settings plugins from node_modules
  includeBuild("../node_modules/@react-native/gradle-plugin")
  includeBuild("../node_modules/expo-modules-autolinking/android/expo-gradle-plugin")
}

plugins {
  id("com.facebook.react.settings")
  id("expo.settings")
}

rootProject.name = "Lucidly"

// App module
include(":app")
