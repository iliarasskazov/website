#!/usr/bin/env python3
"""Refresh publication metrics in data/site.yml from a live source.

    python3 bin/update-metrics.py --find      # look up the OpenAlex author id, once
    python3 bin/update-metrics.py --dry-run   # show what would change, write nothing
    python3 bin/update-metrics.py             # update site.yml if the numbers moved

WHY NOT GOOGLE SCHOLAR
Scholar has no API and blocks automated access, especially from datacenter IPs like
GitHub Actions runners. Anything built on scraping it will work for a while and then
quietly start failing. OpenAlex is free, keyless, and explicitly built for this.

THE TRADE-OFF, STATED PLAINLY
OpenAlex indexes a narrower corpus than Scholar, so its citation count and h-index are
usually LOWER. Run --dry-run first and look at the delta. If you would rather show the
higher Scholar figures, do not enable the workflow -- update site.yml by hand a few
times a year instead. What this script will not do is print Scholar's numbers while
sourcing them from somewhere else.

Set `openalex_id` in data/site.yml to enable. Without it the script is a no-op.
"""
import argparse, datetime, io, json, os, re, sys, urllib.parse, urllib.request

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE   = os.path.join(ROOT, "data", "site.yml")
MAILTO = "il.rasskazov@gmail.com"

def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"iliarasskazov.com (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def find(name):
    q = urllib.parse.urlencode({"search": name, "mailto": MAILTO})
    for a in api(f"https://api.openalex.org/authors?{q}")["results"][:8]:
        st = a.get("summary_stats") or {}
        inst = (a.get("last_known_institutions") or [{}])
        inst = inst[0].get("display_name") if inst else None
        print(f"  {a['id']}")
        print(f"    {a['display_name']}  —  {a['works_count']} works, "
              f"{a['cited_by_count']} citations, h={st.get('h_index')}, i10={st.get('i10_index')}")
        print(f"    {inst or '(no institution)'}\n")
    print("Copy the id into data/site.yml as:  openalex_id: \"A5012345678\"")

def read_site():
    return io.open(SITE, encoding="utf-8").read()

def current(text, label):
    m = re.search(rf'\{{value:\s*"([^"]*)",\s*label:\s*{re.escape(label)}\b', text)
    return m.group(1) if m else None

def set_value(text, label, value):
    return re.sub(rf'(\{{value:\s*)"[^"]*"(,\s*label:\s*{re.escape(label)}\b)',
                  lambda m: f'{m.group(1)}"{value}"{m.group(2)}', text, count=1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--find", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    text = read_site()
    if a.find:
        return find("Ilia Rasskazov")

    m = re.search(r'^openalex_id:\s*"?([A-Za-z0-9]+)"?', text, re.M)
    if not m:
        print("openalex_id not set in data/site.yml — nothing to do.")
        print("Run:  python3 bin/update-metrics.py --find")
        return 0

    author = api(f"https://api.openalex.org/authors/{m.group(1)}?mailto={MAILTO}")
    st = author.get("summary_stats") or {}
    fetched = {
        "publications": f"{author['works_count']}",
        "citations":    f"{author['cited_by_count']:,}",
        "h-index":      f"{st.get('h_index')}",
    }

    print(f"OpenAlex: {author['display_name']}  ({author['id']})\n")
    changed = False
    for label, new in fetched.items():
        old = current(text, label)
        flag = "" if old == new else "   <-- changes"
        print(f"  {label:14} site.yml: {old:>7}   OpenAlex: {new:>7}{flag}")
        if old != new:
            changed = True

    if not changed:
        print("\nno change")
        return 0
    if a.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    for label, new in fetched.items():
        text = set_value(text, label, new)
    today = datetime.date.today().isoformat()
    text = re.sub(r'^(\s*label:\s*).*$', r'\1OpenAlex', text, count=1, flags=re.M) \
        if "metrics_source" in text else text
    text = re.sub(r'^(\s*)url:\s*"[^"]*"', r'\1url: "https://openalex.org/' + m.group(1) + '"',
                  text, count=1, flags=re.M)
    text = re.sub(r'^(\s*updated:\s*).*$', rf'\g<1>"{today}"', text, count=1, flags=re.M)
    io.open(SITE, "w", encoding="utf-8").write(text)
    print(f"\nwrote data/site.yml (source relabelled to OpenAlex, updated {today})")
    print("Now run: python3 build.py")
    return 0

if __name__ == "__main__":
    sys.exit(main())
