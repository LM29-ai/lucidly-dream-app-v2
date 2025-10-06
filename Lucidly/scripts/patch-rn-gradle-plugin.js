// scripts/patch-rn-gradle-plugin.js
const fs = require('fs');
const path = require('path');

const candidates = [
  // RN vendored plugin under react-native/
  'node_modules/react-native/node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
  // Direct install of the plugin (some setups)
  'node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
  // Rare, but include just in case
  'node_modules/react-native-gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
];

function patchOne(fullPath) {
  if (!fs.existsSync(fullPath)) return false;

  let src = fs.readFileSync(fullPath, 'utf8');
  const original = src;

  // 1) Remove the WRONG import if present
  src = src.replace(/\r?\n\s*import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g, '\n');

  // 2) Ensure the RIGHT import exists
  if (!/import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf/.test(src)) {
    // insert after last import line
    src = src.replace(/(^|\n)(import\s+[^\n]+\n)+/m, (m) => m + 'import org.gradle.kotlin.dsl.support.serviceOf\n');
  }

  // 3) Normalize calls: gradle.serviceOf<T>() -> serviceOf<T>()
  src = src.replace(/\bgradle\.serviceOf</g, 'serviceOf<');

  if (src !== original) {
    fs.writeFileSync(fullPath, src, 'utf8');
    console.log(`[patch] Fixed serviceOf import/calls in: ${fullPath}`);
  } else {
    console.log(`[patch] No changes needed in: ${fullPath}`);
  }
  return true;
}

let touchedAny = false;
for (const rel of candidates) {
  const abs = path.join(process.cwd(), rel);
  if (patchOne(abs)) touchedAny = true;
}

if (!touchedAny) {
  console.log('[patch] Could not find RN gradle-plugin file in known locations; continuing anyway.');
}
