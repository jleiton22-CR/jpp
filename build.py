#!/usr/bin/env python3
"""Builds the jplus2 website into public/.

    python3 build.py           build the site
    python3 build.py serve     build it and preview it at http://localhost:8080

Texts are in content/en.json and content/es.json, settings in site.json, and the
style, script, images and downloads in assets/. Only Python 3 is needed.
"""
import functools
import http.server
import json
import re
import datetime
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
LANGS = ["en", "es"]          # the first one is published at the top of the site
PAGES = {"home": "index.html", "privacy": "privacy.html", "support": "support.html", "thanks": "thanks.html", "get": "get.html"}

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


def file_url(site, root):
    """The address of the installer itself, or "" while there is nothing to download."""
    url = site.get("download_url", "")
    return url if url.startswith("http") or not url else root + url


def email_gate(site):
    """The Buttondown username that collects the email before the download, or "" while the email page is off."""
    user = site.get("buttondown_username", "").strip()
    if user and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,40}", user):
        raise SystemExit("site.json: buttondown_username may only have letters, numbers, hyphens and underscores")
    return user


def download_link(site, root):
    """Where the download buttons lead: the email page when it is on, otherwise the thank-you page (which starts the
    download). "" while there is nothing to download."""
    if not site.get("download_url"):
        return ""
    return "get.html" if email_gate(site) else "thanks.html"


def lang_dir(lang):
    return "" if lang == LANGS[0] else lang + "/"


def picture(root, name, alt, w, h, lazy=True, cls=""):
    """A screenshot that follows the light or dark appearance of the visitor's system."""
    loading = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    dark = "(prefers-color-scheme: dark)"
    return (f'<picture><source srcset="{root}img/{name}-dark.webp" type="image/webp" media="{dark}">'
            f'<source srcset="{root}img/{name}-dark.jpg" media="{dark}">'
            f'<source srcset="{root}img/{name}-light.webp" type="image/webp">'
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


def layout(site, t, lang, page, title, description, body, crumb=None, guide=None, article=None):
    root = "" if lang == LANGS[0] else "../"
    here = guide["file"] if guide else PAGES[page]
    home = "index.html" if page != "home" else ""
    other = [l for l in LANGS if l != lang][0]
    other_t = load(f"content/{other}.json")
    # the address of this same page in the other language; ?lang= records that the visitor chose it
    plain = f"{root}{lang_dir(other)}{here if page != 'home' else ''}" or "./"
    if guide:      # a guide has its own address in each language, and may exist in only one
        plain = (f"{root}{lang_dir(other)}{guide['pairs'][other]}.html" if other in guide["pairs"] else f"{root}{lang_dir(other)}")
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
    if guide and other not in guide["pairs"]:
        detect = ""      # no translation of this guide: do not bounce the visitor to a page that does not exist
    base = site.get("base_url", "").rstrip("/")
    seo = ""
    if base:
        locale = {"en": "en_US", "es": "es_ES"}
        url = f'{base}/{lang_dir(lang)}{here if page != "home" else ""}'
        seo += f'<meta property="og:url" content="{url}">\n<meta property="og:site_name" content="{escape(site["app_name"])}">\n'
        seo += f'<meta property="og:locale" content="{locale.get(lang, lang)}">\n'
        seo += "".join(f'<meta property="og:locale:alternate" content="{locale.get(l, l)}">\n' for l in LANGS if l != lang and (not guide or l in guide["pairs"]))
        seo += f'<link rel="canonical" href="{base}/{lang_dir(lang)}{here if page != "home" else ""}">\n'
        if guide:
            for l, sl in guide["pairs"].items():
                seo += f'<link rel="alternate" hreflang="{l}" href="{base}/{lang_dir(l)}{sl}.html">\n'
            xl = LANGS[0] if LANGS[0] in guide["pairs"] else lang
            seo += f'<link rel="alternate" hreflang="x-default" href="{base}/{lang_dir(xl)}{guide["pairs"][xl]}.html">\n'
        else:
            for l in LANGS:
                seo += f'<link rel="alternate" hreflang="{l}" href="{base}/{lang_dir(l)}{here if page != "home" else ""}">\n'
            seo += f'<link rel="alternate" hreflang="x-default" href="{base}/{here if page != "home" else ""}">\n'
        seo += (f'<meta property="og:image" content="{base}/img/og.png">\n<meta property="og:image:width" content="1200">\n'
                f'<meta property="og:image:height" content="630">\n<meta property="og:image:alt" content="{escape(site["app_name"])}">\n'
                f'<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:title" content="{escape(title)}">\n'
                f'<meta name="twitter:description" content="{escape(description)}">\n<meta name="twitter:image" content="{base}/img/og.png">\n')
        if page in ("thanks", "get"):
            seo += '<meta name="robots" content="noindex">\n'
        ids = {"site": f"{base}/#website", "person": f"{base}/#person", "app": f"{base}/#app"}
        graph = []
        if page == "home":
            gate = bool(email_gate(site))
            graph = [
                {"@type": "WebSite", "@id": ids["site"], "url": f"{base}/", "name": site["app_name"],
                 "inLanguage": LANGS, "publisher": {"@id": ids["person"]}},
                {"@type": "Person", "@id": ids["person"], "name": site["author"], "url": f"{base}/",
                 "sameAs": [site["github_profile"]] if site.get("github_profile") else []},
                {"@type": "SoftwareApplication", "@id": ids["app"], "name": site["app_name"],
                 "alternateName": site["app_name"] + " Lite", "url": url, "inLanguage": lang,
                 "description": description, "applicationCategory": "DeveloperApplication",
                 "operatingSystem": "macOS 12.0 or later", "softwareVersion": site["version"],
                 "fileSize": site["download_size"], "image": f"{base}/img/og.png",
                 "screenshot": [f"{base}/img/{n}-light.jpg" for n in ("overview", "debug", "assistant", "excel")],
                 "author": {"@id": ids["person"]}, "publisher": {"@id": ids["person"]},
                 "offers": {"@type": "Offer", "name": site["app_name"] + " Lite", "price": "0", "priceCurrency": "USD",
                            "availability": "https://schema.org/InStock", "url": f"{base}/{lang_dir(lang)}#download"},
                 "featureList": [re.sub("<[^>]+>", "", r[0]) for r in t["editions"]["rows"]]}]
            if site.get("download_url"):
                graph[2]["installUrl"] = f"{base}/{lang_dir(lang)}{'get' if gate else 'thanks'}.html"
        elif page == "guide" and article:
            graph = [{"@type": "Person", "@id": ids["person"], "name": site["author"], "url": f"{base}/"},
                     {"@type": "Article", "headline": article["headline"], "description": description, "inLanguage": lang,
                      "datePublished": article["published"], "dateModified": article["updated"], "url": url,
                      "mainEntityOfPage": url, "image": f"{base}/img/og.png", "author": {"@id": ids["person"]},
                      "publisher": {"@id": ids["person"]}},
                     {"@type": "BreadcrumbList", "itemListElement": [
                         {"@type": "ListItem", "position": 1, "name": site["app_name"], "item": f"{base}/{lang_dir(lang)}"},
                         {"@type": "ListItem", "position": 2, "name": crumb, "item": url}]}]
        elif crumb:
            graph = [{"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": site["app_name"], "item": f"{base}/{lang_dir(lang)}"},
                {"@type": "ListItem", "position": 2, "name": crumb, "item": url}]}]
        if graph:
            seo += '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False) + "</script>\n"
    download = download_link(site, root)
    n, f = t["nav"], t["footer"]
    donate_btn = (f'<a class="btn btn-small btn-donate" href="{escape(site["donate_url"])}" target="_blank" rel="noopener" '
                  f'aria-label="{escape(n["donate_label"])}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.5-9.3C1.1 8.3 3 5 6.2 5c2 0 3.4 1.1 4.2 2.4h.2C11.4 6.1 12.800 5 14.8 5 18 5 19.900 8.300 18.500 11.700 16.500 16.400 12 21 12 21z" transform="translate(1 0)" fill="currentColor"/></svg><span>{n["donate"]}</span></a>'
                  if site.get("donate_url") else "")
    nav_button = (f'<a class="btn btn-small" href="{download}">{n["download"]}</a>' if download
                  else f'<span class="btn btn-small btn-soon">{t["soon"]["soon"]}</span>')
    donate = f'<a href="{escape(site["donate_url"])}" rel="noopener">{f["donate"]}</a>' if site.get("donate_url") else ""
    glinks = "".join(f'<a href="{g["slug"]}.html">{g["short"]}</a>' for g in GUIDES.get(lang, []))
    guides_nav = f'<nav class="footer-guides" aria-label="{escape(f["guides"])}"><strong>{f["guides"]}</strong>{glinks}</nav>' if glinks else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add("nav-js")</script>
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
<a class="skip" href="#top">{n["skip"]}</a>
<header class="nav" id="nav">
  <div class="nav-in">
    <a class="brand" href="{home or '#top'}">{icon_img(root, 28, "brand-icon")}<span>{site["app_name"]}</span></a>
    <nav class="nav-links" id="menu" aria-label="{escape(n['main_label'])}">
      <a href="{home}#why">{n["why"]}</a>
      <a href="{home}#features">{n["features"]}</a>
      <a href="{home}#editions">{n["editions"]}</a>
      <a href="{home}#ipad">{n["ipad"]}</a>
      <a href="privacy.html">{n["privacy"]}</a>
      <a href="support.html">{n["support"]}</a>
      {f'<a class="menu-only" href="{download}">{n["download"]}</a>' if download else ""}
    </nav>
    <div class="nav-end">
      {toggle}
      {donate_btn}
      {nav_button}
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="menu" aria-label="{escape(n["menu"])}"><span></span></button>
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
      <nav class="footer-links" aria-label="{escape(f["nav_label"])}">
        <a href="privacy.html">{f["privacy"]}</a>
        <a href="support.html">{f["support"]}</a>
        <a href="{PRESS[lang]}.html">{f["press"]}</a>
        <a href="mailto:{site["contact_email"]}?subject=jplus2">{f["contact"]}</a>
        {donate}
        <a href="{other_href}" lang="{other}" hreflang="{other}">{other_t["lang_name"]}</a>
      </nav>
    </div>
    {guides_nav}
    <p class="fine">© {site["year"]} {site["author"]}. {f["rights"]}</p>
    <p class="fine">{f["credits"]}</p>
  </div>
</footer>
<script src="{root}js/main.js" defer></script>
{visit_counter(site)}</body>
</html>
"""


def chip(t, edition):
    e = t["editions"]
    return (f'<span class="chip chip-full">{e["chip_full"]}</span>' if edition == "full"
            else f'<span class="chip">{e["chip_both"]}</span>')


def not_found(site):
    """404.html: GitHub Pages shows it for any address that does not exist, so everything here is absolute."""
    en, es = load("content/en.json"), load("content/es.json")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 — jplus2</title>
<meta name="robots" content="noindex">
<meta name="color-scheme" content="light dark">
<link rel="icon" type="image/png" href="/img/favicon.png">
<link rel="stylesheet" href="/css/styles.css">
</head>
<body class="page-404">
<main id="top" class="notfound">
  <div class="wrap">
    <picture><source srcset="/img/icon-dark.png" media="(prefers-color-scheme: dark)"><img class="hero-icon" src="/img/icon-light.png" alt="" width="96" height="96"></picture>
    <h1>404</h1>
    <p class="lead" lang="en">{en["notfound"]["text"]}</p>
    <p class="lead" lang="es">{es["notfound"]["text"]}</p>
    <div class="actions">
      <a class="btn" href="/" lang="en">{en["notfound"]["home"]}</a>
      <a class="btn btn-ghost" href="/es/" lang="es">{es["notfound"]["home"]}</a>
    </div>
  </div>
</main>
</body>
</html>
"""


def get_page(site, t, lang):
    """get.html: asks for the email, sends it to Buttondown in a new tab (its form must be a normal form post: it may show a
    CAPTCHA), and takes this tab on to thanks.html, which starts the download."""
    root = "" if lang == LANGS[0] else "../"
    k = t["getpage"]
    user = email_gate(site)
    action = f"https://buttondown.com/api/emails/embed-subscribe/{user}"
    body = f"""<section class="thanks wrap getpage">
  {icon_img(root, 96, "cta-icon")}
  <h1>{k["title"]}</h1>
  <p class="lead">{fill(k["lead"], site)}</p>
  <form class="emailform" id="emailform" method="post" action="{action}" target="_blank" rel="noopener" novalidate>
    <label for="email">{k["label"]}</label>
    <input id="email" name="email" type="email" required autocomplete="email" inputmode="email" spellcheck="false" autocapitalize="off"
      pattern="[^@\\s]+@[^@\\s]+\\.[^@\\s]{{2,}}" aria-describedby="hint" placeholder="{escape(k["placeholder"])}">
    <input type="hidden" name="embed" value="1">
    <input type="hidden" name="tag" value="download-lite">
    <p class="hint" id="hint" role="status" aria-live="polite" data-empty="{escape(k["hint"])}" data-invalid="{escape(k["invalid"])}"></p>
    <button class="btn btn-large" id="send" type="submit" aria-describedby="hint">{fill(k["button"], site)}</button>
  </form>
  <p class="skiprow"><a class="btn btn-ghost btn-large" id="skipdl" href="thanks.html">{k["skip"]}</a></p>
  <p class="note" id="after" hidden>{k["after"]}</p>
  <p class="note">{k["notice"]}</p>
</section>
<script>(function(){{
var f=document.getElementById("emailform"),i=document.getElementById("email"),b=document.getElementById("send"),h=document.getElementById("hint");
if(!f||!i||!b)return;
var re=/^[^@\\s]+@[^@\\s]+\\.[^@\\s]{{2,}}$/;
var sent=false;
function ok(){{return re.test(i.value.trim())}}
function sync(){{var v=i.value.trim(),good=ok();b.disabled=sent||!good;b.setAttribute("aria-disabled",good?"false":"true");
h.textContent=good?"":(v?h.dataset.invalid:h.dataset.empty);i.setAttribute("aria-invalid",(!good&&v)?"true":"false")}}
["input","change","keyup","blur","paste"].forEach(function(n){{i.addEventListener(n,sync)}});
var last=null;function watch(){{if(i.value!==last){{last=i.value;sync()}}}}
watch();setInterval(watch,400);   // some browsers fill the field (autofill, password managers) without firing an event
var sk=document.getElementById("skipdl");
if(sk)sk.addEventListener("click",function(){{try{{sessionStorage.removeItem("jpp-dl")}}catch(x){{}}}});
f.addEventListener("submit",function(e){{
if(!ok()){{e.preventDefault();sync();i.focus();return}}
i.value=i.value.trim();
try{{sessionStorage.removeItem("jpp-dl")}}catch(x){{}}
document.getElementById("after").hidden=false;sent=true;b.disabled=true;
setTimeout(function(){{location.href="thanks.html"}},1200)}});
}})();</script>
"""
    return layout(site, t, lang, "get", k["meta_title"], k["meta_desc"], body)


def thanks_page(site, t, lang):
    root = "" if lang == LANGS[0] else "../"
    k = t["thanks"]
    sha = site.get("download_sha256", "")
    f = lambda text: fill(text, site).replace("{sha256}", sha)
    steps = "".join(f'<li><h3>{f(a)}</h3><p>{f(b)}</p></li>' for a, b in k["steps"])
    nxt = "".join(f'<article class="tile"><h3>{a}</h3><p>{b}</p><p><a href="{href}">{label} ›</a></p></article>' for a, b, href, label in k["next"])
    donate = (f'<p class="thanks-donate">{k["donate_text"]} <a href="{escape(site["donate_url"])}" target="_blank" rel="noopener">{k["donate"]}</a></p>'
              if site.get("donate_url") else "")
    verify = ""
    if sha:
        verify = (f'<section class="thanks-verify"><h2>{k["verify_title"]}</h2><p>{k["verify_text"]}</p>'
                  f'<pre><code>shasum -a 256 ~/Downloads/jplus2-Lite-{site["version"]}.dmg</code></pre>'
                  f'<p>{k["verify_expect"]}</p><pre><code class="hash">{sha}</code></pre></section>')
    url = escape(file_url(site, root))
    body = f"""<section class="thanks wrap">
  {icon_img(root, 96, "cta-icon")}
  <h1>{k["title"]}</h1>
  <p class="lead" id="status">{k["status"]}</p>
  <div class="actions"><a class="btn btn-large" id="dl" href="{url}">{f(k["button"])}</a></div>
  <p class="note">{f(k["note"])}</p>
  <section class="thanks-steps"><h2>{k["steps_title"]}</h2><ol>{steps}</ol></section>
  {verify}
  <section class="thanks-next"><h2>{k["next_title"]}</h2><div class="tiles">{nxt}</div>{donate}</section>
  <p class="thanks-back"><a href="index.html">‹ {k["back"]}</a></p>
</section>
<script>(function(){{var a=document.getElementById("dl");if(!a)return;try{{if(sessionStorage.getItem("jpp-dl")==="1")return;sessionStorage.setItem("jpp-dl","1")}}catch(e){{}}setTimeout(function(){{location.href=a.href}},900)}})();</script>
"""
    return layout(site, t, lang, "thanks", k["meta_title"], k["meta_desc"], body)


def visit_counter(site):
    """GoatCounter: cookie-free visit counting. Nothing is added until `goatcounter_code` is set in site.json.
    It is skipped for visitors who send Do Not Track, and when the site is previewed on this computer."""
    code = site.get("goatcounter_code", "").strip()
    if not code:
        return ""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,40}", code):
        raise SystemExit("site.json: goatcounter_code must be only lowercase letters, numbers and hyphens")
    return ('<script>(function(){try{if(navigator.doNotTrack==="1"||window.doNotTrack==="1"||'
            '/^(localhost|127\\.|\\[::1\\])/.test(location.hostname))return}catch(e){}'
            'var s=document.createElement("script");s.async=true;s.src="https://gc.zgo.at/count.js";'
            's.setAttribute("data-goatcounter","https://' + code + '.goatcounter.com/count");document.body.appendChild(s)})()</script>\n')


def load_guides():
    """content/guides/*.json: one file per page and language. Pages of the same `group` are translations of each other."""
    out = {l: [] for l in LANGS}
    for f in sorted((ROOT / "content" / "guides").glob("*.json")):
        g = json.loads(f.read_text(encoding="utf-8"))
        out.setdefault(g["lang"], []).append(g)
    for l in out:
        out[l].sort(key=lambda g: g.get("order", 99))
    return out


GUIDES = load_guides()


def guide_pairs(g):
    """{language: slug} for every language this guide exists in."""
    return {l: x["slug"] for l, lst in GUIDES.items() for x in lst if x["group"] == g["group"]}


EMAIL_RE = r"[^@\s]+@[^@\s]+\.[^@\s]{2,}"


def waitlist_form(site, t, lang, tag):
    """Waiting list for the full version: a Buttondown form with the same validated button as get.html, or a mailto link."""
    k, g = t["waitlist"], t["getpage"]
    user = email_gate(site)
    if not user:
        notify = f'mailto:{site["contact_email"]}?subject={quote(t["soon"]["notify_subject"])}'
        return (f'<aside class="waitlist"><h2>{k["title"]}</h2><p>{k["text"]}</p>'
                f'<p><a class="btn" href="{notify}">{t["soon"]["notify"]}</a></p></aside>')
    uid = f"wl-{tag}"
    return f"""<aside class="waitlist" id="waitlist">
  <h2>{k["title"]}</h2>
  <p>{k["text"]}</p>
  <form class="emailform" id="{uid}" method="post" action="https://buttondown.com/api/emails/embed-subscribe/{user}" target="_blank" rel="noopener" novalidate>
    <label for="{uid}-email">{k["label"]}</label>
    <input id="{uid}-email" name="email" type="email" required autocomplete="email" inputmode="email" spellcheck="false" autocapitalize="off"
      pattern="{EMAIL_RE}" aria-describedby="{uid}-hint" placeholder="{escape(g["placeholder"])}">
    <input type="hidden" name="embed" value="1">
    <input type="hidden" name="tag" value="{tag}">
    <p class="hint" id="{uid}-hint" role="status" aria-live="polite" data-empty="{escape(k["hint"])}" data-invalid="{escape(g["invalid"])}"></p>
    <button class="btn" type="submit">{k["button"]}</button>
  </form>
  <p class="note" id="{uid}-after" hidden>{k["after"]}</p>
  <p class="note">{k["notice"]}</p>
</aside>
<script>(function(){{
var f=document.getElementById("{uid}"),i=document.getElementById("{uid}-email"),b=f&&f.querySelector("button"),h=document.getElementById("{uid}-hint");
if(!f||!i||!b)return;
var re=/^{EMAIL_RE}$/;
var sent=false;
function ok(){{return re.test(i.value.trim())}}
function sync(){{var v=i.value.trim(),good=ok();b.disabled=sent||!good;b.setAttribute("aria-disabled",good?"false":"true");
h.textContent=good?"":(v?h.dataset.invalid:h.dataset.empty);i.setAttribute("aria-invalid",(!good&&v)?"true":"false")}}
i.addEventListener("input",function(){{sent=false}});   // editing the address allows another send
["input","change","keyup","blur","paste"].forEach(function(n){{i.addEventListener(n,sync)}});
var last=null;function watch(){{if(i.value!==last){{last=i.value;sync()}}}}
watch();setInterval(watch,400);
f.addEventListener("submit",function(e){{if(!ok()){{e.preventDefault();sync();i.focus();return}}
i.value=i.value.trim();document.getElementById("{uid}-after").hidden=false;sent=true;b.disabled=true}});
}})();</script>
"""


def guide_page(site, t, lang, g):
    """A comparison or how-to page in content/guides/."""
    root = "" if lang == LANGS[0] else "../"
    ui = t["guide_ui"]
    download = download_link(site, root)
    parts = [f'<article class="doc wrap gpage">',
             f'<nav class="crumbs" aria-label="{escape(ui["crumbs"])}"><a href="index.html">{site["app_name"]}</a> <span aria-hidden="true">›</span> <span>{g["short"]}</span></nav>',
             f'<h1>{g["h1"]}</h1>',
             f'<p class="fine">{ui["updated"]}: <time datetime="{g["updated"]}">{g["updated"]}</time></p>',
             f'<p class="lead">{g["lead"]}</p>']
    for sec in g["sections"]:
        parts.append(f'<h2>{sec["h2"]}</h2>\n{fill(sec["html"], site)}')
    if g["cta"] == "waitlist":
        parts.append(waitlist_form(site, t, lang, g.get("tag", "waitlist-full")))
    elif download:
        parts.append(f'<aside class="gcta"><h2>{ui["cta_title"]}</h2><p>{fill(ui["cta_text"], site)}</p>'
                     f'<p><a class="btn btn-large" href="{download}">{fill(ui["cta_button"], site)}</a></p>'
                     f'<p class="note">{fill(ui["cta_note"], site)}</p></aside>')
    if g.get("faq"):
        parts.append(f'<h2>{ui["faq"]}</h2>\n<dl class="faq">' + "".join(f'<dt>{q["q"]}</dt><dd>{fill(q["a"], site)}</dd>' for q in g["faq"]) + "</dl>")
    rel = [x for grp in g.get("related", []) for x in GUIDES.get(lang, []) if x["group"] == grp]
    if rel:
        parts.append(f'<h2>{ui["related"]}</h2>\n<ul class="related">' + "".join(f'<li><a href="{x["slug"]}.html">{x["card_title"]}</a></li>' for x in rel) + "</ul>")
    parts.append("</article>")
    return layout(site, t, lang, "guide", g["meta_title"], g["meta_description"], "\n".join(parts), crumb=g["short"],
                  guide={"file": f'{g["slug"]}.html', "pairs": guide_pairs(g)},
                  article={"headline": g["h1"], "published": g["published"], "updated": g["updated"]})


def guides_home(site, t, lang):
    gs = GUIDES.get(lang, [])
    if not gs:
        return ""
    k = t["guides_home"]
    tiles = "".join(f'      <article class="tile reveal"><h3>{g["card_title"]}</h3><p>{g["card_text"]}</p>'
                    f'<p><a href="{g["slug"]}.html">{k["read"]} ›</a></p></article>\n' for g in gs)
    return f"""<section class="section" id="guides">
  <div class="wrap">
    <p class="eyebrow reveal">{k["eyebrow"]}</p>
    <h2 class="reveal">{k["title"]}</h2>
    <p class="lead reveal">{k["text"]}</p>
    <div class="tiles">
{tiles}    </div>
  </div>
</section>

"""


PRESS = {"en": "press", "es": "prensa"}
PRESS_SHOTS = ["overview", "intellisense-complete", "debug", "excel", "assistant", "github-clone"]
PRESS_ICONS = ["jplus2-icon-light-1024.png", "jplus2-icon-dark-1024.png"]


def _plain(html, site, extra=None):
    """A snippet of the content as plain text, for the README inside the press kit."""
    text = fill(html, site).replace("<br>", "\n")
    for k, v in (extra or {}).items():
        text = text.replace(k, v)
    return re.sub(r"\s+\n", "\n", re.sub(r"<[^>]+>", "", text)).replace("&amp;", "&")


def press_readme(site, tt):
    out = ["jplus2 press kit", "=" * 16, "", "Contents: icon/ (PNG, 1024 px, light and dark), screenshots/ (JPG, 1500 px wide, light and dark), this file.",
           "Updated: " + tt["en"]["press"]["updated"], ""]
    for lang, name in (("en", "ENGLISH"), ("es", "ESPAÑOL")):
        k = tt[lang]["press"]
        out += ["", name, "-" * len(name), "", k["facts_title"].upper()]
        out += [f"- {a}: " + _plain(b, site).replace("\n", " / ") for a, b in k["facts"]]
        out += ["", k["boiler_title"].upper()]
        for b in k["boilers"]:
            out += ["", b["label"] + ":", _plain(b["text"], site)]
        out += ["", k["brand_title"].upper()] + ["- " + _plain(x, site) for x in k["brand"]]
        out += ["", k["know_title"].upper()] + ["- " + _plain(x, site) for x in k["know"]]
    return "\n".join(out) + "\n"


def press_zip(site, tt):
    """press/jplus2-press-kit.zip. Fixed timestamps make the bytes depend only on the contents."""
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        def add(name, data):
            zi = zipfile.ZipInfo("jplus2-press-kit/" + name, (2026, 11, 16, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, data)
        for n in PRESS_ICONS:
            add(f"icon/{n}", (ROOT / "assets" / "press" / n).read_bytes())
        for n in PRESS_SHOTS:
            for ap in ("light", "dark"):
                add(f"screenshots/{n}-{ap}.jpg", (ROOT / "assets" / "img" / f"{n}-{ap}.jpg").read_bytes())
        add("README.txt", press_readme(site, tt).encode("utf-8"))
    return buf.getvalue()


def press_page(site, t, lang, zipsize):
    """The press kit: facts, text to copy, downloads, screenshots and contact."""
    k = t["press"]
    root = "" if lang == LANGS[0] else "../"
    ex = {"{zipsize}": zipsize}
    facts = "".join(f'<tr><th scope="row">{a}</th><td>{fill(b, site)}</td></tr>' for a, b in k["facts"])
    boil = ""
    for n, b in enumerate(k["boilers"]):
        boil += (f'<div class="copyblock"><h3>{b["label"]}</h3><p id="bp{n}">{fill(b["text"], site)}</p>'
                 f'<button type="button" class="btn btn-ghost btn-small" data-copy="bp{n}" data-label="{escape(k["copy"])}" data-done="{escape(k["copied"])}">{k["copy"]}</button></div>')
    shots = ""
    for sh in k["shots"]:
        w, h = image_size(sh["id"])
        shots += (f'<figure class="pshot"><a href="{root}img/{sh["id"]}-light.jpg">{picture(root, sh["id"], sh["caption"], w, h)}</a>'
                  f'<figcaption>{sh["caption"]}<br><a href="{root}img/{sh["id"]}-light.jpg">{k["light"]}</a> · <a href="{root}img/{sh["id"]}-dark.jpg">{k["dark"]}</a></figcaption></figure>')
    dl = download_link(site, root)
    targets = {"get": dl, "editions": "index.html#editions", "support": "support.html", "privacy": "privacy.html"}
    links = "".join(f'<li><a href="{targets[key]}">{label}</a></li>' for label, key in k["links"] if targets.get(key))
    body = f"""<article class="doc wrap gpage press">
<nav class="crumbs" aria-label="{escape(t["guide_ui"]["crumbs"])}"><a href="index.html">{site["app_name"]}</a> <span aria-hidden="true">›</span> <span>{k["short"]}</span></nav>
<h1>{k["h1"]}</h1>
<p class="fine">{t["guide_ui"]["updated"]}: <time datetime="{k["updated"]}">{k["updated"]}</time></p>
<p class="lead">{k["lead"]}</p>
<h2>{k["facts_title"]}</h2>
<div class="guide-table-wrap"><table class="facts-table"><tbody>{facts}</tbody></table></div>
<h2>{k["boiler_title"]}</h2>
{boil}
<h2>{k["assets_title"]}</h2>
<aside class="gcta"><p><a class="btn btn-large" href="{root}press/jplus2-press-kit.zip" download>{k["zip_label"].replace("{zipsize}", zipsize)}</a></p><p class="note">{k["zip_text"]}</p>
<ul class="icons"><li><a href="{root}press/{PRESS_ICONS[0]}" download>{k["icon_light"]}</a></li><li><a href="{root}press/{PRESS_ICONS[1]}" download>{k["icon_dark"]}</a></li></ul></aside>
<h2>{k["shots_title"]}</h2>
<p>{k["shots_note"]}</p>
<div class="pshots">{shots}</div>
<h2>{k["brand_title"]}</h2>
<ul>{"".join(f"<li>{x}</li>" for x in k["brand"])}</ul>
<h2>{k["know_title"]}</h2>
<ul>{"".join(f"<li>{x}</li>" for x in k["know"])}</ul>
<h2>{k["contact_title"]}</h2>
<p>{fill(k["contact_text"], site)}</p>
<h2>{k["links_title"]}</h2>
<ul class="related">{links}</ul>
</article>
<script>(function(){{document.querySelectorAll("[data-copy]").forEach(function(b){{b.addEventListener("click",function(){{
var el=document.getElementById(b.dataset.copy),text=el.textContent.trim();
function done(){{b.textContent=b.dataset.done;setTimeout(function(){{b.textContent=b.dataset.label}},1800)}}
function fallback(){{var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);try{{document.execCommand("copy");done()}}catch(e){{}}}}
if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(text).then(done,fallback)}}else{{fallback()}}}})}})}})();</script>
"""
    return layout(site, t, lang, "press", k["meta_title"], k["meta_description"], body, crumb=k["short"],
                  guide={"file": f"{PRESS[lang]}.html", "pairs": dict(PRESS)})


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
    lite_btn = (f'<a class="btn" href="{download}">{lite["button"]}</a>' if download
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


def agent_html(t):
    a = t["agent"]
    ul = lambda items: "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"
    cards = "".join(f'      <article class="tile reveal"><h3>{h}</h3>{ul(items)}</article>\n'
                    for h, items in ((a["cursor_title"], a["cursor"]), (a["windsurf_title"], a["windsurf"]),
                                     (a["diff_title"], a["diff"])))
    return f"""<section class="section" id="agent">
  <div class="wrap">
    <p class="eyebrow reveal">{a["eyebrow"]} <span class="chip chip-full">{a["chip"]}</span></p>
    <h2 class="reveal">{a["title"]}</h2>
    <p class="lead reveal">{a["text"]}</p>
    <div class="tiles agent-tiles">
{cards}    </div>
    <p class="reveal"><a class="btn btn-ghost" href="{a["more_slug"]}.html">{a["more"]} ›</a></p>
    <p class="note reveal"><strong>{a["lite"]}</strong></p>
    <p class="note reveal">{a["source"]}</p>
  </div>
</section>

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
    <p class="tagline reveal">{h["tagline"]}</p>
    <p class="lead reveal">{h["text"]}</p>
    <div class="actions reveal">
      {f'<a class="btn" href="{download}">{h["primary"]}</a>' if download else f'<span class="btn btn-soon">{soon["soon"]}</span>'}
      {store}
    </div>
    <p class="note reveal">{fill(h["note"], site) if download else soon["note_soon"]}</p>
    <p class="note reveal"><a href="#editions">{h["store_note"]}</a></p>
    <div class="pillars">{"".join(f'<div class="pillar reveal"><h2>{x[0]}</h2><p>{x[1]}</p></div>' for x in h["pillars"])}</div>
    <p class="note reveal">{h["pill_note"]}</p>
  </div>
  <div class="hero-shot reveal">{picture(root, "overview", h["image_alt"], ow, oh, lazy=False)}</div>
</section>

<section class="stats" aria-label="{site["app_name"]}">
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
    tabs = "".join(f'<a class="ftab" role="tab" id="tab-{it["id"]}" href="#{it["id"]}" aria-controls="{it["id"]}"'
                   f' aria-selected="{"true" if i == 0 else "false"}">{it["eyebrow"]}'
                   f'{"" if it.get("edition", "both") == "both" else ""}</a>' for i, it in enumerate(fe["items"]))
    out += f"""  <div class="wrap">
    <p class="lead reveal ftabs-pick">{fe["pick"]}</p>
    <nav class="ftabs reveal" role="tablist" aria-label="{escape(fe["title"])}">{tabs}</nav>
  </div>
  <div class="fpanels">
"""
    for i, it in enumerate(fe["items"]):
        iw, ih = image_size(it["image"])
        bullets = "".join(f"<li>{b}</li>" for b in it["bullets"])
        cls = "feature" + (" dialog" if it.get("dialog") else "")
        out += f"""  <article class="{cls}" id="{it["id"]}" role="tabpanel" aria-labelledby="tab-{it["id"]}">
    <div class="feature-text">
      <p class="eyebrow">{it["eyebrow"]} {chip(t, it.get("edition", "both"))}</p>
      <h3>{it["title"]}</h3>
      <p>{it["text"]}</p>
      <ul>{bullets}</ul>
    </div>
    <div class="feature-shot">{picture(root, it["image"], it["alt"], iw, ih)}</div>
  </article>
"""
    out += "  </div>\n"
    out += editions_html(site, t, root)
    out += ipad_html(t, root)
    out += f"""</section>

{agent_html(t)}<section class="section alt" id="less">
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

{guides_home(site, t, lang)}<section class="section cta" id="download">
  <div class="wrap">
    {icon_img(root, 96, "cta-icon reveal")}
    <h2 class="reveal">{c["title"]}</h2>
    <p class="lead reveal">{c["text"] if download else fill(soon["cta_text"], site)}</p>
    <div class="actions reveal">{f'<a class="btn btn-large" href="{download}">{fill(c["primary"], site)}</a>' if download else f'<a class="btn btn-large" href="{notify}">{soon["notify"]}</a>'}</div>
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
    counting = bool(site.get("goatcounter_code", "").strip())
    for s in p["sections"]:
        text = s["body"]
        if counting and p.get("site_plain") and p["site_plain"] in text:
            text = text.replace(p["site_plain"], p["site_counted"])
        if email_gate(site) and p.get("site_plain") and p["site_plain"] in s["body"] and p.get("email_note"):
            text = re.sub(r"</p>\s*$", " " + p["email_note"] + "</p>", text.rstrip())
        body += f'<h2>{s["title"]}</h2>\n{fill(text, site)}\n'
    body += "</article>\n"
    return layout(site, t, lang, page, p.get("meta_title") or f'{site["app_name"]} — {p["title"]}', p["description"], body, crumb=p["title"])


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
    tt = {l: load(f"content/{l}.json") for l in LANGS}
    zbytes = press_zip(site, tt)
    zipsize = f"{len(zbytes) / 1048576:.1f} MB"
    put(OUT / "press" / "jplus2-press-kit.zip", zbytes)
    for lang in LANGS:
        t = load(f"content/{lang}.json")
        d = OUT / lang_dir(lang)
        put(d / "index.html", home(site, t, lang).encode("utf-8"))
        for page in ("privacy", "support"):
            put(d / PAGES[page], article(site, t, lang, page).encode("utf-8"))
        if site.get("download_url"):
            put(d / PAGES["thanks"], thanks_page(site, t, lang).encode("utf-8"))
            if email_gate(site):
                put(d / PAGES["get"], get_page(site, t, lang).encode("utf-8"))
        urls += [f"{lang_dir(lang)}", f"{lang_dir(lang)}privacy.html", f"{lang_dir(lang)}support.html"]
        put(d / f"{PRESS[lang]}.html", press_page(site, t, lang, zipsize).encode("utf-8"))
        urls.append((f"{lang_dir(lang)}{PRESS[lang]}.html", t["press"]["updated"]))
        for g in GUIDES.get(lang, []):
            put(d / f'{g["slug"]}.html', guide_page(site, t, lang, g).encode("utf-8"))
            urls.append((f'{lang_dir(lang)}{g["slug"]}.html', g["updated"]))
    put(OUT / "404.html", not_found(site).encode("utf-8"))
    base = site.get("base_url", "").rstrip("/")
    if base:
        today = datetime.date.today().isoformat()
        items = "".join(f"<url><loc>{base}/{(u if isinstance(u, str) else u[0])}</loc><lastmod>{today if isinstance(u, str) else u[1]}</lastmod></url>\n" for u in urls)
        put(OUT / "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n'.encode("utf-8"))
        put(OUT / "robots.txt", f"User-agent: *\nAllow: /\nDisallow: /thanks.html\nDisallow: /es/thanks.html\nDisallow: /get.html\nDisallow: /es/get.html\nSitemap: {base}/sitemap.xml\n".encode("utf-8"))
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
