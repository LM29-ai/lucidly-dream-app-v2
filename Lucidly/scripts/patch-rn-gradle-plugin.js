// scripts/patch-rn-gradle-plugin.js
// Fixes wrong serviceOf import/calls in RN gradle plugin for Gradle 8.x

const fs = require('fs');
const path = require('path');

function uniq(a){ return [...new Set(a)]; }
function pushIfExists(list, p){ if (p && fs.existsSync(p)) list.push(p); }

const candidates = [];

// A) resolve the plugin directly
try {
  const pkg = require.resolve('@react-native/gradle-plugin/package.json', { paths: [process.cwd()] });
  const base = path.dirname(pkg);
  pushIfExists(candidates, path.join(base, 'react-native-gradle-plugin', 'build.gradle.kts'));
} catch {}

// B) resolve via react-native’s nested node_modules
try {
  const rnPkg = require.resolve('react-native/package.json', { paths: [process.cwd()] });
  const rnBase = path.dirname(rnPkg);
  pushIfExists(candidates, path.join(
    rnBase, 'node_modules', '@react-native', 'gradle-plugin', 'react-native-gradle-plugin', 'build.gradle.kts'
  ));
} catch {}

pushIfExists(candidates, path.join(
  process.cwd(), 'node_modules', '@react-native', 'gradle-plugin', 'react-native-gradle-plugin', 'build.gradle.kts'
));
pushIfExists(candidates, path.join(
  process.cwd(), 'node_modules', 'react-native', 'node_modules', '@react-native', 'gradle-plugin', 'react-native-gradle-plugin', 'build.gradle.kts'
));

const files = uniq(candidates);
if (!files.length) {
  console.log('[patch] RN gradle plugin file not found; continuing');
  process.exit(0);
}

let changed = 0;
for (const file of files) {
  try {
    let s = fs.readFileSync(file, 'utf8');
    const before = s;

    // Drop the wrong import
    s = s.replace(/\n\s*import\s+org\.gradle\.configurationcache\.extensions\.serviceOf\s*\r?\n/g, '\n');

    // Ensure the correct import exists
    if (!/import\s+org\.gradle\.kotlin\.dsl\.support\.serviceOf/.test(s)) {
      // insert after last import if possible
      const m = s.match(/(^|\n)import[^\n]*\n/g);
      if (m) {
        const last = m[m.length - 1];
        const idx = s.lastIndexOf(last) + last.length;
        s = s.slice(0, idx) + 'import org.gradle.kotlin.dsl.support.serviceOf\n' + s.slice(idx);
      } else {
        s = 'import org.gradle.kotlin.dsl.support.serviceOf\n' + s;
      }
    }

    // Normalize calls
    s = s.replace(/\bgradle\.serviceOf</g, 'serviceOf<');

    if (s !== before) {
      fs.writeFileSync(file, s, 'utf8');
      console.log('[patch] fixed', path.relative(process.cwd(), file));
      changed++;
    } else {
      console.log('[patch] no changes needed for', path.relative(process.cwd(), file));
    }
  } catch (e) {
    console.log('[patch] error on', file, e?.message || e);
  }
}

if (!changed) console.log('[patch] nothing changed; proceeding');
