// Word lookups in the browser version: snippet word pieces, Wiktionary links in the interface language,
// and marking a word as new removes it from the assumed-known set (en and es). Run: node web/lookup_test.js
const fs = require('fs'), LL = require(__dirname + '/ll.js');
let fails = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) fails++; };
const p = LL.wordPieces("Volcán: l'état d'un mont—it's 3 km.");
ok(p.map(x => x.t).join('') === "Volcán: l'état d'un mont—it's 3 km.", 'pieces rebuild the text exactly');
ok(p.filter(x => x.w).map(x => x.t).join('|') === "Volcán|l'état|d'un|mont|it's|km", 'word pieces keep accents and apostrophes, skip digits');
ok(LL.wiktionaryUrl('Volcán', 'es', 'en') === 'https://en.wiktionary.org/wiki/volc%C3%A1n#Spanish', 'Spanish word, English interface');
ok(LL.wiktionaryUrl('volcano', 'en', 'es') === 'https://es.wiktionary.org/wiki/volcano#Ingl%C3%A9s', 'English word, Spanish interface');
for (const lang of ['en', 'es']) {
  const idx = JSON.parse(fs.readFileSync(__dirname + '/data/' + lang + '.json'));
  if (idx.parts) { /* parts are merged by the page loader; the first part is enough for the known-word list */ }
  const base = LL.knownWords(idx, 'intermediate');
  const w = [...base][5], w2 = [...base][50];
  const k = LL.knownWords(idx, 'intermediate', [w, w2.toUpperCase()]);
  ok(base.has(w) && !k.has(w) && !k.has(w2) && k.size === base.size - 2, `${lang}: marking 2 words as new removes exactly them from ${base.size} known words`);
  const q = lang === 'en' ? 'volcano' : 'volcán', t = idx.targets.intermediate;
  const a = LL.search(idx, q, { target: t, known: base }).map(r => r.id), b = LL.search(idx, q, { target: t, known: k }).map(r => r.id);
  ok(a.length === 10 && b.length === 10, `${lang}: search still returns 10 results with marked words`);
}
process.exit(fails ? 1 : 0);
