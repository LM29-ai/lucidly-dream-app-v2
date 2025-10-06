// scripts/postinstall.js
const fs = require("fs");
const path = require("path");

function tryPatch(file) {
  if (!fs.existsSync(file)) return false;
  let src = fs.readFileSync(file, "utf8");

  // 1) Remove the brittle import (if present)
  src = src.replace(
    /import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g,
    ""
  );
  src = src.replace(
    /import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf\s*\r?\n/g,
    ""
  );

  // 2) Replace calls with the stable receiver form
  //    serviceOf<Foo>()  ->  gradle.serviceOf<Foo>()
  src = src.replace(/(^|\s)serviceOf</g, "$1gradle.serviceOf<");

  fs.writeFileSync(file, src, "utf8");
  console.log(`[postinstall] patched: ${file}`);
  return true;
}

function findCandidates() {
  const roots = [
    // react-native vendored plugin path variants
    path.join("node_modules", "react-native", "node_modules", "@react-native", "gradle-plugin", "react-native-gradle-plugin", "build.gradle.kts"),
    path.join("node_modules", "@react-native", "gradle-plugin", "react-native-gradle-plugin", "build.gradle.kts"),
  ];
  return roots.filter(fs.existsSync);
}

function main() {
  // Best-effort: allow CI to proceed even if patch-package not present
  try {
    require("child_process").spawnSync("npx", ["--yes", "patch-package"], {
      stdio: "inherit",
      shell: process.platform === "win32",
    });
  } catch {
    console.log("[postinstall] patch-package not available (ignored)");
  }

  const files = findCandidates();
  if (files.length === 0) {
    console.log("[postinstall] RN gradle-plugin file not found (ok if plugin layout differs).");
    return;
  }
  files.forEach(tryPatch);
  console.log("[postinstall] done");
}

main();
