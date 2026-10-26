import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
const source = fs.readFileSync(new URL('../src/reviewEvidence.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
const { runForImage, reviewsForRun, candidateViewport } = await import('data:text/javascript;base64,' + Buffer.from(js).toString('base64'));
test('a result never crosses image identity', () => {
  const result = { id: 'run', image_id: 'a' };
  assert.equal(runForImage('a', result), result);
  assert.equal(runForImage('b', result), null);
});
test('case-only and other-run reviews are never silently substituted', () => {
  const reviews = [{id:'legacy'}, {id:'first', analysis_event_id:'a'}, {id:'second', analysis_event_id:'b'}];
  assert.deepEqual(reviewsForRun(reviews, 'a').map(r => r.id), ['first']);
  assert.deepEqual(reviewsForRun(reviews), []);
});
test('candidate focus respects letterboxing and rejects invalid bounds', () => {
  assert.deepEqual(candidateViewport([246,246,266,266], 800, 400), {zoom:5, offset:{x:0,y:0}});
  assert.equal(candidateViewport([10,10,9,12], 800, 400), null);
  assert.equal(candidateViewport([0,0,513,512], 800, 400), null);
  assert.equal(candidateViewport([0,NaN,40,40], 800, 400), null);
});
