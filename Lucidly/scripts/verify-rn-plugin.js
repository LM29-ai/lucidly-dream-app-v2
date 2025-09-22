const fs = require('fs');
const path = require('path');

const pluginPath = path.join(__dirname, '..', 'node_modules', '@react-native', 'gradle-plugin');

if (!fs.existsSync(pluginPath)) {
  console.error(
    [
      "❌ @react-native/gradle-plugin is missing.",
      "EAS (or local) didn’t install dependencies where Gradle expects them.",
      "Expected path:",
      "  " + pluginPath,
      "",
      "Fixes:",
      "  • Ensure the build runs in the folder that has android/ and package.json (Lucidly).",
      "  • Make sure `npm ci` or `npm install` succeeded (no peer-conflict errors).",
      "  • Keep Node 20.17 and LEGACY_PEER_DEPS=true in eas.json (you already do)."
    ].join("\n")
  );
  process.exit(1);
} else {
  console.log("✅ Found @react-native/gradle-plugin at", pluginPath);
}
