#!/usr/bin/env python3
"""Resolve DOIs for data/publications.yml via the Crossref REST API.

Writes data/dois.json  ->  {title: {"doi": ..., "score": ..., "matched": ...}}
build.py merges this in, so publications.yml keeps its comments and stays hand-editable.

  python3 bin/fetch-dois.py            # all unresolved
  python3 bin/fetch-dois.py 0 15       # entries [0:15] only

Run this on your own machine -- api.crossref.org is not reachable from the
Cowork sandbox, so DOIs cannot be resolved from there. One pass takes ~30s.
"""
import json, os, re, sys, time, urllib.parse, urllib.request, difflib
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBS = os.path.join(ROOT, "data", "publications.yml")
OUT  = os.path.join(ROOT, "data", "dois.json")
MAILTO = "il.rasskazov@gmail.com"          # polite pool, per Crossref etiquette
THRESHOLD = 0.90                            # title-similarity floor to accept a match

def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()

def query(title):
    url = ("https://api.crossref.org/works?"
           + urllib.parse.urlencode({"query.bibliographic": title, "rows": 3, "mailto": MAILTO}))
    req = urllib.request.Request(url, headers={"User-Agent": f"iliarasskazov.com DOI resolver (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.load(r)["message"]["items"]

def main():
    pubs = yaml.safe_load(open(PUBS, encoding="utf-8"))
    known = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else len(pubs)

    for p in pubs[start:start + limit]:
        t = p["title"]
        if (known.get(t) or {}).get("doi") or p.get("doi") or p.get("arxiv"):
            continue   # already resolved; nulls are retried
        try:
            items = query(t)
        except Exception as e:
            print(f"  ERR  {t[:55]!r}: {e}")
            continue
        best, best_score = None, 0.0
        for it in items:
            cand = (it.get("title") or [""])[0]
            score = difflib.SequenceMatcher(None, norm(t), norm(cand)).ratio()
            if score > best_score:
                best, best_score = it, score
        if best and best_score >= THRESHOLD:
            known[t] = {"doi": best.get("DOI"), "score": round(best_score, 3),
                        "matched": (best.get("title") or [""])[0]}
            print(f"  ok   {best_score:.2f}  {best.get('DOI')}")
        else:
            known[t] = {"doi": None, "score": round(best_score, 3),
                        "matched": (best.get("title") or [""])[0] if best else None}
            print(f"  MISS {best_score:.2f}  {t[:55]!r}")
            if best and best_score >= 0.75:
                # near miss: usually means OUR title is stale, not that Crossref is wrong
                print(f"         candidate: {best.get('DOI')}")
                print(f"         titled   : {(best.get('title') or [''])[0][:70]!r}")
        time.sleep(0.25)

    json.dump(known, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
    got = sum(1 for v in known.values() if v.get("doi"))
    print(f"resolved {got}/{len(known)} attempted  ->  data/dois.json")

if __name__ == "__main__":
    main()
