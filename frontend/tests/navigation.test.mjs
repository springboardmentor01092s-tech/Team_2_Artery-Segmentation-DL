import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const source = fs.readFileSync(new URL('../src/permissions.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const sandbox = { exports: {} };
vm.runInNewContext(compiled, sandbox);
const { canOpenSection } = sandbox.exports;

test('viewer and ML navigation do not acquire case operations', () => {
  assert.equal(canOpenSection('cases', 'viewer'), true);
  for (const role of ['viewer', 'ml_engineer']) {
    for (const view of ['uploads', 'reviews', 'admin', 'permissions', 'access', 'audit']) assert.equal(canOpenSection(view, role), false);
  }
  for (const view of ['cases', 'analysis', 'reports']) assert.equal(canOpenSection(view, 'ml_engineer'), false);
  assert.equal(canOpenSection('models', 'ml_engineer'), true);
});

test('professional sections retain explicit scope', () => {
  assert.equal(canOpenSection('uploads', 'researcher'), true);
  assert.equal(canOpenSection('reviews', 'researcher'), false);
  assert.equal(canOpenSection('reviews', 'clinician'), true);
  assert.equal(canOpenSection('reviews', 'doctor'), true);
  assert.equal(canOpenSection('reviews', 'technician'), false);
  for (const view of ['admin', 'permissions', 'access', 'audit']) {
    assert.equal(canOpenSection(view, 'admin'), true);
    assert.equal(canOpenSection(view, 'researcher'), false);
  }
});

test('administrator includes clinical sections alongside management', () => {
  for (const view of ['cases', 'uploads', 'analysis', 'reports', 'reviews', 'admin', 'audit']) assert.equal(canOpenSection(view, 'admin', []), true);
  assert.equal(canOpenSection('uploads', 'admin', ['case:upload']), true);
  assert.equal(canOpenSection('analysis', 'admin', ['case:upload']), true);
  assert.equal(canOpenSection('analysis', 'admin', ['analysis:run']), true);
  assert.equal(canOpenSection('reports', 'admin', ['analysis:export']), true);
});

test('unknown sections are denied', () => {
  for (const role of ['viewer', 'researcher', 'clinician', 'ml_engineer', 'admin']) assert.equal(canOpenSection('training-submit', role), false);
  assert.equal(canOpenSection('overview', undefined), false);
});
