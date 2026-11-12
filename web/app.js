const $ = id => document.getElementById(id);
const cache = {};
async function loadIndex(lang) {
  if (!cache[lang] && window.LL_EMBEDDED && window.LL_EMBEDDED[lang]) cache[lang] = window.LL_EMBEDDED[lang];
  if (!cache[lang]) {
    const r = await fetch(`data/${lang}.json`);
    if (!r.ok) throw new Error('Could not load the ' + lang + ' index');
    cache[lang] = await r.json();
  }
  return cache[lang];
}
const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const pct = x => Math.round(x * 100);

async function run() {
  const q = $('q').value.trim();
  if (!q) return;
  const lang = $('lang').value, level = $('level').value;
  $('status').textContent = 'Loading index…';
  let idx;
  try { idx = await loadIndex(lang); } catch (e) { $('status').textContent = e.message; return; }
  const t0 = performance.now();
  const res = LL.search(idx, q, { target: idx.targets[level], rerank: !$('plain').checked });
  const ms = Math.round(performance.now() - t0);
  if (!res.length) { $('results').innerHTML = '<li class="empty">No matches. Try a simpler or different word, or switch language.</li>'; $('status').textContent = 'No results'; return; }
  $('status').textContent = res.length ? `${res.length} results in ${ms} ms (` + Object.entries(res.reduce((a,r)=>{const c=cefr(r.difficulty);a[c]=(a[c]||0)+1;return a;},{})).sort().map(([k,v])=>k+' ×'+v).join(', ') + `)` + ($('plain').checked ? ' (plain BM25)' : ` fitted to ${level}`) : 'No matches. Try other words.';
  const cefr = d => { d=Math.min(Math.max(+d,0),1); const b=[[.2,'A1'],[.61,'A2'],[.87,'B1'],[.94,'B2'],[.98,'C1']]; for (const [h,l] of b) if (d<h) return l; return 'C2'; };
  const card = r => `
    <li><h3><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a></h3>
      <p>${esc(r.snippet)}</p>
      <div class="meta"><span class="badge ${esc(r.level)}">${esc(r.level)}</span> <span class="badge">${cefr(r.difficulty)}</span>
        <span>difficulty ${pct(r.difficulty)}</span>
        <span>relevance <span class="bar"><i style="width:${pct(r.relevance)}%"></i></span></span>
        <span>level fit <span class="bar"><i style="width:${pct(r.fit)}%"></i></span></span>
        <span>${r.words} words</span>
        <a class="full" href="${esc(r.url)}" target="_blank" rel="noopener">Read full article on Wikipedia &rarr;</a></div></li>`;
  if ($('cmp').checked) {
    const base = LL.search(idx, q, { target: idx.targets[level], rerank: false });
    $('results').className = 'cols';
    $('results').innerHTML = `<li class="col"><h2>Plain BM25</h2><ol>${base.map(card).join('')}</ol></li><li class="col"><h2>LinguaLadder (${esc(level)})</h2><ol>${res.map(card).join('')}</ol></li>`;
  } else { $('results').className = ''; $('results').innerHTML = res.map(card).join(''); }
}
$('f').addEventListener('submit', e => { e.preventDefault(); run(); });
$('reader').addEventListener('change', () => document.body.classList.toggle('reader', $('reader').checked));
for (const id of ['lang', 'level', 'plain', 'cmp']) $(id).addEventListener('change', () => $('q').value.trim() && run());
// Remember profile choices and support shareable ?q= links
(function () {
  try {
    const p = new URLSearchParams(location.search), s = JSON.parse(localStorage.getItem('ll_profile') || '{}');
    for (const id of ['lang', 'level']) { const v = p.get(id) || s[id]; if (v && [...$(id).options].some(o => o.value === v)) $(id).value = v; }
    for (const id of ['lang', 'level']) $(id).addEventListener('change', () => { s[id] = $(id).value; localStorage.setItem('ll_profile', JSON.stringify(s)); });
    $('f').addEventListener('submit', () => { const u = new URL(location); u.searchParams.set('q', $('q').value.trim()); history.replaceState(null, '', u); });
    if (p.get('q')) { $('q').value = p.get('q'); run(); }
  } catch (e) {}
})();
// Keyboard shortcut: "/" focuses the search box; Escape clears it
document.addEventListener('keydown', e => {
  const t = e.target.tagName;
  if (e.key === '/' && t !== 'INPUT' && t !== 'SELECT') { e.preventDefault(); $('q').focus(); $('q').select(); }
  else if (e.key === 'Escape' && e.target === $('q')) { $('q').value = ''; }
});
