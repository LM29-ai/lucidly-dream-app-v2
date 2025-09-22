const fs = require('fs');
const path = require('path');

const p = path.join(__dirname, '..', 'node_modules', '@react-native', 'gradle-plugin');
if (!fs.existsSync(p)) {
  console.error(
    [
      '❌ @react-native/gradle-plugin is missing.',
      'This means npm install did not complete in the same directory that contains package.json.',
      'Expected path:',
      p,
      '',
      'Fixes to try:',
      '  • Ensure EAS builds from the Lucidly subfolder (the folder with android/, node_modules/, package.json).',
      '  • Make sure npm install succeeded (no peer-conflict errors).',
      '  • In eas.json, stay on Node 20 and enable legacy peer deps (you already did).',
    ].join('\n')
  );
  process.exit(1);
} else {
  console.log('✅ Found @react-native/gradle-plugin at', p);
}
