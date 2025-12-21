// app.config.js
const { withSettingsGradle } = require("@expo/config-plugins");

module.exports = (config) => {
  return withSettingsGradle(config, (mod) => {
    const c = mod.modResults.contents;

    // Fix the common broken output where plugin IDs appear as bare symbols:
    // plugins { com.facebook.react.settings  expo.settings }
    mod.modResults.contents = c
      .replace(/plugins\s*\{\s*com\.facebook\.react\.settings/g, 'plugins {\n  id("com.facebook.react.settings")')
      .replace(/^\s*com\.facebook\.react\.settings\s*$/gm, 'id("com.facebook.react.settings")')
      .replace(/^\s*expo\.settings\s*$/gm, 'id("expo.settings")');

    // Also ensure expo.settings line is properly wrapped if it appears in plugins {}
    if (mod.modResults.contents.includes("id(\"com.facebook.react.settings\")") &&
        !mod.modResults.contents.includes("id(\"expo.settings\")")) {
      mod.modResults.contents = mod.modResults.contents.replace(
        /id\("com\.facebook\.react\.settings"\)\s*\n?\}/,
        'id("com.facebook.react.settings")\n  id("expo.settings")\n}'
      );
    }

    return mod;
  });
};
