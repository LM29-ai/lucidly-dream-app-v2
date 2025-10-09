// scripts/prepare-android-settings.js
const fs = require("fs");
const path = require("path");

const groovy = path.join("android", "settings.gradle");
const kts = path.join("android", "settings.gradle.kts");

try {
  if (fs.existsSync(groovy)) {
    fs.unlinkSync(groovy);
    console.log("[prepare-android-settings] removed android/settings.gradle");
  } else {
    console.log("[prepare-android-settings] no Groovy settings.gradle present");
  }
  if (fs.existsSync(kts)) {
    console.log("[prepare-android-settings] using android/settings.gradle.kts");
    // Optional: show the first 40 lines to the EAS log for sanity
    const lines = fs.readFileSync(kts, "utf8").split(/\r?\n/).slice(0, 40);
    console.log(lines.map((l, i) => String(i + 1).padStart(3) + "  " + l).join("\n"));
  } else {
    console.log("[prepare-android-settings] WARNING: android/settings.gradle.kts not found");
  }
} catch (e) {
  console.log("[prepare-android-settings] error:", e.message);
  // Don’t fail the build on logging issues
}
