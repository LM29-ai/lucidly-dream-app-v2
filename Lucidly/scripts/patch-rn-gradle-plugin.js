/**
 * No-op RN Gradle plugin patch so postinstall never fails in CI.
 * Replace with a real patch later if you actually need one.
 */
try {
  console.log("[postinstall] skip: no RN Gradle plugin patch required");
} catch {}
