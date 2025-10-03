// app.config.js
export default {
  expo: {
    name: "Lucidly",
    slug: "lucidly",
    version: "1.0.0",
extra: {
      eas: { projectId: "a38e5048-5154-4fe9-ac8c-a58e3cd72b61" }
    // Android package (required for EAS GitHub builds)
    android: {
      package: "com.lm29ai.lucidly", // <-- change if you use a different app id
    },

    // Optional (kept minimal). Add icons/splash when ready:
    // icon: "./assets/icon.png",
    // splash: { image: "./assets/splash.png", resizeMode: "contain", backgroundColor: "#ffffff" },
  },
};
