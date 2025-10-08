// scripts/patch-rn-gradle-plugin.js
const fs = require('fs');
const path = require('path');

const candidates = [
  'node_modules/react-native/node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
  'node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
];

let touched = 0;

for (const rel of candidates) {
  const file = path.join(process.cwd(), rel);
  if (!fs.existsSync(file)) continue;

  let src = fs.readFileSync(file, 'utf8');
  const before = src;

  // Remove wrong import if present
  src = src.replace(/\n\s*import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g, '\n');

  // Ensure correct import
  if (!/import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf/.test(src)) {
    src = src.replace(
      /(import[^\n]*\n)+(?!import)/m,
      (m) => m + 'import org.gradle.kotlin.dsl.support.serviceOf\n'
    );
  }

  // Normalize calls
  src = src.replace(/\bgradle\.serviceOf</g, 'serviceOf<');

  if (src !== before) {
    fs.writeFileSync(file, src, 'utf8');
    console.log('[patch] fixed serviceOf in:', rel);
    touched++;
  } else {
    console.log('[patch] no changes needed for:', rel);
  }
}

if (!touched) console.log('[patch] RN gradle plugin file not found; nothing to do.');
