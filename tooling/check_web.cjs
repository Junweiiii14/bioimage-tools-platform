'use strict';

const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { spawnSync } = require('node:child_process');
const root = resolve(__dirname, '..');
const manifest = require('../package.json');
const expectedNode = readFileSync(resolve(root, '.node-version'), 'utf8').trim();
if (process.versions.node !== expectedNode) {
    console.error(`Use Node ${expectedNode}; found ${process.versions.node}`);
    process.exit(1);
}
for (const [name, version] of Object.entries(manifest.devDependencies)) {
    let installed;
    try {
        installed = require(resolve(root, 'node_modules', name, 'package.json')).version;
    } catch {
        console.error('Install locked web development tools: npm ci --ignore-scripts');
        process.exit(1);
    }
    if (installed !== version) {
        console.error(`${name}: expected ${version}, found ${installed}; run npm ci --ignore-scripts`);
        process.exit(1);
    }
}
const web = 'apps/desktop/src/bioimage_app/web_ui/*.js';
const commands = [
    ['node_modules/prettier/bin/prettier.cjs', '--check', web],
    ['node_modules/eslint/bin/eslint.js', web, '--max-warnings', '0'],
    ['node_modules/typescript/bin/tsc', '--project', 'tsconfig.web.json'],
    ['--test', 'tooling/web_quality.test.cjs'],
];
for (const args of commands) {
    const result = spawnSync(process.execPath, args, { cwd: root, stdio: 'inherit' });
    if (result.error) console.error(result.error.message);
    if (result.status !== 0) process.exit(result.status || 1);
}
