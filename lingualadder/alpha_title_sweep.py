"""Alpha x sigma sweep with the exact-title bonus on (en and es, mean of the three levels).

python -m lingualadder.alpha_title_sweep   -> data/alpha_title_sweep.json
"""
import json
import numpy as np
from lingualadder.search import LinguaLadder
from lingualadder.evaluate import retrieval_eval
e=LinguaLadder(); out=[]
for a in (0.4,0.5,0.6,0.7):
  for s in (0.10,0.15):
    r=retrieval_eval(e,alpha=a,sigma=s)
    row={"alpha":a,"sigma":s}
    for lang in("en","es"):
        row[lang]={k:round(float(np.mean([r[lang][l][k] for l in r[lang] if l!='queries'])),3) for k in("lingualadder_p10","lingualadder_ndcg10","lingualadder_level_match")}
    out.append(row); print(json.dumps(row),flush=True)
json.dump(out,open('data/alpha_title_sweep.json','w'),indent=1)
