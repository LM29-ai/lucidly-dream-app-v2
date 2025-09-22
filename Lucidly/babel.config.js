// babel.config.js — SDK 54 safe config
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    // No expo-router/babel here on SDK 50+
    // If you use Reanimated, add it LAST:
    // plugins: ['react-native-reanimated/plugin'],
  };
};
