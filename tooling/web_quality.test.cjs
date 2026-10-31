'use strict';

const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');
const root = resolve(__dirname, '..');
const payloadFile = 'apps/desktop/src/bioimage_app/web_ui/bridge_payload.js';

function cli(script, args, input) {
    return spawnSync(process.execPath, [script, ...args], { cwd: root, input, encoding: 'utf8' });
}

test('format gate rejects an unformatted input and accepts formatted input', () => {
    const args = ['--check', '--stdin-filepath', payloadFile];
    const bad = cli('node_modules/prettier/bin/prettier.cjs', args, 'function value(){return 1}\n');
    assert.equal(bad.status, 1, bad.stdout + bad.stderr);
    const good = cli('node_modules/prettier/bin/prettier.cjs', args, 'function value() {\n    return 1;\n}\n');
    assert.equal(good.status, 0, good.stdout + good.stderr);
});

test('lint gate rejects unreachable code in the production file scope', () => {
    const args = ['--stdin', '--stdin-filename', payloadFile, '--max-warnings', '0'];
    const bad = cli('node_modules/eslint/bin/eslint.js', args, 'function f() { return 1; throw Error(); }');
    assert.equal(bad.status, 1, bad.stdout + bad.stderr);
    assert.match(bad.stdout, /no-unreachable/);
    const good = cli('node_modules/eslint/bin/eslint.js', args, 'function f() { return 1; }');
    assert.equal(good.status, 0, good.stdout + good.stderr);
});

function contractDiagnostics(source) {
    const config = ts.readConfigFile(resolve(root, 'tsconfig.web.json'), ts.sys.readFile);
    assert.equal(config.error, undefined);
    const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys, root);
    assert.equal(parsed.errors.length, 0);
    const file = resolve(root, '.local/web-quality-controlled-input.js');
    const host = ts.createCompilerHost(parsed.options);
    const original = host.getSourceFile.bind(host);
    host.getSourceFile = (name, languageVersion, onError, shouldCreateNewSourceFile) =>
        resolve(name) === file
            ? ts.createSourceFile(file, source, languageVersion, true, ts.ScriptKind.JS)
            : original(name, languageVersion, onError, shouldCreateNewSourceFile);
    const program = ts.createProgram([...parsed.fileNames, file], parsed.options, host);
    return ts.getPreEmitDiagnostics(program);
}

test('checkJs rejects wrong identity and request types at the real payload producer', () => {
    const valid = "makeAdvancedRequest({projectId:'p',sessionEpoch:1,revision:2},'r','open',{});";
    assert.deepEqual(contractDiagnostics(valid), []);
    const wrongRevision = contractDiagnostics(valid.replace('revision:2', "revision:'wrong'"));
    assert.ok(wrongRevision.some(diagnostic => diagnostic.code === 2322));
    const wrongRequest = contractDiagnostics(valid.replace("},'r'", '},5'));
    assert.ok(wrongRequest.some(diagnostic => diagnostic.code === 2345));
});

test('typed producer keeps the existing advanced request wire representation', () => {
    const source = readFileSync(resolve(root, payloadFile), 'utf8');
    const encoded = vm.runInNewContext(
        source + "\nJSON.stringify(makeAdvancedRequest({projectId:'p',sessionEpoch:3,revision:7},'r','open',{section:'ocr'}));",
        {},
    );
    assert.equal(encoded, '{"schema_version":1,"requestId":"r","projectId":"p","sessionEpoch":3,"revision":7,"operation":"open","value":{"section":"ocr"}}');
});
