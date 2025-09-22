const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
config.projectRoot = __dirname;   // lock to this folder
config.watchFolders = [];         // don’t scan parent dirs

module.exports = config;
