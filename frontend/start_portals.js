#!/usr/bin/env node
/**
 * start_portals.js
 * Launches all 5 dedicated portal dev servers simultaneously on separate ports.
 * Run with: npm run dev:all
 */

import { spawn } from 'child_process';

const portals = [
  { id: 'admin',     port: 5173 },
  { id: 'victim',    port: 5174 },
  { id: 'authority', port: 5175 },
  { id: 'donor',     port: 5176 },
  { id: 'volunteer', port: 5177 },
];

const colors = {
  admin:     '\x1b[31m',   // red
  victim:    '\x1b[35m',   // magenta
  authority: '\x1b[34m',   // blue
  donor:     '\x1b[32m',   // green
  volunteer: '\x1b[33m',   // yellow
  reset:     '\x1b[0m',
};

console.log('\n+-----------------------------------------------------+');
console.log('|  Disaster Relief System  Multi-Portal Launcher      |');
console.log('+-----------------------------------------------------+');
portals.forEach(({ id, port }) => {
  console.log(`|  ${colors[id]}${id.padEnd(12)}${colors.reset}  ->  http://localhost:${port}              |`);
});
console.log('+-----------------------------------------------------+\n');

const processes = [];

for (const { id, port } of portals) {
  const isWin = process.platform === 'win32';
  const cmd = isWin ? 'npx.cmd' : 'npx';

  const child = spawn(cmd, ['vite', '--port', String(port), '--host'], {
    cwd: process.cwd(),
    env: {
      ...process.env,
      VITE_PORTAL_TYPE: id,
      FORCE_COLOR: '1',
    },
    shell: isWin,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  const label = `[${id.toUpperCase().padEnd(9)}:${port}]`;
  const color = colors[id];

  child.stdout.on('data', (data) => {
    const lines = data.toString().split('\n').filter(Boolean);
    lines.forEach((line) => {
      console.log(`${color}${label}${colors.reset} ${line}`);
    });
  });

  child.stderr.on('data', (data) => {
    const lines = data.toString().split('\n').filter(Boolean);
    lines.forEach((line) => {
      console.error(`${color}${label}${colors.reset} \x1b[90m${line}${colors.reset}`);
    });
  });

  child.on('close', (code) => {
    console.log(`\n${color}${label}${colors.reset} exited with code ${code}`);
  });

  child.on('error', (err) => {
    console.error(`${color}${label}${colors.reset} \x1b[91mError: ${err.message}${colors.reset}`);
  });

  processes.push(child);
}

// Graceful shutdown
const shutdown = () => {
  console.log('\n\nShutting down all portal servers...');
  processes.forEach((p) => p.kill('SIGTERM'));
  process.exit(0);
};

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
process.on('exit', shutdown);
