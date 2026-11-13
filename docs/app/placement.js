// LinguaLadder placement test: estimates a learner's reading level from performance, not self-report.
// Part 1 (vocabulary): yes/no checklist of real words from six corpus-frequency bands plus invented
//   pseudowords; the hit rate is corrected for guessing with the false-alarm rate (Meara-style).
// Part 2 (reading): adaptive cloze. Each item is the opening of a real article from the index at a
//   given difficulty quantile with one content word blanked and four options; a staircase moves the
//   quantile up after a correct answer and down after a wrong one, with a shrinking step.
// The two parts combine into a difficulty quantile, turned into a per-language target difficulty.
// Works in browsers (window.LLPlace) and Node (module.exports).
(function (root) {
  const VOWELS = { en: 'aeiou', es: 'aeiou' };

  function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
  const pick = (a, r) => a[Math.floor(r() * a.length)];
  function shuffle(a, r) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }

  // Lowercase content words that occur in the article leads, ranked by document frequency.
  function wordList(idx) {
    if (idx._words) return idx._words;
    const stop = new Set(idx.stop || []), seen = new Set();
    for (const d of idx.docs) for (const w of (d[3] || '').match(/\p{Ll}{4,}/gu) || []) if (!stop.has(w)) seen.add(w);
    const ws = [...seen].filter(w => idx.terms[w]).map(w => ({ w, df: (idx.terms[w].length - 1) / 2 }))
      .filter(x => x.df >= 2).sort((a, b) => b.df - a.df || (a.w < b.w ? -1 : 1));
    ws.forEach((x, i) => { x.rank = i / Math.max(ws.length - 1, 1); });
    idx._words = ws; idx._wordRank = new Map(ws.map(x => [x.w, x]));
    return ws;
  }

  function pseudoword(idx, words, r, lang) {
    const v = VOWELS[lang] || 'aeiou', all = idx._wordRank;
    for (let k = 0; k < 200; k++) {
      const base = pick(words, r).w;
      if (base.length < 5 || !/^[a-zñ]+$/.test(base)) continue;
      const ch = base.split('');
      const vi = ch.map((c, i) => v.includes(c) ? i : -1).filter(i => i > 0);
      if (vi.length < 2) continue;
      const i = pick(vi, r); ch[i] = pick(v.replace(ch[i], '').split(''), r);
      if (r() < 0.5) { const j = 1 + Math.floor(r() * (ch.length - 2)); if (!v.includes(ch[j]) && !v.includes(ch[j + 1])) [ch[j], ch[j + 1]] = [ch[j + 1], ch[j]]; }
      const w = ch.join('');
      if (!idx.terms[w] && !all.has(w)) return w;
    }
    return null;
  }

  // 18 real words (3 from each of 6 frequency bands) + 6 pseudowords, shuffled.
  function vocabItems(idx, seed, lang) {
    const r = rng(seed), ws = wordList(idx).filter(x => x.w.length >= 4), items = [];
    for (let b = 0; b < 6; b++) {
      const band = ws.filter(x => x.rank >= b / 6 && x.rank < (b + 1) / 6 + (b === 5 ? 1e-9 : 0));
      for (const x of shuffle(band, r).slice(0, 3)) items.push({ word: x.w, real: true, band: b });
    }
    const mid = ws.filter(x => x.rank > 0.2 && x.rank < 0.8);
    for (let k = 0; k < 6; k++) { const p = pseudoword(idx, mid, r, lang); if (p) items.push({ word: p, real: false, band: -1 }); }
    return shuffle(items, r);
  }

  // answers: array of booleans ("I know this word") aligned with items. Returns 0..1.
  function scoreVocab(items, answers) {
    let h = 0, nr = 0, f = 0, np = 0;
    items.forEach((it, i) => { if (it.real) { nr++; if (answers[i]) h++; } else { np++; if (answers[i]) f++; } });
    const H = nr ? h / nr : 0, F = np ? f / np : 0;
    if (F >= 1) return 0;
    return Math.max(0, Math.min(1, (H - F) / (1 - F)));
  }

  function sortedDifficulty(idx) {
    if (!idx._sd) idx._sd = idx.docs.map(d => d[4]).sort((a, b) => a - b);
    return idx._sd;
  }
  const quantileToTarget = (idx, q) => { const s = sortedDifficulty(idx); return s[Math.min(s.length - 1, Math.max(0, Math.round(q * (s.length - 1))))]; };

  // One cloze item from an article near difficulty quantile q.
  function clozeItem(idx, q, r, used) {
    wordList(idx);
    const order = idx.docs.map((d, i) => i).sort((a, b) => idx.docs[a][4] - idx.docs[b][4]);
    const center = Math.round(q * (order.length - 1));
    for (let spread = 15; spread < order.length; spread *= 2) {
      const lo = Math.max(0, center - spread), hi = Math.min(order.length, center + spread);
      for (const di of shuffle(order.slice(lo, hi), r)) {
        if (used.has(di)) continue;
        const d = idx.docs[di];
        let text = (d[3] || '').replace(/…$/, '');
        const sents = text.match(/[^.!?]+[.!?]/g) || [];
        text = sents.slice(0, 2).join(' ').trim();
        if (text.length < 70 || text.length > 320) continue;
        const toks = text.match(/\p{Ll}{5,}/gu) || [];
        const cands = toks.map(w => idx._wordRank.get(w)).filter(x => x && x.rank > 0.08 && x.rank < 0.9 && !d[1].toLowerCase().includes(x.w));
        if (!cands.length) continue;
        const ans = pick(cands, r);
        const pool = idx._words.filter(x => x.w !== ans.w && Math.abs(x.rank - ans.rank) < 0.15 && Math.abs(x.w.length - ans.w.length) <= 2 && !toks.includes(x.w));
        const same = pool.filter(x => x.w.slice(-2) === ans.w.slice(-2));
        const ds = shuffle(same.length >= 3 ? same : pool, r).slice(0, 3).map(x => x.w);
        if (ds.length < 3) continue;
        used.add(di);
        const re = new RegExp('(^|[^\\p{L}])' + ans.w + '(?![\\p{L}])', 'u');
        return { doc: di, title: d[1], difficulty: d[4], q, text: text.replace(re, '$1_____'), answer: ans.w, options: shuffle([ans.w, ...ds], r) };
      }
    }
    return null;
  }

  // Adaptive staircase over difficulty quantiles.
  function Staircase(n = 8) { this.q = 0.5; this.step = 0.25; this.n = n; this.history = []; }
  Staircase.prototype.record = function (correct) {
    this.history.push({ q: this.q, correct });
    this.q = Math.min(0.97, Math.max(0.03, this.q + (correct ? this.step : -this.step)));
    this.step = Math.max(0.06, this.step * 0.6);
  };
  Staircase.prototype.done = function () { return this.history.length >= this.n; };
  // Estimate: mean of the last few quantiles visited, which is where the staircase settles.
  Staircase.prototype.estimate = function () {
    const qs = this.history.map(h => h.q).concat([this.q]).slice(-4);
    return qs.reduce((a, b) => a + b, 0) / qs.length;
  };

  function combine(idx, vocabScore, clozeQ) {
    const q = Math.min(0.97, Math.max(0.03, 0.6 * clozeQ + 0.4 * vocabScore));
    const target = quantileToTarget(idx, q);
    const level = target < 0.35 ? 'beginner' : target < 0.65 ? 'intermediate' : 'advanced';
    return { quantile: q, target, level };
  }

  const api = { rng, vocabItems, scoreVocab, clozeItem, Staircase, combine, quantileToTarget, wordList };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.LLPlace = api;
})(typeof self !== 'undefined' ? self : this);
