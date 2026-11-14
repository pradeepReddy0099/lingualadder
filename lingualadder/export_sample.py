"""Build a small topic-balanced SAMPLE of the web index and a single-file page from it, for hosts that
accept only one small HTML file (the Hark Page). Per language and topic it keeps up to 2 beginner,
1 intermediate and 1 advanced article (deterministic), re-numbers postings, keeps the full-corpus idf.
Usage: python -m lingualadder.export_sample [lang ...]  -> web/dist/lingualadder_sample.html"""
import hashlib, json, os, sys
from collections import defaultdict
from lingualadder import build_single
W = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'web')
QUOTA = {'beginner': 2, 'intermediate': 1, 'advanced': 1}


def load_full(lang):
    d = json.load(open(os.path.join(W, 'data', lang + '.json'), encoding='utf-8'))
    for i in range(2, (d.get('parts') or 0) + 2):
        d['terms'].update(json.load(open(os.path.join(W, 'data', f'{lang}.p{i}.json'), encoding='utf-8')))
    return d


def sample(d):
    by = defaultdict(list)
    for i, doc in enumerate(d['docs']):
        by[(doc[7], doc[5])].append(i)
    keep = []
    for (topic, lv), ids in by.items():
        ids.sort(key=lambda i: hashlib.md5(d['docs'][i][0].encode()).hexdigest())
        keep += ids[:QUOTA.get(lv, 0)]
    keep = sorted(set(keep))
    new = {old: n for n, old in enumerate(keep)}
    terms = {}
    for t, flat in d['terms'].items():
        out, prev, cur = [flat[0]], 0, 0
        for j in range(1, len(flat), 2):
            cur += flat[j]
            if cur in new:
                out += [new[cur] - prev, flat[j + 1]]
                prev = new[cur]
        if len(out) > 1:
            terms[t] = out
    dl = [d['dl'][i] for i in keep]
    o = {k: v for k, v in d.items() if k not in ('docs', 'dl', 'terms', 'parts')}
    o.update(docs=[d['docs'][i] for i in keep], dl=dl, terms=terms, n=len(keep), avgdl=round(sum(dl) / len(dl), 3), sample=True)
    return o


def main(langs):
    emb = {l: sample(load_full(l)) for l in langs}
    for l, o in emb.items():
        print(l, o['n'], 'docs,', len(o['terms']), 'terms')
    rd = lambda f: open(os.path.join(W, f), encoding='utf-8').read()
    html = rd('index.html')
    data = 'window.LL_EMBEDDED=' + json.dumps(emb, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ';'
    html = html.replace('<link rel="stylesheet" href="style.css">', '<style>' + rd('style.css') + '</style>')
    html = html.replace('<script src="i18n.js"></script>', '<script>' + rd('i18n.js') + '</script>')
    html = html.replace('<script src="ll.js"></script>', '<script>' + data + '</script><script>' + rd('ll.js') + '</script>')
    html = html.replace('<script src="placement.js"></script>', '<script>' + rd('placement.js') + '</script>')
    html = html.replace('<script src="app.js"></script>', '<script>' + rd('app.js') + '</script>')
    out = os.path.join(W, 'dist', 'lingualadder_sample.html')
    open(out, 'w', encoding='utf-8').write(html)
    print(out, round(len(html.encode()) / 1e6, 2), 'MB')


if __name__ == '__main__':
    main(sys.argv[1:] or ['en', 'es'])
