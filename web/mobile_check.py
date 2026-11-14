"""Mobile-width browser check of the static web version (needs playwright + chromium).
Serves web/ locally, searches in en and es at 320/390/768 px, and fails on horizontal overflow,
JS errors, or tap targets under 40 px (buttons, selects, links; checkboxes and in-text words excluded).
Run: python web/mobile_check.py"""
import os, subprocess, sys, time, json
from playwright.sync_api import sync_playwright
root = os.path.dirname(os.path.abspath(__file__)); port = 8766
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port)], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1); fails = []
JS = """()=>{const bad=[];document.querySelectorAll('a,button,select,.topic').forEach(e=>{const r=e.getBoundingClientRect();
 if(r.width>0&&r.height>0&&r.height<40&&!e.closest('.snip'))bad.push(e.tagName+' '+(e.textContent||'').trim().slice(0,20)+' '+Math.round(r.height))});
 let over=0;document.querySelectorAll('body *').forEach(e=>{const r=e.getBoundingClientRect();if(r.width>0&&r.right>innerWidth+1)over++});
 return {sw:document.documentElement.scrollWidth,iw:innerWidth,bad,over,n:document.querySelectorAll('#results > li').length}}"""
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        for lang, q in (('en', 'volcano'), ('es', 'volcán')):
            for w in (320, 390):
                ctx = b.new_context(viewport={'width': w, 'height': 800}, is_mobile=True, has_touch=True)
                pg = ctx.new_page(); errs = []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.goto(f'http://localhost:{port}/index.html'); pg.wait_for_timeout(1000)
                pg.select_option('#lang', lang); pg.fill('#q', q); pg.keyboard.press('Enter'); pg.wait_for_timeout(2500)
                r = pg.evaluate(JS)
                ok = r['sw'] <= r['iw'] and not errs and not r['bad'] and r['over'] == 0 and r['n'] >= 10
                print(lang, w, 'OK' if ok else 'FAIL', json.dumps(r)[:200], errs[:2])
                if not ok: fails.append((lang, w))
        b.close()
finally:
    srv.terminate()
sys.exit(1 if fails else 0)
