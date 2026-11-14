#!/usr/bin/env python3
"""Builds the J++ website into public/.

    python3 build.py           build the site
    python3 build.py serve     build it and preview it at http://localhost:8080

Texts are in content/en.json and content/es.json, settings in site.json, and the
style, script, images and downloads in assets/. Only Python 3 is needed.
"""
import functools
import http.server
import json
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
LANGS = ["en", "es"]          # the first one is published at the top of the site
PAGES = {"home": "index.html", "privacy": "privacy.html", "support": "support.html"}

ICONS = {
    "native": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "box": '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5M12 13v8"/>',
    "data": '<ellipse cx="12" cy="5.5" rx="8" ry="3"/><path d="M4 5.5v6.5c0 1.7 3.6 3 8 3s8-1.3 8-3V5.5M4 12v6.500c0 1.700 3.600 3 8 3s8-1.300 8-3V12"/>',
    "ai": '<path d="M10 3 11.800 8.200 17 10l-5.200 1.800L10 17l-1.800-5.200L3 10l5.200-1.800z"/><path d="M18 14l.9 2.100L21 17l-2.100.9L18 20l-.9-2.100L15 17l2.100-.9z"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2.500"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "mac": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
}


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def fill(text, site):
    """Replaces the {placeholders} a text may use."""
    return (text.replace("{version}", site["version"]).replace("{size}", site["download_size"])
            .replace("{email}", site["contact_email"]).replace("{year}", site["year"]))


def download_link(site, root):
    """The address of the installer, or "" while there is nothing to download."""
    url = site.get("download_url", "")
    return url if url.startswith("http") or not url else root + url


def lang_dir(lang):
    return "" if lang == LANGS[0] else lang + "/"


def picture(root, name, alt, w, h, lazy=True, cls=""):
    """A screenshot that follows the light or dark appearance of the visitor's system."""
    loading = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    return (f'<picture><source srcset="{root}img/{name}-dark.jpg" media="(prefers-color-scheme: dark)">'
            f'<img class="shot {cls}" src="{root}img/{name}-light.jpg" alt="{escape(alt)}" width="{w}" height="{h}"{loading}></picture>')


def icon_img(root, size, cls="", alt=""):
    return (f'<picture><source srcset="{root}img/icon-dark.png" media="(prefers-color-scheme: dark)">'
            f'<img class="{cls}" src="{root}img/icon-light.png" alt="{escape(alt)}" width="{size}" height="{size}"></picture>')


def image_size(name):
    """Width and height of a screenshot, read from the JPEG file itself."""
    data = (ROOT / "assets" / "img" / f"{name}-light.jpg").read_bytes()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
        i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    return 1500, 1000


def layout(site, t, lang, page, title, description, body):
    root = "" if lang == LANGS[0] else "../"
    here = PAGES[page]
    home = "index.html" if page != "home" else ""
    other = [l for l in LANGS if l != lang][0]
    other_t = load(f"content/{other}.json")
    # the address of this same page in the other language; ?lang= records that the visitor chose it
    plain = f"{root}{lang_dir(other)}{here if page != 'home' else ''}" or "./"
    other_href = f"{plain}?lang={other}"
    names = {l: (t if l == lang else other_t)["lang_name"] for l in LANGS}
    toggle = f'<div class="lang-toggle" role="group" aria-label="{names[LANGS[0]]} / {names[LANGS[1]]}">'
    for l in LANGS:
        if l == lang:
            toggle += f'<span class="on" aria-current="true" title="{names[l]}">{l.upper()}</span>'
        else:
            toggle += f'<a href="{other_href}" lang="{l}" hreflang="{l}" title="{names[l]}" aria-label="{names[l]}">{l.upper()}</a>'
    toggle += "</div>"
    # runs before the page is drawn: a first visit opens in the language of the visitor's system, and later
    # visits in the language chosen with the switch
    detect = ("<script>(function(){try{var here='%s',store=null,q=/[?&]lang=(%s)/.exec(location.search);"
              "try{store=localStorage.getItem('jpp-lang')}catch(e){}"
              "if(q){try{localStorage.setItem('jpp-lang',q[1])}catch(e){}"
              "history.replaceState(null,'',location.pathname+location.hash);return}"
              "var sys=((navigator.languages&&navigator.languages[0])||navigator.language||'').toLowerCase().slice(0,2);"
              "var want=store||(sys==='%s'?sys:'%s');"
              "if(want!==here)location.replace('%s'+location.hash)}catch(e){}})();</script>"
              % (lang, "|".join(LANGS), LANGS[1], LANGS[0], plain))
    base = site.get("base_url", "").rstrip("/")
    seo = ""
    if base:
        seo += f'<link rel="canonical" href="{base}/{lang_dir(lang)}{here if page != "home" else ""}">\n'
        for l in LANGS:
            seo += f'<link rel="alternate" hreflang="{l}" href="{base}/{lang_dir(l)}{here if page != "home" else ""}">\n'
        seo += f'<link rel="alternate" hreflang="x-default" href="{base}/{here if page != "home" else ""}">\n'
        seo += f'<meta property="og:image" content="{base}/img/og.png">\n<meta name="twitter:card" content="summary">\n'
    download = download_link(site, root)
    n, f = t["nav"], t["footer"]
    donate_btn = (f'<a class="btn btn-small btn-donate" href="{escape(site["donate_url"])}" target="_blank" rel="noopener" '
                  f'aria-label="{escape(n["donate_label"])}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.5-9.3C1.1 8.3 3 5 6.2 5c2 0 3.4 1.1 4.2 2.4h.2C11.4 6.1 12.800 5 14.8 5 18 5 19.900 8.300 18.500 11.700 16.500 16.400 12 21 12 21z" transform="translate(1 0)" fill="currentColor"/></svg><span>{n["donate"]}</span></a>'
                  if site.get("donate_url") else "")
    nav_button = (f'<a class="btn btn-small" href="{download}" download>{n["download"]}</a>' if download
                  else f'<span class="btn btn-small btn-soon">{t["soon"]["soon"]}</span>')
    donate = f'<a href="{escape(site["donate_url"])}" rel="noopener">{f["donate"]}</a>' if site.get("donate_url") else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{detect}
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
{seo}<link rel="icon" type="image/png" href="{root}img/favicon.png">
<link rel="apple-touch-icon" href="{root}img/apple-touch-icon.png">
<link rel="stylesheet" href="{root}css/styles.css">
</head>
<body class="page-{page}">
<header class="nav" id="nav">
  <div class="nav-in">
    <a class="brand" href="{home or '#top'}">{icon_img(root, 28, "brand-icon")}<span>{site["app_name"]}</span></a>
    <nav class="nav-links" aria-label="{escape(n['features'])}">
      <a href="{home}#why">{n["why"]}</a>
      <a href="{home}#features">{n["features"]}</a>
      <a href="{home}#editions">{n["editions"]}</a>
      <a href="{home}#ipad">{n["ipad"]}</a>
      <a href="privacy.html">{n["privacy"]}</a>
      <a href="support.html">{n["support"]}</a>
    </nav>
    <div class="nav-end">
      {toggle}
      {donate_btn}
      {nav_button}
    </div>
  </div>
</header>
<main id="top">
{body}
</main>
<footer class="footer">
  <div class="wrap">
    <div class="footer-top">
      <a class="brand" href="{home or '#top'}">{icon_img(root, 28, "brand-icon")}<span>{site["app_name"]}</span></a>
      <nav class="footer-links">
        <a href="privacy.html">{f["privacy"]}</a>
        <a href="support.html">{f["support"]}</a>
        <a href="mailto:{site["contact_email"]}?subject=J%2B%2B">{f["contact"]}</a>
        {donate}
        <a href="{other_href}" lang="{other}" hreflang="{other}">{other_t["lang_name"]}</a>
      </nav>
    </div>
    <p class="fine">© {site["year"]} {site["author"]}. {f["rights"]}</p>
    <p class="fine">{f["credits"]}</p>
  </div>
</footer>
<script src="{root}js/main.js" defer></script>
</body>
</html>
"""


def store_button(site, label, label_soon, cls):
    """The Mac App Store button: a link once app_store_url is set, otherwise a quiet "coming soon" label."""
    url = site.get("app_store_url", "")
    if url:
        return f'<a class="{cls}" href="{escape(url)}" rel="noopener">{label}</a>'
    return f'<span class="btn btn-soon">{label_soon}</span>'


def editions_html(site, t, root):
    e = t["editions"]
    lite, full = e["lite"], e["full"]
    download = download_link(site, root)
    li = lambda items: "".join(f"<li>{x}</li>" for x in items)
    lite_btn = (f'<a class="btn" href="{download}" download>{lite["button"]}</a>' if download
                else f'<span class="btn btn-soon">{t["soon"]["soon"]}</span>')
    full_btn = store_button(site, full["button"], full["button_soon"], "btn btn-ghost")
    rows = ""
    for name, a, b in e["rows"]:
        mark = lambda v: (f'<span class="yes" role="img" aria-label="{escape(e["yes"])}">&#10003;</span>' if v == "yes"
                          else f'<span class="no" role="img" aria-label="{escape(e["no"])}">&mdash;</span>')
        rows += f'<tr><th scope="row">{name}</th><td>{mark(a)}</td><td>{mark(b)}</td></tr>\n'
    return f"""</section>

<section class="section" id="editions">
  <div class="wrap">
    <p class="eyebrow reveal">{e["eyebrow"]}</p>
    <h2 class="reveal">{e["title"]}</h2>
    <p class="lead reveal">{e["text"]}</p>
    <div class="editions">
      <article class="edition reveal">
        <p class="tag">{lite["tag"]}</p>
        <h3>{lite["name"]}</h3>
        <p>{lite["text"]}</p>
        <ul>{li(lite["items"])}</ul>
        <div class="actions">{lite_btn}</div>
      </article>
      <article class="edition full reveal">
        <p class="tag">{full["tag"]}</p>
        <h3>{full["name"]}</h3>
        <p>{full["text"]}</p>
        <ul>{li(full["items"])}</ul>
        <div class="actions">{full_btn}</div>
      </article>
    </div>
    <h3 class="table-title reveal">{e["table_title"]}</h3>
    <div class="table-wrap reveal">
      <table class="compare">
        <thead><tr><th scope="col">{e["head"][0]}</th><th scope="col">{e["head"][1]}</th><th scope="col">{e["head"][2]}</th></tr></thead>
        <tbody>
{rows}        </tbody>
      </table>
    </div>
    <p class="note reveal">{e["note"]}</p>
  </div>
"""


def ipad_html(t, root):
    p = t["ipad"]
    iw, ih = image_size("ipad")
    tiles = "".join(f'      <article class="tile reveal"><h3>{it["title"]}</h3><p>{it["text"]}</p></article>\n' for it in p["items"])
    return f"""</section>

<section class="section alt" id="ipad">
  <div class="wrap">
    <p class="eyebrow reveal">{p["eyebrow"]}</p>
    <h2 class="reveal">{p["title"]}</h2>
    <p class="lead reveal">{p["text"]}</p>
    <p class="reveal"><span class="soon-badge">{p["badge"]}</span></p>
    <p class="note reveal">{p["badge_note"]}</p>
    <div class="ipad-shot reveal">{picture(root, "ipad", p["image_alt"], iw, ih)}</div>
    <div class="tiles">
{tiles}    </div>
    <p class="note reveal">{p["note"]}</p>
  </div>
"""


def home(site, t, lang):
    root = "" if lang == LANGS[0] else "../"
    download = download_link(site, root)
    h, w, fe, c, soon = t["hero"], t["why"], t["features"], t["cta"], t["soon"]
    notify = f'mailto:{site["contact_email"]}?subject={quote(soon["notify_subject"])}'
    store = (f'<a class="btn btn-ghost" href="{escape(site["app_store_url"])}" rel="noopener">{h["app_store"]}</a>'
             if site.get("app_store_url") else f'<a class="btn btn-ghost" href="#features">{h["secondary"]}</a>')
    ow, oh = image_size("overview")
    out = f"""<section class="hero">
  <div class="wrap">
    {icon_img(root, 128, "hero-icon reveal", site["app_name"])}
    <p class="eyebrow reveal">{fill(h["eyebrow"], site)}</p>
    <h1 class="reveal">{h["title"]}</h1>
    <p class="lead reveal">{h["text"]}</p>
    <div class="actions reveal">
      {f'<a class="btn" href="{download}" download>{h["primary"]}</a>' if download else f'<span class="btn btn-soon">{soon["soon"]}</span>'}
      {store}
    </div>
    <p class="note reveal">{fill(h["note"], site) if download else soon["note_soon"]}</p>
    <p class="note reveal"><a href="#editions">{h["store_note"]}</a></p>
  </div>
  <div class="hero-shot reveal">{picture(root, "overview", h["image_alt"], ow, oh, lazy=False)}</div>
</section>

<section class="stats" aria-label="J++">
  <div class="wrap stats-grid">
"""
    for s in t["stats"]:
        out += f'    <div class="stat reveal"><strong>{escape(s["value"])}</strong><span>{s["label"]}</span></div>\n'
    out += f"""  </div>
</section>

<section class="section alt" id="why">
  <div class="wrap">
    <p class="eyebrow reveal">{w["eyebrow"]}</p>
    <h2 class="reveal">{w["title"]}</h2>
    <p class="lead reveal">{w["text"]}</p>
    <div class="tiles">
"""
    for it in w["items"]:
        out += (f'      <article class="tile reveal"><svg class="tile-icon" viewBox="0 0 24 24" aria-hidden="true">{ICONS[it["icon"]]}</svg>'
                f'<h3>{it["title"]}</h3><p>{it["text"]}</p></article>\n')
    out += f"""    </div>
  </div>
</section>

<section class="section" id="features">
  <div class="wrap">
    <p class="eyebrow reveal">{fe["eyebrow"]}</p>
    <h2 class="reveal">{fe["title"]}</h2>
  </div>
"""
    for i, it in enumerate(fe["items"]):
        iw, ih = image_size(it["image"])
        bullets = "".join(f"<li>{b}</li>" for b in it["bullets"])
        cls = "feature" + (" flip" if i % 2 else "") + (" dialog" if it.get("dialog") else "")
        out += f"""  <article class="{cls}" id="{it["id"]}">
    <div class="feature-text reveal">
      <p class="eyebrow">{it["eyebrow"]}</p>
      <h3>{it["title"]}</h3>
      <p>{it["text"]}</p>
      <ul>{bullets}</ul>
    </div>
    <div class="feature-shot reveal">{picture(root, it["image"], it["alt"], iw, ih)}</div>
  </article>
"""
    out += editions_html(site, t, root)
    out += ipad_html(t, root)
    out += f"""</section>

<section class="section alt" id="less">
  <div class="wrap">
    <h2 class="reveal">{t["less"]["title"]}</h2>
    <div class="less-grid">
"""
    for it in t["less"]["items"]:
        out += f'      <div class="less reveal"><h3>{it["title"]}</h3><p>{it["text"]}</p></div>\n'
    out += f"""    </div>
    <div class="guide reveal"><h3>{t["guide"]["title"]}</h3><p>{t["guide"]["text"]}</p></div>
  </div>
</section>

<section class="section cta" id="download">
  <div class="wrap">
    {icon_img(root, 96, "cta-icon reveal")}
    <h2 class="reveal">{c["title"]}</h2>
    <p class="lead reveal">{c["text"] if download else fill(soon["cta_text"], site)}</p>
    <div class="actions reveal">{f'<a class="btn btn-large" href="{download}" download>{fill(c["primary"], site)}</a>' if download else f'<a class="btn btn-large" href="{notify}">{soon["notify"]}</a>'}</div>
    <p class="note reveal">{fill(c["note"], site) if download else soon["note_soon"]}</p>
    <div class="actions reveal">{store_button(site, c["store"], c["store_soon"], "btn btn-ghost")}</div>
    <p class="note reveal">{c["requirements"]}</p>
  </div>
</section>
"""
    return layout(site, t, lang, "home", t["meta"]["title"], t["meta"]["description"], out)


def article(site, t, lang, page):
    p = t[f"{page}_page"]
    body = f'<article class="doc wrap">\n<h1>{p["title"]}</h1>\n'
    if p.get("updated"):
        body += f'<p class="fine">{p["updated"]}</p>\n'
    body += f'<p class="lead">{p["intro"]}</p>\n'
    for s in p["sections"]:
        body += f'<h2>{s["title"]}</h2>\n{fill(s["body"], site)}\n'
    body += "</article>\n"
    return layout(site, t, lang, page, f'{site["app_name"]} — {p["title"]}', p["description"], body)


def build():
    site = load("site.json")
    # public/ is updated in place (only what changed is written), which is kinder to iCloud and to Git
    written = set()

    def put(path, data):
        written.add(path)
        if not path.exists() or path.read_bytes() != data:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    for src in (ROOT / "assets").rglob("*"):
        if src.is_file() and src.name != ".DS_Store":
            put(OUT / src.relative_to(ROOT / "assets"), src.read_bytes())
    urls = []
    for lang in LANGS:
        t = load(f"content/{lang}.json")
        d = OUT / lang_dir(lang)
        put(d / "index.html", home(site, t, lang).encode("utf-8"))
        for page in ("privacy", "support"):
            put(d / PAGES[page], article(site, t, lang, page).encode("utf-8"))
        urls += [f"{lang_dir(lang)}", f"{lang_dir(lang)}privacy.html", f"{lang_dir(lang)}support.html"]
    base = site.get("base_url", "").rstrip("/")
    if base:
        items = "".join(f"<url><loc>{base}/{u}</loc></url>\n" for u in urls)
        put(OUT / "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n'.encode("utf-8"))
        put(OUT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n".encode("utf-8"))
    for old in sorted(OUT.rglob("*"), reverse=True):      # whatever is no longer part of the site
        if old.is_file() and old not in written:
            old.unlink()
        elif old.is_dir() and not any(old.iterdir()):
            old.rmdir()
    target = OUT / site["download_url"]
    if site["download_url"] and not site["download_url"].startswith("http") and not target.exists():
        print(f"warning: the download {site['download_url']} is not in assets/")
    print(f"built {len(urls)} pages in {OUT}")


if __name__ == "__main__":
    build()
    if sys.argv[1:2] == ["serve"]:
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print(f"preview at http://localhost:{port}  (Ctrl-C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
