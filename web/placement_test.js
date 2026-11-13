// Checks the placement test generator and simulates learners of known ability. Run: node web/placement_test.js
const fs = require('fs'), P = require(__dirname + '/placement.js');
let fails = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) fails++; };
for (const lang of ['en', 'es']) {
  const idx = JSON.parse(fs.readFileSync(__dirname + `/data/${lang}.json`, 'utf8'));
  const v = P.vocabItems(idx, 7, lang);
  ok(v.filter(x => x.real).length === 18 && v.filter(x => !x.real).length >= 5, `${lang} vocab: ${v.filter(x=>x.real).length} real + ${v.filter(x=>!x.real).length} fake (${v.filter(x=>!x.real).map(x=>x.word).join(', ')})`);
  ok(P.scoreVocab(v, v.map(x => x.real)) === 1 && P.scoreVocab(v, v.map(() => true)) === 0, `${lang} vocab scoring: perfect=1, say-yes-to-all=0`);
  const r = P.rng(3), used = new Set(); let n = 0;
  for (const q of [0.1, 0.3, 0.5, 0.7, 0.9]) { const c = P.clozeItem(idx, q, r, used); if (c && c.text.includes('_____') && c.options.includes(c.answer) && c.options.length === 4) n++; if (q===0.5&&c) console.log('     sample:', c.text.slice(0,110), '|', c.options.join(' / '), '| answer', c.answer); }
  ok(n === 5, `${lang} cloze items generated at 5 difficulty levels: ${n}/5`);
  // Simulated learners: P(correct) = logistic((ability - item quantile) * 8) with a 25% guessing floor.
  const errs = [];
  for (const ability of [0.15, 0.35, 0.5, 0.65, 0.85]) for (let s = 0; s < 40; s++) {
    const rr = P.rng(1000 + s * 7 + Math.round(ability * 100)), st = new P.Staircase(), u = new Set();
    while (!st.done()) { const c = P.clozeItem(idx, st.q, rr, u); if (!c) break; const p = 0.25 + 0.75 / (1 + Math.exp(-(ability - st.q) * 8)); st.record(rr() < p); }
    errs.push({ ability, est: st.estimate() });
  }
  const mae = errs.reduce((a, e) => a + Math.abs(e.est - e.ability), 0) / errs.length;
  const byA = [0.15, 0.5, 0.85].map(a => (errs.filter(e => e.ability === a).reduce((s, e) => s + e.est, 0) / 40).toFixed(2));
  ok(mae < 0.2 && byA[0] < byA[1] && byA[1] < byA[2], `${lang} simulated learners: mean abs error ${mae.toFixed(3)} in quantile; mean estimate for ability 0.15/0.50/0.85 = ${byA.join('/')}`);
}
process.exit(fails ? 1 : 0);
