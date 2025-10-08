// scripts/patch-rn-gradle-plugin.js
// Fix RN Gradle plugin import: use org.gradle.kotlin.dsl.support.serviceOf

const fs = require('fs');
const path = require('path');

const candidates = [
  // RN often nests the plugin under react-native/node_modules
  'node_modules/react-native/node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
  // sometimes it’s installed top-level
  'node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
];

let fixedAny = false;

for (const rel of candidates) {
  const file = path.join(process.cwd(), rel);
  if (!fs.existsSync(file)) continue;

  let src = fs.readFileSync(file, 'utf8');
  const before = src;

  // 1) Drop the wrong import if present
  src = src.replace(
    /\n\s*import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g,
    '\n'
  );

  // 2) Ensure the correct import exists after other imports
  if (!/import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf/.test(src)) {
    // insert after the last import line
    src = src.replace(
      /(import[^\n]*\n)(?!.*\bimport\b)/s, // after the last import
      (m) => m + 'import org.gradle.kotlin.dsl.support.serviceOf\n'
    );
    // If there were no imports, prepend
    if (!/import\s/.test(before)) {
      src = 'import org.gradle.kotlin.dsl.support.serviceOf\n' + src;
    }
  }

  // 3) Normalize calls like gradle.serviceOf<...>() -> serviceOf<...>()
  src = src.replace(/\bgradle\.serviceOf</g, 'serviceOf<');

  if (src !== before) {
    fs.writeFileSync(file, src, 'utf8');
    console.log('[patch] fixed serviceOf imports/calls in', rel);
    fixedAny = true;
  } else {
    console.log('[patch] no changes needed for', rel);
  }
}

if (!fixedAny) {
  console.log('[patch] RN Gradle plugin file not found in known locations; continuing');
}
