// CEFR band cut-offs in ll.js must equal lingualadder/search.py (CEFR_CUTS), per language.
const fs = require('fs'), LL = require(__dirname + '/ll.js');
const py = fs.readFileSync(__dirname + '/../lingualadder/search.py', 'utf8');
let bad = 0;
for (const lang of ['en', 'es']) {
  const m = py.match(new RegExp('"' + lang + '":\\s*\\[([^\\]]+)\\]'));
  const cuts = m[1].split(',').map(Number);
  const same = JSON.stringify(cuts) === JSON.stringify(LL.CEFR_CUTS[lang]);
  console.log(same ? 'OK  ' : 'FAIL', lang, 'cuts match search.py', cuts.join(','));
  if (!same) bad++;
}
const exp = [[0, 'en', 'A1'], [0.2, 'en', 'B1'], [0.5, 'en', 'B2'], [0.9, 'en', 'C2'], [0.2, 'es', 'B2'], [0.5, 'es', 'C1'], [0.99, 'es', 'C2'], [1, 'es', 'C2']];
for (const [d, l, want] of exp) { const got = LL.cefr(d, l); if (got !== want) { console.log('FAIL', d, l, got, want); bad++; } }
// display split mirrors search.py CEFR_SPLIT
const m2 = py.match(/CEFR_SPLIT = \{"en": \("(\w+)", ([\d.]+)\), "es": \("(\w+)", ([\d.]+)\)\}/);
const pySplit = { en: [m2[1], +m2[2]], es: [m2[3], +m2[4]] };
if (JSON.stringify(pySplit) !== JSON.stringify(LL.CEFR_SPLIT)) { console.log('FAIL split differs from search.py'); bad++; }
const exp2 = [[0.9, 'en', 'C2'], [0.96, 'en', 'C2+'], [0.5, 'en', 'B2'], [0.5, 'es', 'C1'], [0.9, 'es', 'C1+'], [0.99, 'es', 'C2'], [0.7, 'es', 'C1']];
for (const [d, l, want] of exp2) { const got = LL.cefrDisplay(d, l); if (got !== want) { console.log('FAIL display', d, l, got, want); bad++; } }
console.log(bad ? 'FAILED' : 'cefr: OK'); process.exit(bad ? 1 : 0);
