function sentenceOf(sel) {
  const node = sel.anchorNode; if (!node) return '';
  const full = (node.textContent || ''); const off = sel.anchorOffset;
  const parts = full.split(/(?<=[.!?\u0964\u3002\uff01\uff1f])\s*/); let pos = 0;
  for (const p of parts) { if (off <= pos + p.length) return p.slice(0, 400); pos += p.length + 1; }
  return full.slice(0, 400);
}
const art = document.getElementById('article'), pop = document.getElementById('pop');
art.addEventListener('mouseup', async (e) => {
  const sel = window.getSelection(); const text = sel.toString().trim();
  if (!text || text.length > 400) { pop.hidden = true; return; }
  const rect = sel.getRangeAt(0).getBoundingClientRect();
  pop.style.top = (window.scrollY + rect.bottom + 6) + 'px'; pop.style.left = (window.scrollX + rect.left) + 'px';
  pop.textContent = 'Translating…'; pop.hidden = false;
  const r = await fetch('/api/translate', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text, context: sentenceOf(sel), doc_id: art.dataset.doc})});
  const j = await r.json();
  pop.innerHTML = ''; const b = document.createElement('b'); b.textContent = text; pop.append(b, document.createElement('br'), j.text || 'Translation unavailable');
  if (j.context_translation) { const s = document.createElement('div'); s.className = 'ctx'; s.textContent = 'In this sentence: ' + j.context_translation; pop.append(s); }
  if (j.text && text.split(/\s+/).length <= 6) { const li = document.createElement('li'); li.innerHTML = '<b></b> '; li.firstChild.textContent = text.toLowerCase(); li.append(j.text); document.getElementById('vocab').prepend(li); }
});
document.addEventListener('mousedown', (e) => { if (!pop.contains(e.target)) pop.hidden = true; });
document.querySelectorAll('.feedback button').forEach(btn => btn.onclick = async () => {
  const r = await fetch('/api/feedback', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({verdict: btn.dataset.v, doc_id: art.dataset.doc, difficulty: parseFloat(art.dataset.diff)})});
  const j = await r.json();
  document.getElementById('fbmsg').textContent = ` Thanks! Your target difficulty is now ${j.target}.`;
});
