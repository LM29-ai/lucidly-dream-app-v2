// android/settings.gradle.kts

pluginManagement {
  repositories {
    gradlePluginPortal()
    google()
    mavenCentral()
  }
  // Settings plugins from node_modules
  includeBuild("../node_modules/@react-native/gradle-plugin")
  includeBuild("../node_modules/expo-modules-autolinking/android/expo-gradle-plugin")
}

plugins {
  id("com.facebook.react.settings")
  id("expo.settings")
}

rootProject.name = "Lucidly"
include(":app")
