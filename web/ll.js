// LinguaLadder core in plain JS: tokenizer + BM25 + level-aware reranker.
// Mirrors lingualadder/search.py and textproc.index_tokens. Works in browsers and in Node (module.exports).
(function (root) {
  const WORD = /[\p{L}\p{M}]+(?:['’-][\p{L}\p{M}]+)*/gu;
  const CJK_RUN = /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}ー]+/gu;
  const CJK_CHAR = /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Thai}ー]/u;

  function indexTokens(text, idx) {
    text = text.toLowerCase();
    if (idx.cjk) {
      const toks = [];
      for (const run of text.match(CJK_RUN) || []) {
        const ch = Array.from(run);
        if (ch.length === 1) toks.push(run);
        for (let i = 0; i < ch.length - 1; i++) toks.push(ch[i] + ch[i + 1]);
      }
      for (const w of text.match(WORD) || []) if (!CJK_CHAR.test(w)) toks.push(w);
      return toks;
    }
    const stop = idx.stopSet || (idx.stopSet = new Set(idx.stop));
    return (text.match(WORD) || []).filter(w => !stop.has(w) && Array.from(w).length > 1);
  }

  // Raw BM25 scores: Map(docIndex -> score) for the query.
  function bm25(idx, query) {
    const scores = new Map();
    const { k1, b, avgdl, dl, terms } = idx;
    for (const t of new Set(indexTokens(query, idx))) {
      const e = terms[t];
      if (!e) continue;
      const idf = e[0];
      let d = 0;
      for (let j = 1; j < e.length; j += 2) {
        d += e[j];
        const tf = e[j + 1];
        const s = idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl[d] / avgdl));
        scores.set(d, (scores.get(d) || 0) + s);
      }
    }
    return scores;
  }

  // Words a learner at this level is assumed to know: the N most frequent words of the article openings
  // (ties alphabetical, same as lingualadder/vocab.py), minus words they looked up.
  const VOCAB_SIZES = { beginner: 300, intermediate: 1500, advanced: 5000 };
  function knownWords(idx, level, unknown) {
    if (!idx._ranked) {
      const df = new Map();
      for (const d of idx.docs) for (const t of new Set(indexTokens(d[3] || '', idx))) df.set(t, (df.get(t) || 0) + 1);
      idx._ranked = Array.from(df).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0)).map(x => x[0]);
    }
    const known = new Set(idx._ranked.slice(0, VOCAB_SIZES[level] ?? VOCAB_SIZES.intermediate));
    for (const u of unknown || []) for (const t of indexTokens(u, idx)) known.delete(t);
    return known;
  }

  // opts: {target, alpha, sigma, k, rerank, minRel, candidates}
  function search(idx, query, opts) {
    const o = Object.assign({ alpha: idx.alpha, sigma: idx.sigma, k: 10, rerank: true, minRel: 0, candidates: idx.candidates, known: null, beta: null }, opts);
    const beta = o.known && o.known.size ? (o.beta ?? idx.vocab_beta ?? 0.5) : 0;
    const cands = Array.from(bm25(idx, query)).sort((a, b) => b[1] - a[1] || a[0] - b[0]).slice(0, o.candidates);
    if (!cands.length) return [];
    const top = cands[0][1] || 1;
    const tw = o.topicWeight ?? idx.topic_weight ?? 0.4, tmin = idx.on_topic_min ?? 0.5;
    const onFirst = o.onTopicFirst ?? idx.on_topic_first ?? true;
    const qterms = Array.from(new Set(indexTokens(query, idx))).filter(t => idx.terms[t]);
    const qidf = qterms.reduce((a, t) => a + idx.terms[t][0], 0) || 1;
    const out = cands.map(([i, s]) => {
      const d = idx.docs[i];
      // Topicality: query words in the title (full credit) or opening lead (half), weighted by idf.
      if (!d._tl) d._tl = [new Set(indexTokens(d[1], idx)), new Set(indexTokens(d[3] || '', idx))];
      const topical = qterms.reduce((a, t) => a + idx.terms[t][0] * (d._tl[0].has(t) ? 1 : d._tl[1].has(t) ? 0.5 : 0), 0) / qidf;
      const onTopic = topical >= tmin;
      const rel = o.rerank ? (1 - tw) * (s / top) + tw * topical : s / top;
      const diff = d[4];
      const fit = Math.exp(-((diff - o.target) ** 2) / (2 * o.sigma ** 2));
      let final = o.rerank ? o.alpha * rel + (1 - o.alpha) * fit : rel;
      if (o.rerank && beta) { const tk = indexTokens(d[3] || '', idx); if (tk.length) final += beta * (tk.filter(t => o.known.has(t)).length / tk.length - 0.5); }
      if (o.rerank && rel < o.minRel) final -= 1;
      if (o.rerank && onFirst && !onTopic) final = rel - 2;
      return { id: d[0], title: d[1], url: d[2], snippet: d[3], difficulty: d[4], level: d[5], words: d[6],
               topic: d[7], source: d[8], bm25: s, relevance: rel, fit, score: final, onTopic };
    });
    out.sort((a, b) => b.score - a.score);
    return out.slice(0, o.k);
  }

  const api = { indexTokens, bm25, search, knownWords, VOCAB_SIZES };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.LL = api;
})(typeof self !== 'undefined' ? self : this);
