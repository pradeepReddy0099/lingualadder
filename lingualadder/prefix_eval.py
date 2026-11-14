"""Prefix queries: first 2 words of 3-5 word titles; is that article rank 1 / in top 3? python -m lingualadder.prefix_eval"""
import json
from .config import DATA_DIR
from .search import LinguaLadder
from . import search as S
def run(ll):
    out={}
    for lang in ("en","es"):
        docs=[d for d in ll.docs[lang] if "(" not in d["title"] and 3<=len(d["title"].split())<=5][::8][:250]
        r1=r3=0
        for d in docs:
            q=" ".join(d["title"].split()[:2]); top=ll.search(lang,q,0.5,k=10)
            t=[x["title"] for x in top]; r1+=bool(t and t[0]==d["title"]); r3+=d["title"] in t[:3]
        out[lang]={"queries":len(docs),"rank1":round(r1/len(docs),3),"top3":round(r3/len(docs),3)}
    return out
if __name__=="__main__":
    ll=LinguaLadder(); r={}
    for v in (0.0,0.25):
        S.PREFIX_MATCH=v; r[str(v)]=run(ll); print(v,r[str(v)],flush=True)
    (DATA_DIR/"prefix_eval.json").write_text(json.dumps(r,indent=1))
