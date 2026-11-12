"""Build one self-contained HTML file (web/dist/lingualadder.html) with the
chosen languages embedded, for hosts that allow only a single file.
Usage: python -m lingualadder.build_single [lang ...]   (default: en es)"""
import json, os, sys
W = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'web')
def build(langs):
    rd = lambda f: open(os.path.join(W, f), encoding='utf-8').read()
    html = rd('index.html')
    emb = {l: json.load(open(os.path.join(W, 'data', l + '.json'), encoding='utf-8')) for l in langs}
    data = 'window.LL_EMBEDDED=' + json.dumps(emb, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ';'
    html = html.replace('<link rel="stylesheet" href="style.css">', '<style>' + rd('style.css') + '</style>')
    html = html.replace('<script src="ll.js"></script>', '<script>' + data + '</script><script>' + rd('ll.js') + '</script>')
    html = html.replace('<script src="app.js"></script>', '<script>' + rd('app.js') + '</script>')
    os.makedirs(os.path.join(W, 'dist'), exist_ok=True)
    out = os.path.join(W, 'dist', 'lingualadder.html')
    open(out, 'w', encoding='utf-8').write(html)
    return out, len(html)
if __name__ == '__main__':
    print(build(sys.argv[1:] or ['en', 'es']))
