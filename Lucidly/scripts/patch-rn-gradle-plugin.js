// scripts/patch-rn-gradle-plugin.js
const fs = require("fs");
const path = require("path");

const candidates = [
  path.join("node_modules","react-native","node_modules","@react-native","gradle-plugin","react-native-gradle-plugin","build.gradle.kts"),
  path.join("node_modules","@react-native","gradle-plugin","react-native-gradle-plugin","build.gradle.kts"),
];

function patchFile(file) {
  if (!fs.existsSync(file)) return false;
  let src = fs.readFileSync(file, "utf8");
  const before = src;

  // remove fragile imports
  src = src.replace(/import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g, "");
  src = src.replace(/import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf\s*\r?\n/g, "");

  // make calls explicit: gradle.serviceOf<...>()
  src = src.replace(/(^|[\s(=])serviceOf</g, "$1gradle.serviceOf<");

  if (src !== before) {
    fs.writeFileSync(file, src, "utf8");
    console.log(`[patch-rn-gradle-plugin] patched: ${file}`);
    return true;
  }
  console.log(`[patch-rn-gradle-plugin] no changes needed: ${file}`);
  return false;
}

(function main() {
  let touched = 0;
  for (const f of candidates) try { if (patchFile(f)) touched++; } catch (e) {
    console.warn(`[patch-rn-gradle-plugin] failed on ${f}:`, e.message);
  }
  if (!touched) console.log("[patch-rn-gradle-plugin] plugin file not found; continuing.");
})();
