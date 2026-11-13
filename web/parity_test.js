function loadIdx(l){const fs_=require('fs');const d=JSON.parse(fs_.readFileSync(__dirname+'/data/'+l+'.json','utf8'));for(let i=2;i<=(d.parts||0)+1;i++)Object.assign(d.terms,JSON.parse(fs_.readFileSync(__dirname+'/data/'+l+'.p'+i+'.json','utf8')));return d;}
// Compares JS top-10 with Python's (web/parity_expected.json from lingualadder.web_parity). Run: node web/parity_test.js
const fs = require('fs'), path = require('path');
const LL = require('./ll.js');
const exp = JSON.parse(fs.readFileSync(path.join(__dirname, 'parity_expected.json'), 'utf8'));
const cache = {};
let bad = 0, total = 0;
for (const c of exp) {
  const idx = cache[c.lang] || (cache[c.lang] = loadIdx(c.lang));
  const res = LL.search(idx, c.query, { target: c.target });
  const got = res.map(r => r.id);
  const ok = JSON.stringify(got) === JSON.stringify(c.ids);
  const maxdiff = Math.max(...res.map((r, i) => Math.abs(r.score - c.scores[i])));
  total++; if (!ok || maxdiff > 1e-3) bad++;
  console.log((ok && maxdiff <= 1e-3 ? 'OK  ' : 'FAIL'), c.lang, c.level, JSON.stringify(c.query), 'maxScoreDiff', maxdiff.toExponential(1));
}
console.log(total - bad + '/' + total + ' match');
process.exit(bad ? 1 : 0);
