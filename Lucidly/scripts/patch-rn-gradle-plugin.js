// scripts/patch-rn-gradle-plugin.js
// Robustly locate and fix the RN Gradle plugin import/call for serviceOf

const fs = require('fs');
const path = require('path');

function uniq(arr){ return [...new Set(arr)]; }

function tryPushCandidate(list, p) {
  if (p && fs.existsSync(p)) list.push(p);
}

const candidates = [];

// A. Resolve the plugin directly if present at top-level node_modules
try {
  const pkg = require.resolve('@react-native/gradle-plugin/package.json', { paths: [process.cwd()] });
  const base = path.dirname(pkg);
  tryPushCandidate(candidates, path.join(base, 'react-native-gradle-plugin', 'build.gradle.kts'));
} catch (_) {}

// B. Resolve react-native, then check its nested node_modules for the plugin
try {
  const rnPkg = require.resolve('react-native/package.json', { paths: [process.cwd()] });
  const rnBase = path.dirname(rnPkg);
  tryPushCandidate(
    candidates,
    path.join(rnBase, 'node_modules', '@react-native', 'gradle-plugin', 'react-native-gradle-plugin', 'build.gradle.kts')
  );
} catch (_) {}

// C. Fallback hard-coded paths we’ve seen in CI images
tryPushCandidate(candidates, path.join(process.cwd(),
  'node_modules', 'react-native', 'node_modules', '@react-native', 'gradle-plugin', 'react-native-gradle-plugin', 'build.gradle.kts'));
tryPushCandidate(candidates, path.join(process.cwd(),
  'node_modules', '@react-native', 'gradle-plugin', 'react-native-gradle-plugin', 'build.gradle.kts'));

const files = uniq(candidates);
if (!files.length) {
  console.log('[patch] RN gradle plugin file not found in known locations; continuing');
  process.exit(0);
}

let touched = 0;
for (const file of files) {
  try {
    let src = fs.readFileSync(file, 'utf8');
    const before = src;

    // 1) Remove the wrong import
    src = src.replace(
      /\n\s*import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g,
      '\n'
    );

    // 2) Ensure the correct import exists
    if (!/import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf/.test(src)) {
      if (/import\s/.test(src)) {
        // append after the last import line
        src = src.replace(
          /(^|\n)(import[^\n]*\n)(?!.*\bimport\b)/s,
          (m) => m + 'import org.gradle.kotlin.dsl.support.serviceOf\n'
        );
        if (!/import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf/.test(src)) {
          // if the above pattern didn't match, prepend
          src = 'import org.gradle.kotlin.dsl.support.serviceOf\n' + src;
        }
      } else {
        src = 'import org.gradle.kotlin.dsl.support.serviceOf\n' + src;
      }
    }

    // 3) Normalize calls: gradle.serviceOf<...>() -> serviceOf<...>()
    src = src.replace(/\bgradle\.serviceOf</g, 'serviceOf<');

    if (src !== before) {
      fs.writeFileSync(file, src, 'utf8');
      console.log('[patch] fixed serviceOf imports/calls in', path.relative(process.cwd(), file));
      touched++;
    } else {
      console.log('[patch] no changes needed for', path.relative(process.cwd(), file));
    }
  } catch (e) {
    console.log('[patch] error processing', file, e?.message || e);
  }
}

if (!touched) console.log('[patch] nothing changed; proceeding');
process.exit(0);
