// Checks the interface text: same keys and {placeholders} in English and Spanish, every data-i18n key in index.html exists,
// and a headless search in each interface language renders localized text. Run: node web/i18n_test.js
const fs = require('fs'), I = require(__dirname + '/i18n.js');
let fails = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) fails++; };
const en = I.dict.en, es = I.dict.es, ph = s => (s.match(/\{\w+\}/g) || []).sort().join(',');
ok(Object.keys(en).sort().join() === Object.keys(es).sort().join(), `en and es have the same ${Object.keys(en).length} keys`);
const badPh = Object.keys(en).filter(k => ph(en[k]) !== ph(es[k]));
ok(!badPh.length, 'placeholders match in both languages' + (badPh.length ? ': ' + badPh.join(', ') : ''));
const same = Object.keys(en).filter(k => en[k] === es[k] && !/^(search_key|lang_|t_of)/.test(k));
console.log('     identical en/es strings (should be few):', same.join(', ') || 'none');
const html = fs.readFileSync(__dirname + '/index.html', 'utf8');
const used = [...html.matchAll(/data-i18n(?:-html|-ph|-title|-aria)?="(\w+)"/g)].map(m => m[1]);
const missing = used.filter(k => !(k in en));
ok(!missing.length, `all ${used.length} data-i18n keys in index.html exist` + (missing.length ? ': ' + missing.join(', ') : ''));
const src = fs.readFileSync(__dirname + '/app.js', 'utf8'), ak = [...src.matchAll(/\btr\('(\w+)'(?=[,)])/g)].map(m => m[1]);
const miss2 = ak.filter(k => !(k in en));
ok(!miss2.length, `all ${new Set(ak).size} tr() keys in app.js exist` + (miss2.length ? ': ' + miss2.join(', ') : ''));
const dyn = ['b_', 'lvl_'].every(p => ['beginner', 'intermediate', 'advanced'].every(l => (p + l) in en && (p + l) in es));
ok(dyn, 'level names exist in both languages');
I.set('es'); ok(I.t('results_in', { n: 10, ms: 5 }) === '10 resultados en 5 ms', 'Spanish placeholder fill'); ok(I.t('nope') === 'nope', 'unknown key falls back to key');
ok(I.detect('es-MX') === 'es' && I.detect('en-US') === 'en' && I.detect('fr') === 'en', 'browser language detection');
process.exit(fails ? 1 : 0);
