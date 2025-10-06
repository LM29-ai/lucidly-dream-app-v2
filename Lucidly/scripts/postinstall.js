// scripts/postinstall.js
const { spawnSync } = require("child_process");

function run(cmd, args) {
  const res = spawnSync(cmd, args, {
    stdio: "inherit",
    shell: process.platform === "win32",
  });
  return res.status === 0;
}

// Best-effort patch-package (ok if not present)
try {
  run("npx", ["--yes", "patch-package"]);
} catch {
  console.log("[postinstall] patch-package not available (ignored)");
}

// Optional Gradle plugin patch (ok if missing)
try {
  run("node", ["scripts/patch-rn-gradle-plugin.js"]);
} catch {
  console.log("[postinstall] gradle plugin patch missing (ignored)");
}

console.log("[postinstall] done");
