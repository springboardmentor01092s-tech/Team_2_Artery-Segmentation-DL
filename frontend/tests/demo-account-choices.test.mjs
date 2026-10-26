import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const source = fs.readFileSync(new URL('../src/demoSessions.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const sandbox = { exports: {} };
vm.runInNewContext(compiled, sandbox);
const { demoAccountChoices } = sandbox.exports;
const account = (id, role, email, name = 'Demo User') => ({ id, role, email, name, token: 'test-only' });
const choices = [
  account('radiologist', 'clinician', 'radiologist.demo@example.com'),
  account('doctor', 'doctor', 'doctor.demo@example.com'),
  account('institution', 'doctor', 'researcher@corovision.example.org', 'Demo Institutional Researcher'),
  account('researcher', 'researcher', 'researcher.demo@example.com'),
];

test('keeps doctor and clinician distinct and omits institutional demo', () => {
  const result = demoAccountChoices(choices);
  assert.deepEqual(Array.from(result, item => item.id), ['doctor', 'radiologist', 'researcher']);
  assert.equal(choices.length, 4);
});

test('hides current clinician role without hiding doctor or merging real users', () => {
  const real = [account('one', 'doctor', 'one@hospital.org', 'Doctor One'), account('two', 'doctor', 'two@hospital.org', 'Doctor Two')];
  const result = demoAccountChoices([...choices, ...real], 'clinician');
  assert.deepEqual(Array.from(result, item => item.id), ['doctor', 'researcher', 'one', 'two']);
});
