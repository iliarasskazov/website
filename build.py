#!/usr/bin/env python3
"""Build iliarasskazov.com into docs/ (GitHub Pages serves from there).

    python3 build.py

Content lives in data/*.yml. Design lives in assets/style.css.
Structure lives here. Nothing else to install beyond PyYAML.
"""
import html, json, os, re, shutil, sys
import yaml

ROOT  = os.path.dirname(os.path.abspath(__file__))
DATA  = os.path.join(ROOT, "data")
OUT   = os.path.join(ROOT, "docs")
DOMAIN = "iliarasskazov.com"

def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return yaml.safe_load(f)

def e(s):
    return html.escape(str(s), quote=False)

def typo(s):
    """Escape, then apply the small typographic fixes plain-text data files can't carry."""
    s = e(s)
    s = s.replace("---", "&mdash;").replace(" -- ", " &ndash; ")
    s = re.sub(r"(?<=\d)-(?=\d)", "&ndash;", s)      # page and volume ranges
    s = re.sub(r"\s+-\s+", " &ndash; ", s)            # stray hyphen used as a dash
    s = s.replace("(x2)", "(&times;2)")
    return s

def bold_self(authors):
    """Bold every variant of his own name in an author string."""
    return re.sub(r"((?:I\.\s*L\.\s*|I\.\s*)?Rasskazov)", r"<b>\1</b>", e(authors))

def badges(p):
    return "".join(f'<span class="badge">{e(b)}</span>' for b in p.get("badges") or [])

def pub_url(p, dois):
    if p.get("arxiv"):
        return f"https://arxiv.org/abs/{p['arxiv']}"
    doi = p.get("doi") or (dois.get(p["title"]) or {}).get("doi")
    return f"https://doi.org/{doi}" if doi else None

def render_pub(p, dois):
    url = pub_url(p, dois)
    title = e(p["title"])
    t = f'<a href="{url}">{title}</a>' if url else title
    ref = f", {typo(p['ref'])}" if p.get("ref") else ""
    extra = ""
    if p.get("software"):
        extra = f' &middot; <a href="{p["software"]}">code</a>'
    return (f'<div class="pub">'
            f'<div class="t">{t}{badges(p)}</div>'
            f'<div class="a">{bold_self(p["authors"])}</div>'
            f'<div class="v">{e(p["venue"])}{ref} ({p["year"]}){extra}</div>'
            f'</div>')

def page(title, body, nav_here, desc, repo=None):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="Ilia L. Rasskazov">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="profile">
<meta property="og:url" content="https://{DOMAIN}/">
<link rel="canonical" href="https://{DOMAIN}/{'' if nav_here=='home' else 'publications.html'}">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9788;</text></svg>">
</head>
<body>
<header class="masthead"><div class="wrap">
  <a class="who" href="index.html">Ilia L. Rasskazov</a>
  <nav>
    <a href="index.html"{' aria-current="page"' if nav_here=='home' else ''}>Home</a>
    <a href="publications.html"{' aria-current="page"' if nav_here=='pubs' else ''}>Publications</a>
    <a href="https://scholar.google.com/citations?user=jCpbgOEAAAAJ">Scholar</a>
    <a href="https://multilayer.app">multilayer.app</a>
  </nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">
  Ilia L. Rasskazov &middot; <a href="mailto:il.rasskazov@gmail.com">il.rasskazov@gmail.com</a> &middot; San Jose, California<br>
  {'<span style="font-size:.82rem">Built from a data file. Source: <a href="' + repo + '">' + repo.replace("https://","") + "</a></span>" if repo else ""}
</div></footer>
</body>
</html>
"""

def build():
    s     = load("site.yml")
    pubs  = load("publications.yml")
    dpath = os.path.join(DATA, "dois.json")
    dois  = json.load(open(dpath, encoding="utf-8")) if os.path.exists(dpath) else {}

    # ---------------- home ----------------
    links = "".join(f'<a href="{l["url"]}">{e(l["label"])}</a>' for l in s["links"])
    metrics = "".join(f'<div><span class="v">{e(m["value"])}</span>'
                      f'<span class="l">{e(m["label"])}</span></div>' for m in s["metrics"])
    about = "".join(f"<p>{typo(p.strip())}</p>" for p in s["about"])
    software = "".join(
        f'<div class="card"><h3><a href="{c["url"]}">{e(c["name"])}</a></h3>'
        f'<p>{typo(c["blurb"].strip())}</p><div class="meta">{typo(c["meta"])}</div></div>'
        for c in s["software"])
    exp = "".join(
        f'<div class="row"><div><span class="what">{e(r["role"])}</span><br>'
        f'<span class="where">{e(r["org"])}{", " + e(r["loc"]) if r.get("loc") else ""}</span></div>'
        f'<span class="when">{e(r["dates"])}</span></div>' for r in s["experience"])
    edu = "".join(
        f'<div class="row"><div><span class="what">{e(r["degree"])}</span><br>'
        f'<span class="where">{e(r["org"])}</span></div>'
        f'<span class="when">{e(r["year"])}</span></div>' for r in s["education"])
    rec = "".join(f"<li>{typo(r)}</li>" for r in s["recognition"])
    selected = [p for p in pubs if p.get("badges") or p.get("software")][:6]
    sel_html = "".join(render_pub(p, dois) for p in selected)

    home = f"""<div class="hero">
  <h1>{e(s['name'])}</h1>
  <p class="role">{e(s['role_line'])}<span class="dot">&bull;</span>{e(s['tagline'])}</p>
  <p class="lede">{typo(s['lede'].strip())}</p>
  <div class="linkrow">{links}<a href="mailto:{s['email']}">Email</a></div>
</div>
<div class="metrics">{metrics}</div>
<section><h2>About</h2>{about}</section>
<section><h2>Software</h2>{software}</section>
<section><h2>Selected publications</h2>{sel_html}
  <p style="margin-top:1.1rem"><a href="publications.html">All {len(pubs)} publications &rarr;</a></p></section>
<section><h2>Experience</h2>{exp}</section>
<section><h2>Education</h2>{edu}</section>
<section><h2>Service &amp; recognition</h2>
  <p>{typo(s['service']['review'].strip())}</p>
  <p>{typo(s['service']['mentoring'].strip())}</p>
  <ul class="plain">{rec}</ul></section>"""

    # ---------------- publications ----------------
    by_year, order = {}, []
    for p in sorted(pubs, key=lambda x: -int(x["year"])):
        if p["year"] not in by_year:
            by_year[p["year"]] = []
            order.append(p["year"])
        by_year[p["year"]].append(p)
    plist = "".join(
        f'<div class="year">{y}</div>' + "".join(render_pub(p, dois) for p in by_year[y])
        for y in order)
    m = s["metrics"]
    strip = " \u00b7 ".join(f"{x['value']} {x['label']}" for x in m)
    pubs_page = f"""<div class="hero"><h1>Publications</h1>
  <p class="role">{e(strip)}</p>
  <p class="lede" style="font-size:1.05rem">Complete list, newest first. Metrics from
  <a href="https://scholar.google.com/citations?user=jCpbgOEAAAAJ">Google Scholar</a>.</p></div>
{plist}"""

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(f"{s['name']} — {s['role_line']}", home, "home", s["lede"].strip(), s.get("repo_url")))
    with open(os.path.join(OUT, "publications.html"), "w", encoding="utf-8") as f:
        f.write(page(f"Publications — {s['name']}", pubs_page, "pubs",
                     f"{len(pubs)} peer-reviewed publications by Ilia L. Rasskazov.", s.get("repo_url")))
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"), dirs_exist_ok=True)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    with open(os.path.join(OUT, "CNAME"), "w") as f:
        f.write(DOMAIN + "\n")

    unlinked = [p["title"] for p in pubs if not pub_url(p, dois)]
    print(f"built docs/  ->  {len(pubs)} publications, {len(order)} years")
    if unlinked:
        print(f"WARNING: {len(unlinked)}/{len(pubs)} publications have no DOI link.")
        print("         Run:  python3 bin/fetch-dois.py    (needs internet; ~30s)")

if __name__ == "__main__":
    build()
