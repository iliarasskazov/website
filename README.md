# iliarasskazov.com

Personal site for Ilia L. Rasskazov. Static HTML, no framework, no build toolchain
beyond Python and PyYAML. Served by GitHub Pages from `docs/`.

## Why it is built this way

The previous site carried three different publication counts across two pages,
because the list was maintained by hand. Here the content lives in data files and
the pages are generated, so a number can only be wrong in one place.

| Path | What it is |
|---|---|
| `data/site.yml` | Bio, links, metrics, experience, education, software. |
| `data/publications.yml` | Full publication list. One entry per paper. |
| `data/dois.json` | DOIs resolved from Crossref. Generated — do not hand-edit. |
| `assets/style.css` | All the design. Hand-written, ~190 lines. |
| `build.py` | Structure. Reads `data/`, writes `docs/`. |
| `docs/` | Build output. **This is what GitHub Pages serves.** |

## Build

```sh
pip3 install pyyaml     # once
python3 build.py        # writes docs/
open docs/index.html    # preview locally
```

## Resolve DOIs

Publication titles link to their DOI when one is known. To fill them in:

```sh
python3 bin/fetch-dois.py
python3 build.py
```

It queries Crossref by title and only accepts matches above 0.90 similarity, so a
wrong DOI is unlikely — but check `data/dois.json` for any low `score` values.
Entries with an `arxiv:` field link straight to arXiv and are skipped.

## Publishing

1. Push to GitHub.
2. Settings → Pages → Source: *Deploy from a branch*, branch `main`, folder `/docs`.
3. Point `iliarasskazov.com` at GitHub Pages by adding these DNS records at your
   registrar (this replaces the Wix records):

   | Type | Name | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | `<username>.github.io` |

   `docs/CNAME` already contains the domain. Enable *Enforce HTTPS* once the
   certificate is issued (usually within an hour).

Keep the Wix site up until Pages is serving correctly, then cancel it.

## To do

- [ ] Resolve DOIs (`bin/fetch-dois.py`) — 45 of 47 entries currently unlinked
- [ ] Reconcile 47 entries here against 49 on Google Scholar; two are unaccounted for
- [ ] Set `repo_url` in `data/site.yml` once this repo exists (footer link is hidden until then)
- [ ] Add a photo if wanted — the design currently carries none by choice
