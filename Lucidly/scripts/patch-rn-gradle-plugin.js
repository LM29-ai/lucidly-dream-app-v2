// scripts/patch-rn-gradle-plugin.js
const fs = require('fs');
const path = require('path');

const targets = [
  // RN vendored plugin under react-native
  'node_modules/react-native/node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
  // direct install path
  'node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
];

function ensureImportBlock(src) {
  // If there are no imports at all, add one after the first line
  if (!/\nimport\s+/.test(src)) {
    const lines = src.split('\n');
    lines.splice(1, 0, 'import org.gradle.kotlin.dsl.support.serviceOf');
    return lines.join('\n');
  }
  // Otherwise, append the import after the last existing import
  return src.replace(
    /((?:^|\n)import\s+[^\n]+\n)+/m,
    (m) =>
      m.includes('org.gradle.kotlin.dsl.support.serviceOf')
        ? m
        : m + 'import org.gradle.kotlin.dsl.support.serviceOf\n'
  );
}

function patchOne(absPath) {
  if (!fs.existsSync(absPath)) return false;

  let src = fs.readFileSync(absPath, 'utf8');
  const before = src;

  // Drop the WRONG import if present
  src = src.replace(
    /\r?\n\s*import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g,
    '\n'
  );

  // Ensure the RIGHT import exists
  src = ensureImportBlock(src);

  // Normalize calls: gradle.serviceOf<T>() -> serviceOf<T>()
  src = src.replace(/\bgradle\.serviceOf</g, 'serviceOf<');

  if (src !== before) {
    fs.writeFileSync(absPath, src, 'utf8');
    console.log(`[patch] fixed serviceOf import/calls in: ${absPath}`);
  } else {
    console.log(`[patch] no changes needed: ${absPath}`);
  }
  return true;
}

let touched = false;
for (const rel of targets) {
  const abs = path.join(process.cwd(), rel);
  if (patchOne(abs)) touched = true;
}
if (!touched) {
  console.log('[patch] RN gradle-plugin file not found in known locations; continuing.');
}
