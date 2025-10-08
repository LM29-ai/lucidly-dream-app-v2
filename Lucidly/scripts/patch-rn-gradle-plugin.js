// scripts/patch-rn-gradle-plugin.js
// Robustly fix wrong 'serviceOf' import/usages inside RN's gradle plugin.
// Safe to run multiple times.

const fs = require('fs');
const path = require('path');

const root = process.cwd();
let fixed = 0;
let scanned = 0;

function fixFile(file) {
  let src = fs.readFileSync(file, 'utf8');
  const before = src;

  // Remove the WRONG import if present
  // import org.gradle.configurationcache.extensions.serviceOf
  src = src.replace(
    /\r?\n\s*import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g,
    '\n'
  );

  // Ensure the CORRECT import is present
  if (!/import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf/.test(src)) {
    // insert after the import block (after any consecutive import lines)
    src = src.replace(
      /((?:^|\n)\s*import[^\n]*\n)+/m,
      (m) => m + 'import org.gradle.kotlin.dsl.support.serviceOf\n'
    );
  }

  // Normalize calls: gradle.serviceOf<T>() -> serviceOf<T>()
  src = src.replace(/\bgradle\.serviceOf</g, 'serviceOf<');

  if (src !== before) {
    fs.writeFileSync(file, src, 'utf8');
    fixed++;
    console.log('[patch] repaired:', path.relative(root, file));
  } else {
    console.log('[patch] no changes needed:', path.relative(root, file));
  }
}

function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      walk(full);
    } else if (name === 'build.gradle.kts' && full.includes('@react-native/gradle-plugin')) {
      scanned++;
      fixFile(full);
    }
  }
}

// Search under node_modules only (fast & sufficient)
const nm = path.join(root, 'node_modules');
if (fs.existsSync(nm)) {
  walk(nm);
} else {
  console.log('[patch] node_modules not found, nothing to do (this is okay before install in some flows).');
}

if (scanned === 0) {
  console.log('[patch] did not find any RN gradle-plugin build.gradle.kts files.');
}

console.log(`[patch] scanned: ${scanned}, fixed: ${fixed}`);
