const $ = id => document.getElementById(id);
const tr = (k, v) => LLI18n.t(k, v);
const langName = l => tr(l === 'es' ? 'lang_es' : 'lang_en');
const cache = {};
async function loadIndex(lang) {
  if (!cache[lang] && window.LL_EMBEDDED && window.LL_EMBEDDED[lang]) cache[lang] = window.LL_EMBEDDED[lang];
  if (!cache[lang]) {
    const r = await fetch(`data/${lang}.json`);
    if (!r.ok) throw new Error(tr('load_err', { lang: langName(lang) }));
    const idx = await r.json();
    for (let i = 2; i <= (idx.parts || 0) + 1; i++) {
      const rp = await fetch(`data/${lang}.p${i}.json`);
      if (!rp.ok) throw new Error(tr('load_err', { lang: langName(lang) }) + ' (' + i + ')');
      Object.assign(idx.terms, await rp.json());
    }
    cache[lang] = idx;
  }
  return cache[lang];
}
const cefr = (d, lang) => LL.cefr(d, lang || ($('lang') && $('lang').value) || 'en');
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const pct = x => Math.round(x * 100);
const LEVEL_NAMES = { get beginner() { return tr('lvl_beginner'); }, get intermediate() { return tr('lvl_intermediate'); }, get advanced() { return tr('lvl_advanced'); } };
const lvBadge = l => tr('b_' + l);

// ---- Learner profile: language, level, placement result, reading history (kept in this browser only)
const prof = (() => { try { return JSON.parse(localStorage.getItem('ll_profile') || '{}'); } catch (e) { return {}; } })();
prof.read = prof.read || []; prof.place = prof.place || {}; prof.words = prof.words || {};
const myWords = lang => prof.words[lang] || (prof.words[lang] = []);
const save = () => { try { localStorage.setItem('ll_profile', JSON.stringify(prof)); } catch (e) {} };
function sorted(idx) { return idx._sd || (idx._sd = idx.docs.map(d => d[4]).sort((a, b) => a - b)); }
function quantileOf(idx, t) { const s = sorted(idx); let i = 0; while (i < s.length && s[i] < t) i++; return i / Math.max(s.length - 1, 1); }
function targetFor(idx, lang) {
  const level = $('level').value, p = prof.place[lang];
  if (level === 'custom' && p && typeof LLPlace !== 'undefined') return LLPlace.quantileToTarget(idx, p.q);
  return idx.targets[level] ?? idx.targets.intermediate;
}
function showChip() {
  const p = prof.place[$('lang').value], chip = $('level-chip'), opt = $('custom-opt');
  if (p) { chip.hidden = false; chip.textContent = tr('chip', { cefr: p.cefr, level: LEVEL_NAMES[p.level] }); opt.hidden = false; opt.textContent = tr('lv_custom_opt', { cefr: p.cefr }); }
  else { chip.hidden = true; if (opt) opt.hidden = true; if ($('level').value === 'custom') $('level').value = 'intermediate'; }
}

// ---- Word lookups: tap a snippet word to look it up (Wiktionary in the interface language) and mark it as new.
// Marked words leave the assumed-known set, so snippets made of fewer new words rank higher (same term as the Python app).
function snippetHtml(text, lang) {
  const mine = new Set(myWords(lang));
  return LL.wordPieces(text).map(p => p.w ? `<span class="w${mine.has(p.t.toLowerCase()) ? ' mine' : ''}" role="button" tabindex="0" data-w="${esc(p.t)}">${esc(p.t)}</span>` : esc(p.t)).join('');
}
function openWord(el) {
  const li = el.closest('li'), pop = li && li.querySelector('.wordpop'); if (!pop) return;
  const lang = $('lang').value, w = el.dataset.w, lw = w.toLowerCase(), has = myWords(lang).includes(lw);
  pop.hidden = false;
  pop.innerHTML = `<b>${esc(w)}</b> <a href="${esc(LL.wiktionaryUrl(w, lang, LLI18n.get()))}" target="_blank" rel="noopener">${tr('word_look')} &rarr;</a> <button type="button" class="mini" data-markword="${esc(lw)}" data-mark="${has ? 0 : 1}">${tr(has ? 'word_unmark' : 'word_mark')}</button>`;
}
function setWord(w, on) {
  const lang = $('lang').value, list = myWords(lang), i = list.indexOf(w);
  if (on && i < 0) list.push(w); else if (!on && i >= 0) list.splice(i, 1);
  prof.words[lang] = list.slice(-300); save(); renderMyWords();
  $('status').textContent = tr(on ? 'word_added' : 'word_removed', { w });
  const keep = $('status').textContent;
  if ($('q').value.trim()) run().then(() => { $('status').textContent = keep + ' ' + $('status').textContent; });
}
function renderMyWords() {
  const box = $('mywords'); if (!box) return;
  const list = myWords($('lang').value);
  box.innerHTML = list.length ? list.map(w => `<button type="button" class="topic" data-markword="${esc(w)}" data-mark="0" title="${esc(tr('word_unmark'))}">${esc(w)} &times;</button>`).join('') : `<small class="muted">${tr('mywords_none')}</small>`;
  if ($('mywords-clear')) $('mywords-clear').hidden = !list.length;
}

// ---- Search
async function run() {
  const q = $('q').value.trim();
  if (!q) return;
  const lang = $('lang').value, level = $('level').value;
  $('status').textContent = tr('loading');
  let idx;
  try { idx = await loadIndex(lang); } catch (e) { $('status').textContent = e.message; return; }
  if (document.body.classList) document.body.classList.add('searched');
  const target = targetFor(idx, lang);
  const t0 = performance.now();
  const place = prof.place[lang], vlevel = level === 'custom' ? (place && place.level) || 'intermediate' : level;
  const known = $('vocab') && $('vocab').checked ? LL.knownWords(idx, vlevel, myWords(lang)) : null;  // words a learner at this level is assumed to know
  const res = LL.search(idx, q, { target, rerank: !$('plain').checked, known });
  const ms = Math.round(performance.now() - t0);
  if (!res.length) { $('results').innerHTML = '<li class="empty">' + esc(tr('empty')) + '</li>'; $('status').textContent = tr('no_results'); return; }
   $('status').textContent = tr('results_in', { n: res.length, ms }) + ' (' + Object.entries(res.reduce((a,r)=>{const c=cefr(r.difficulty);a[c]=(a[c]||0)+1;return a;},{})).sort().map(([k,v])=>k+' ×'+v).join(', ') + ')' + ($('plain').checked ? tr('plain_tag') : tr('fitted', { level: level === 'custom' ? tr('fitted_custom') : LEVEL_NAMES[level].toLowerCase() }));
  if (!$('plain').checked) {
    const off = res.filter(r => !r.onTopic).length;
    if (off === res.length) $('status').textContent += tr('all_mention');
    else if (off) $('status').textContent += tr('some_mention', { on: res.length - off, off });
  }
  const card = r => `
    <li class="lv-${esc(r.level)}${r.onTopic === false ? ' off-topic' : ''}" data-id="${esc(r.id)}"><h3><a href="${esc(r.url)}" target="_blank" rel="noopener" data-read="${esc(r.id)}">${esc(r.title)}</a></h3>
      <p class="snip" title="${esc(tr('word_tap'))}">${snippetHtml(r.snippet, lang)}</p><div class="wordpop" hidden></div>
      <div class="meta"><span class="badge ${esc(r.level)}">${esc(lvBadge(r.level))}</span> <span class="badge">${cefr(r.difficulty)}</span>${r.onTopic === false ? ` <span class="badge mention" title="${esc(tr('mentions_title'))}">${tr('mentions')}</span>` : ''}${prof.read.includes(r.id) ? ` <span class="badge">${tr('read_badge')}</span>` : ''}
        <span>${tr('relevance')} <span class="bar"><i style="width:${pct(r.relevance)}%"></i></span></span>
        <span>${tr('level_fit')} <span class="bar"><i style="width:${pct(r.fit)}%"></i></span></span>
        <span>${tr('words', { n: r.words })}</span>
        <a class="full" href="${esc(r.url)}" target="_blank" rel="noopener" data-read="${esc(r.id)}">${tr('read_on')} &rarr;</a></div>
      <div class="actions"><button type="button" class="mini" data-next="${esc(r.id)}">${tr('read_next')}</button><button type="button" class="mini" data-fb="too_easy">${tr('too_easy')}</button><button type="button" class="mini" data-fb="too_hard">${tr('too_hard')}</button></div>
      <div class="next" hidden></div></li>`;
  const ladder = ladderStrip(idx, q, target);
  if ($('cmp').checked) {
    const base = LL.search(idx, q, { target, rerank: false });
    $('results').className = 'cols';
    $('results').innerHTML = `<li class="col"><h2>${tr('plain_bm25')}</h2><ol>${base.map(card).join('')}</ol></li><li class="col"><h2>${esc(tr('ll_col', { level: level === 'custom' ? tr('lv_custom_plain') : LEVEL_NAMES[level] }))}</h2><ol>${res.map(card).join('')}</ol></li>`;
  } else { $('results').className = ''; $('results').innerHTML = ladder + res.map(card).join(''); }
}

// One on-topic pick per level, so every topic shows its easier and harder rungs.
function ladderStrip(idx, q, target) {
  if ($('plain').checked) return '';
  const all = LL.search(idx, q, { target, k: 100 }).filter(r => r.onTopic);
  if (!all.length) return '';
  const rung = lv => { const r = all.filter(x => x.level === lv).sort((a, b) => b.relevance - a.relevance)[0];
    return `<div class="rung ${lv}"><span class="badge ${lv}">${LEVEL_NAMES[lv]}</span>${r ? `<a href="${esc(r.url)}" target="_blank" rel="noopener" data-read="${esc(r.id)}">${esc(r.title)}</a><small>${cefr(r.difficulty)} · ${tr('words', { n: r.words })}</small>` : `<small>${tr('ladder_none')}</small>`}</div>`; };
  return `<li class="ladder-strip"><h2>${tr('ladder_h')}</h2><div class="rungs">${['beginner', 'intermediate', 'advanced'].map(rung).join('')}</div></li>`;
}

// ---- Recommendations
// Topics ranked by how many articles sit near the learner's target (and not yet read), shown as chips.
async function renderTopics() {
  const box = $('topics'); if (!box) return;
  let idx; try { idx = await loadIndex($('lang').value); } catch (e) { return; }
  const target = targetFor(idx, $('lang').value), stat = {};
  idx.docs.forEach(d => { const t = d[7]; if (!t) return; const s = stat[t] || (stat[t] = { n: 0, near: 0, read: 0 });
    s.n++; if (Math.abs(d[4] - target) <= 0.15) s.near++; if (prof.read.includes(d[0])) s.read++; });
  const label = t => (idx.topics && idx.topics[t]) || t;
  const ranked = Object.entries(stat).filter(([, s]) => s.n >= 3)
    .map(([t, s]) => [t, s.near + 0.05 * s.n - 0.5 * s.read]).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
  const showAll = box.dataset.all === '1', list = showAll ? ranked.slice().sort((a, b) => label(a[0]).localeCompare(label(b[0]))) : ranked.slice(0, 14);
  box.innerHTML = list.map(([t]) => `<button type="button" class="topic" data-topic="${esc(label(t))}">${esc(label(t))}</button>`).join('') +
    `<button type="button" class="topic more-topics" data-all="1">${showAll ? tr('fewer_topics') : tr('all_topics', { n: ranked.length })}</button>`;
}

function readNext(idx, id, box) {
  const d = idx.docs.find(x => x[0] === id); if (!d) return;
  const pool = idx.docs.filter(x => x[7] === d[7] && x[0] !== id && !prof.read.includes(x[0]));
  const up = pool.filter(x => x[4] > d[4]).sort((a, b) => a[4] - b[4]);
  const n = up[0] || pool.sort((a, b) => Math.abs(a[4] - d[4]) - Math.abs(b[4] - d[4]))[0];
  box.hidden = false;
  box.innerHTML = n ? `${tr('next_up')} <a href="${esc(n[2])}" target="_blank" rel="noopener" data-read="${esc(n[0])}">${esc(n[1])}</a> <span class="badge ${esc(n[5])}">${esc(lvBadge(n[5]))}</span> <span class="badge">${cefr(n[4])}</span>${up[0] ? '' : ` <small>${tr('nothing_harder')}</small>`}`
    : tr('all_read');
}

// Feedback nudges the personal target (as a difficulty quantile) and switches to it.
async function feedback(kind) {
  const lang = $('lang').value, idx = await loadIndex(lang);
  const p = prof.place[lang] || { q: quantileOf(idx, targetFor(idx, lang)), cefr: '', level: 'intermediate', source: 'feedback' };
  p.q = Math.min(0.97, Math.max(0.03, p.q + (kind === 'too_easy' ? 0.07 : -0.07)));
  const t = LLPlace.quantileToTarget(idx, p.q); p.cefr = cefr(t, lang); p.level = t < 0.35 ? 'beginner' : t < 0.65 ? 'intermediate' : 'advanced';
  prof.place[lang] = p; save(); showChip(); $('level').value = 'custom'; prof.level = 'custom'; save();
  $('status').textContent = tr(kind === 'too_easy' ? 'fb_up' : 'fb_down');
  run(); renderTopics();
}

// ---- Placement test
const T = {};
async function startTest() {
  const lang = $('lang').value, idx = await loadIndex(lang);
  Object.assign(T, { lang, idx, seed: Date.now() % 100000, step: 0 });
  T.items = LLPlace.vocabItems(idx, T.seed, lang); T.ans = T.items.map(() => false);
  T.st = new LLPlace.Staircase(); T.used = new Set(); T.r = LLPlace.rng(T.seed + 1);
  const dlg = $('test'); if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
  testIntro();
}
const prog = f => { $('test-progress').style.width = Math.round(f * 100) + '%'; };
function testIntro() {
  prog(0);
  $('test-body').innerHTML = `<h3>${esc(tr('t_intro_h', { lang: langName(T.lang) }))}</h3>
    <p class="muted">${esc(tr('t_intro_p'))}</p>
    <div class="row-end"><button class="primary" id="t-go">${tr('t_start')}</button></div>`;
  $('t-go').onclick = testVocab;
}
function testVocab() {
  prog(0.05);
  $('test-body').innerHTML = `<h3>${tr('t_vocab_h')}</h3><p class="muted">${tr('t_vocab_p')}</p>
    <div class="words">${T.items.map((it, i) => `<button type="button" class="word" aria-pressed="false" data-i="${i}">${esc(it.word)}</button>`).join('')}</div>
    <div class="row-end"><button class="primary" id="t-next">${tr('t_continue')}</button></div>`;
  $('test-body').querySelectorAll('.word').forEach(b => b.onclick = () => { const i = +b.dataset.i; T.ans[i] = !T.ans[i]; b.setAttribute('aria-pressed', String(T.ans[i])); });
  $('t-next').onclick = () => { T.vocab = LLPlace.scoreVocab(T.items, T.ans); testCloze(); };
}
function testCloze() {
  if (T.st.done()) return testResult();
  prog(0.15 + 0.75 * T.st.history.length / T.st.n);
  const c = LLPlace.clozeItem(T.idx, T.st.q, T.r, T.used);
  if (!c) return testResult();
  $('test-body').innerHTML = `<h3>${tr('t_cloze_h')} <small class="muted">· ${tr('t_of', { i: T.st.history.length + 1, n: T.st.n })}</small></h3>
    <p class="passage">${esc(c.text).replace('_____', '<span class="blank">&nbsp;</span>')}</p>
    <div class="opts">${c.options.map(o => `<button type="button" class="opt" data-o="${esc(o)}">${esc(o)}</button>`).join('')}</div>
    <button type="button" class="skip" id="t-skip">${tr('t_skip')}</button>`;
  const answer = o => {
    const ok = o === c.answer;
    $('test-body').querySelectorAll('.opt').forEach(b => { b.disabled = true; if (b.dataset.o === c.answer) b.classList.add('right'); else if (b.dataset.o === o) b.classList.add('wrong'); });
    T.st.record(ok); setTimeout(testCloze, 450);
  };
  $('test-body').querySelectorAll('.opt').forEach(b => b.onclick = () => answer(b.dataset.o));
  $('t-skip').onclick = () => answer(null);
}
function testResult() {
  prog(1);
  const r = LLPlace.combine(T.idx, T.vocab, T.st.estimate()), band = cefr(r.target, T.lang);
  prof.place[T.lang] = { q: r.quantile, cefr: band, level: r.level, vocab: +T.vocab.toFixed(2), cloze: +T.st.estimate().toFixed(2), source: 'test' };
  save();
  const bands = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
  $('test-body').innerHTML = `<div class="result"><p class="muted">${esc(tr('t_res_lead', { lang: langName(T.lang) }))}</p>
    <div class="big">${band}</div><div class="ladder">${bands.map(b => `<span class="${b === band ? 'on' : ''}">${b}</span>`).join('')}</div>
    <p class="muted">${esc(tr('t_res_detail', { level: LEVEL_NAMES[r.level], vocab: pct(T.vocab), pct: pct(T.st.estimate()) }))}</p>
    <div class="row-end"><button class="primary" id="t-done">${tr('t_done')}</button></div></div>`;
  $('t-done').onclick = () => { $('test').close ? $('test').close() : $('test').removeAttribute('open'); showChip(); $('level').value = 'custom'; prof.level = 'custom'; save(); renderTopics(); run(); };
}

// ---- Wiring
$('f').addEventListener('submit', e => { e.preventDefault(); run(); });
$('reader').addEventListener('change', () => document.body.classList.toggle('reader', $('reader').checked));
for (const id of ['lang', 'level', 'plain', 'cmp']) $(id).addEventListener('change', () => { if (id === 'lang') { showChip(); renderMyWords(); } if (id === 'lang' || id === 'level') renderTopics(); $('q').value.trim() && run(); });
if ($('take-test')) $('take-test').addEventListener('click', startTest);
document.addEventListener('click', async e => {
  const t = e.target; if (!t || !t.closest) return;
  const read = t.closest('[data-read]'); if (read) { const id = read.dataset.read; if (!prof.read.includes(id)) { prof.read.push(id); prof.read = prof.read.slice(-500); save(); } }
  const topic = t.closest('[data-topic]'); if (topic) { $('q').value = topic.dataset.topic; run(); window.scrollTo && window.scrollTo({ top: 0, behavior: 'smooth' }); }
  const all = t.closest('.more-topics'); if (all) { const b = $('topics'); b.dataset.all = b.dataset.all === '1' ? '0' : '1'; renderTopics(); }
  const nx = t.closest('[data-next]'); if (nx) readNext(await loadIndex($('lang').value), nx.dataset.next, nx.closest('li').querySelector('.next'));
  const fb = t.closest('[data-fb]'); if (fb) feedback(fb.dataset.fb);
  const wd = t.closest('.w'); if (wd) openWord(wd);
  const mk = t.closest('[data-markword]'); if (mk) setWord(mk.dataset.markword, mk.dataset.mark === '1');
  if (t.closest('#mywords-clear')) { prof.words[$('lang').value] = []; save(); renderMyWords(); $('q').value.trim() && run(); }
});
// Interface language (independent of the search language): saved choice, else the browser's language
function setUI(l, rerun) {
  LLI18n.set(l); $('ui').value = LLI18n.get(); LLI18n.apply(document); showChip(); renderTopics(); renderMyWords();
  const opt = document.getElementById('custom-opt'); if (opt && opt.hidden) opt.textContent = tr('lv_custom_plain');
  if (rerun && $('q').value.trim()) run();
}
$('ui').addEventListener('change', () => { prof.ui = $('ui').value; save(); setUI($('ui').value, true); });
// Remember profile choices and support shareable ?q= links
(function () {
  try {
    const up = new URLSearchParams(location.search).get('ui');
    LLI18n.set(up || prof.ui || LLI18n.detect(typeof navigator !== 'undefined' ? navigator.language : 'en')); $('ui').value = LLI18n.get(); LLI18n.apply(document);
    const p = new URLSearchParams(location.search);
    for (const id of ['lang', 'level']) { const v = p.get(id) || prof[id]; if (v && [...$(id).options].some(o => o.value === v)) $(id).value = v; }
    showChip();
    for (const id of ['lang', 'level']) $(id).addEventListener('change', () => { prof[id] = $(id).value; save(); });
    $('f').addEventListener('submit', () => { const u = new URL(location); u.searchParams.set('q', $('q').value.trim()); history.replaceState(null, '', u); });
    renderTopics(); renderMyWords();
    if (p.get('q')) { $('q').value = p.get('q'); run(); }
  } catch (e) {}
})();
// Keyboard shortcut: "/" focuses the search box; Escape clears it
document.addEventListener('keydown', e => {
  const t = e.target.tagName;
  if (e.key === '/' && t !== 'INPUT' && t !== 'SELECT') { e.preventDefault(); $('q').focus(); $('q').select(); }
  else if (e.key === 'Escape' && e.target === $('q')) { $('q').value = ''; }
  else if ((e.key === 'Enter' || e.key === ' ') && e.target.classList && e.target.classList.contains('w')) { e.preventDefault(); openWord(e.target); }
});
