// scripts/patch-rn-gradle-plugin.js
const fs = require("fs");
const path = require("path");

const candidates = [
  // RN 0.73.x typical location
  path.join(__dirname, "..", "node_modules", "@react-native", "gradle-plugin", "build.gradle.kts"),
  // Some package layouts keep the plugin under a submodule folder:
  path.join(__dirname, "..", "node_modules", "@react-native", "gradle-plugin", "react-native-gradle-plugin", "build.gradle.kts"),
];

let patchedAny = false;

for (const file of candidates) {
  if (!fs.existsSync(file)) continue;
  let src = fs.readFileSync(file, "utf8");
  const before = src;

  // 1) Kotlin DSL new API: compilerOptions { allWarningsAsErrors.set(true) }
  src = src.replace(/allWarningsAsErrors\.set\(\s*true\s*\)/g, "allWarningsAsErrors.set(false)");

  // 2) Older style: kotlinOptions { allWarningsAsErrors = true }
  src = src.replace(/allWarningsAsErrors\s*=\s*true/g, "allWarningsAsErrors = false");

  // 3) Belt & suspenders in case they force Werror via freeCompilerArgs
  //    e.g. freeCompilerArgs.add("-Werror")
  src = src.replace(/freeCompilerArgs\.add\(\s*"-Werror"\s*\)/g, '// removed "-Werror" by postinstall patch');

  if (src !== before) {
    fs.writeFileSync(file, src, "utf8");
    console.log(`✔ Patched Kotlin Werror in ${file}`);
    patchedAny = true;
  } else {
    console.log(`ℹ No Werror tokens found in ${file} (already OK)`);
  }
}

if (!patchedAny) {
  console.log("ℹ React Native gradle-plugin build file not found or already patched. Nothing to do.");
}
