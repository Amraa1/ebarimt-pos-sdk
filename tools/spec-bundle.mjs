import { mkdir } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { spawn } from "node:child_process";

const root = process.cwd();
const specPath = path.join(root, "spec", "openapi", "posapi-3.0.yaml");
const outDir = path.join(root, "spec", "openapi", ".normalized");
const outPath = path.join(outDir, "posapi-3.0.json");

function runCapture(cmd, args) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { shell: process.platform === "win32" });
    let stdout = "";
    let stderr = "";

    p.stdout.on("data", (d) => (stdout += d));
    p.stderr.on("data", (d) => (stderr += d));

    p.on("close", (code) => {
      if (code !== 0) {
        reject(
          new Error(
            `Command failed: ${cmd} ${args.join(" ")}\n\nSTDOUT:\n${stdout}\n\nSTDERR:\n${stderr}`,
          ),
        );
      } else {
        resolve(stdout);
      }
    });
  });
}

async function main() {
  await mkdir(outDir, { recursive: true });

  const bundled = await runCapture("npx", [
    "--no",
    "redocly",
    "bundle",
    specPath,
    "--output",
    outPath,
  ]);

  console.log(`OK: wrote ${path.relative(root, outPath)}`);
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
