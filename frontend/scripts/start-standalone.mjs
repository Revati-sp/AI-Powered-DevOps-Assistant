import { cpSync, existsSync } from "node:fs";
import { join } from "node:path";
import { spawn } from "node:child_process";

const root = process.cwd();
const standalone = join(root, ".next", "standalone");
const serverJs = join(standalone, "server.js");

if (!existsSync(serverJs)) {
  console.error("Missing .next/standalone/server.js. Run `npm run build` first.");
  process.exit(1);
}

cpSync(join(root, "public"), join(standalone, "public"), { recursive: true });
cpSync(join(root, ".next", "static"), join(standalone, ".next", "static"), {
  recursive: true,
});

const child = spawn(process.execPath, [serverJs], {
  cwd: standalone,
  stdio: "inherit",
  env: {
    ...process.env,
    PORT: process.env.PORT ?? "3000",
    HOSTNAME: process.env.HOSTNAME ?? "0.0.0.0",
    NODE_ENV: "production",
  },
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
