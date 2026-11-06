import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
const source = fs.readFileSync(new URL('../src/savedRunNavigation.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
const { savedRunForImage, analysisLocation, pinnedRunForImage, savedImageForRequest, clearAnalysisLocation } = await import('data:text/javascript;base64,' + Buffer.from(js).toString('base64'));

test('refresh chooses the exact historical run, never a newer or other-image result', () => {
  const items = [{ id: 'new', image_id: 'a' }, { id: 'old', image_id: 'a' }, { id: 'other', image_id: 'b' }];
  assert.equal(savedRunForImage(items, 'a', 'old'), items[1]);
  assert.equal(savedRunForImage(items, 'a', 'missing'), null);
  assert.equal(savedRunForImage(items, 'a', 'other'), null);
  assert.equal(savedRunForImage(items, 'a', null), items[0]);
});

test('saved selection round-trips encoded identifiers and preserves unrelated URL state', () => {
  const path = analysisLocation('https://example.org/app?mode=research#viewer', 'case & 18', 'image/114', 'run?one');
  const url = new URL(path, 'https://example.org');
  assert.equal(url.searchParams.get('case_id'), 'case & 18');
  assert.equal(url.searchParams.get('image_id'), 'image/114');
  assert.equal(url.searchParams.get('run_id'), 'run?one');
  assert.equal(url.searchParams.get('mode'), 'research');
  assert.equal(url.hash, '#viewer');
});

test('an explicitly pinned old run survives a newer history result', () => {
  const old = { id: 'old', image_id: 'a' };
  const pin = { imageId: 'a', runId: 'old' };
  assert.equal(pinnedRunForImage([old], 'a', pin), old);
  assert.equal(pinnedRunForImage([{ id: 'new', image_id: 'a' }, old], 'a', pin), old);
});

test('missing pinned evidence stays unavailable across history refreshes', () => {
  const pin = { imageId: 'a', runId: 'missing' };
  assert.equal(pinnedRunForImage([{ id: 'new', image_id: 'a' }], 'a', pin), null);
  assert.equal(pinnedRunForImage([{ id: 'newer', image_id: 'a' }, { id: 'new', image_id: 'a' }], 'a', pin), null);
  assert.equal(pinnedRunForImage([{ id: 'other', image_id: 'b' }], 'a', pin), null);
});

test('historical run links require the specified image and never borrow the latest image', () => {
  const images = [{ id: 'older-image' }, { id: 'newer-image' }];
  assert.equal(savedImageForRequest(images, 'older-image', 'run'), images[0]);
  assert.equal(savedImageForRequest(images, 'missing-image', 'run'), undefined);
  assert.equal(savedImageForRequest(images, null, 'run'), undefined);
  assert.equal(savedImageForRequest(images, null, null), images[1]);
});

test('leaving analysis or signing out removes only saved-analysis identifiers', () => {
  const url = new URL(clearAnalysisLocation('https://example.org/app?case_id=c&image_id=i&run_id=r&mode=research#section'), 'https://example.org');
  for (const key of ['case_id', 'image_id', 'run_id']) assert.equal(url.searchParams.has(key), false);
  assert.equal(url.searchParams.get('mode'), 'research');
  assert.equal(url.hash, '#section');
});
