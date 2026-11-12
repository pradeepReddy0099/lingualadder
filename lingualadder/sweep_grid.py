# Grid sweep of ALPHA x SIGMA; run: python -m lingualadder.sweep_grid
from lingualadder.search import LinguaLadder
from lingualadder.evaluate import retrieval_eval, summarize
e=LinguaLadder()
for a in (0.5,0.6,0.7):
  for s in (0.1,0.15,0.25,0.35):
    r=summarize(retrieval_eval(e,alpha=a,sigma=s));n=r["lingualadder_ndcg10"];l=r["lingualadder_level_match"]
    print(a,s,r["lingualadder_p10"],n,l,round(2*n*l/(n+l),3),flush=True)
