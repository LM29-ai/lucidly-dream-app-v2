// scripts/postinstall.js
const { spawnSync } = require("child_process");

function run(cmd, args) {
  const res = spawnSync(cmd, args, {
    stdio: "inherit",
    shell: process.platform === "win32", // allow npx on Windows
  });
  if (res.status !== 0) {
    console.log(`[postinstall] ${cmd} ${args.join(" ")} failed (ignored)`);
  }
}

try {
  run("npx", ["--yes", "patch-package"]);
} catch (_) {
  console.log("[postinstall] patch-package not available (ignored)");
}

try {
  run("node", ["scripts/patch-rn-gradle-plugin.js"]);
} catch (_) {
  console.log("[postinstall] gradle plugin patch missing (ignored)");
}
