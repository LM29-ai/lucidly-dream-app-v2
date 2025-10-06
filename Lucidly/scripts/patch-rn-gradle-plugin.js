// scripts/patch-rn-gradle-plugin.js
// Fixes bad import in RN Gradle plugin that breaks with Gradle 8.x
// - Removes:   import org.gradle.configurationcache.extensions.serviceOf
// - Ensures:   import org.gradle.kotlin.dsl.support.serviceOf
// - Normalizes: gradle.serviceOf<...> -> serviceOf<...>

const fs = require('fs');
const path = require('path');

const CWD = process.cwd();
const candidates = [
  // React Native nested path (most common in Expo builds)
  'node_modules/react-native/node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
  // Direct path (some installs)
  'node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/build.gradle.kts',
];

let touched = 0;

for (const rel of candidates) {
  const file = path.join(CWD, rel);
  if (!fs.existsSync(file)) continue;

  let s = fs.readFileSync(file, 'utf8');
  const before = s;

  // 1) Drop the wrong import if present
  s = s.replace(
    /\n\s*import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g,
    '\n'
  );

  // 2) Ensure the correct import exists (keep imports block tidy)
  if (!/import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf/.test(s)) {
    s = s.replace(
      /((?:^|\n)import\s+[^\n]+\n)+/m,
      (m) => m + 'import org.gradle.kotlin.dsl.support.serviceOf\n'
    );
  }

  // 3) Normalize calls
  s = s.replace(/\bgradle\.serviceOf</g, 'serviceOf<');

  if (s !== before) {
    fs.writeFileSync(file, s, 'utf8');
    console.log('[patch] fixed:', rel);
    touched++;
  } else {
    console.log('[patch] no changes needed:', rel);
  }
}

if (!touched) {
  console.log('[patch] RN gradle-plugin file not found; continuing');
}
