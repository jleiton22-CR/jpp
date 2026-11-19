// jplus2 website: a line under the navigation after scrolling, and sections that appear as they come into view.
// The page always opens at the top: when it is opened from outside, refreshed or reached with the back button, it starts at the
// hero, with no restored scroll position and no #section. Only a link from another page of this site may land on a section.
(function () {
  try { if ("scrollRestoration" in history) history.scrollRestoration = "manual"; } catch (e) {}
  var internal = false;
  try { internal = !!document.referrer && new URL(document.referrer).origin === location.origin; } catch (e) {}
  var nt = "navigate";
  try { var n = performance.getEntriesByType("navigation")[0]; if (n) nt = n.type; } catch (e) {}
  var keep = !!location.hash && internal && nt === "navigate";
  function up() { window.scrollTo({ top: 0, left: 0, behavior: "instant" }); }
  if (!keep) {
    if (location.hash && history.replaceState) history.replaceState(null, "", location.pathname + location.search);
    up();
    window.addEventListener("load", up);
    window.addEventListener("pageshow", function () { up(); });
    setTimeout(up, 60); setTimeout(up, 300);
  } else {
    window.addEventListener("load", function () {
      var el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (el && !el.classList.contains("feature")) el.scrollIntoView();
    });
  }
  window.__jpTop = !keep;
})();

(function () {
  var root = document.documentElement;
  var nav = document.getElementById("nav");
  function onScroll() { nav.classList.toggle("scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // menu button on small screens
  var toggle = document.querySelector(".nav-toggle");
  if (toggle) {
    var setOpen = function (open) { nav.classList.toggle("open", open); toggle.setAttribute("aria-expanded", open ? "true" : "false"); };
    toggle.addEventListener("click", function () { setOpen(!nav.classList.contains("open")); });
    nav.addEventListener("click", function (e) { if (e.target.closest(".nav-links a")) setOpen(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { setOpen(false); toggle.focus(); } });
  }

  var items = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) return;   // without it everything is simply visible
  root.classList.add("js");
  var seen = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting || e.boundingClientRect.top < 0) { e.target.classList.add("in"); seen.unobserve(e.target); }
    });
  }, { rootMargin: "0px 0px -8% 0px" });
  items.forEach(function (el) { seen.observe(el); });
})();

// Features: tabs that show one topic at a time. Without this script every topic stays visible.
(function () {
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".ftab"));
  if (!tabs.length) return;
  var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute("aria-controls")); });
  function show(i, focus) {
    tabs.forEach(function (t, k) {
      var on = k === i;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      panels[k].hidden = !on;
    });
    panels[i].querySelectorAll(".reveal").forEach(function (el) { el.classList.add("in"); });
    if (focus) tabs[i].focus();
    var bar = tabs[i]; if (bar.scrollIntoView) bar.scrollIntoView({ block: "nearest", inline: "center" });
  }
  tabs.forEach(function (t, i) {
    t.addEventListener("click", function (e) { e.preventDefault(); show(i, false); if (history.replaceState) history.replaceState(null, "", "#" + panels[i].id); });
    t.addEventListener("keydown", function (e) {
      var k = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (k) { e.preventDefault(); show((i + k + tabs.length) % tabs.length, true); }
      if (e.key === "Home") { e.preventDefault(); show(0, true); }
      if (e.key === "End") { e.preventDefault(); show(tabs.length - 1, true); }
    });
  });
  function fromHash() {
    var id = location.hash.slice(1), i = panels.findIndex(function (p) { return p && p.id === id; });
    if (i < 0 && !fromHash.first) { show(0, false); fromHash.first = 1; return; }
    if (i < 0) return;
    fromHash.first = 1;
    show(i, false);
    document.getElementById("features").scrollIntoView();
  }
  window.addEventListener("hashchange", fromHash);
  fromHash();
  var first = location.hash.slice(1);
  if (!panels.some(function (p) { return p && p.id === first; })) window.scrollTo(window.scrollX, window.scrollY);
})();

// the navigation shows where you are: the link of the section on screen is underlined
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll(".nav-links a[href*='#']"));
  if (!links.length || !document.getElementById("features")) return;
  var items = links.map(function (a) { var id = a.getAttribute("href").split("#")[1]; return { a: a, id: id, el: document.getElementById(id) }; });
  var ticking = false;
  function update() {
    ticking = false;
    var line = window.innerHeight * 0.35, current = null;
    items.forEach(function (it) {
      var sec = it.el;
      if (!sec) return;
      var r = sec.getBoundingClientRect();
      if (r.top <= line && r.bottom > line) current = it;
    });
    items.forEach(function (it) { if (it === current) it.a.setAttribute("aria-current", "true"); else it.a.removeAttribute("aria-current"); });
  }
  function req() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  window.addEventListener("scroll", req, { passive: true });
  document.addEventListener("click", req);
  window.addEventListener("hashchange", req);
  update();
})();

// Hero demo: the screenshots take turns while the demo is on screen; hover, focus or the pause button stop it.
(function () {
  var box = document.querySelector(".demo"); if (!box) return;
  var frames = Array.prototype.slice.call(box.querySelectorAll(".demo-frame")), dots = Array.prototype.slice.call(box.querySelectorAll(".demo-dot"));
  var title = box.querySelector(".demo-title"), text = box.querySelector(".demo-text"), pp = box.querySelector(".demo-pp");
  var cur = 0, timer = null, paused = false, visible = false, hold = false;
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (still) paused = true;
  function show(i) {
    cur = (i + frames.length) % frames.length;
    frames.forEach(function (f, k) { f.classList.toggle("on", k === cur); if (k === cur) f.removeAttribute("aria-hidden"); else f.setAttribute("aria-hidden", "true"); });
    dots.forEach(function (d, k) { d.classList.toggle("on", k === cur); d.setAttribute("aria-pressed", k === cur ? "true" : "false"); });
    if (frames[cur].hasAttribute("data-anim")) { var pic = frames[cur].querySelector("picture"); if (pic) pic.parentNode.replaceChild(pic.cloneNode(true), pic); }   // a fresh image plays its animation from the start
    title.textContent = frames[cur].getAttribute("data-title"); text.textContent = frames[cur].getAttribute("data-text");
  }
  function tick() { clearTimeout(timer); if (!paused && visible && !hold) timer = setTimeout(function () { show(cur + 1); tick(); }, +frames[cur].getAttribute("data-dur") || 5000); }
  function label() { pp.setAttribute("aria-label", box.getAttribute(paused ? "data-play" : "data-pause")); pp.firstChild.textContent = paused ? "▶" : "❚❚"; }
  dots.forEach(function (d, k) { d.addEventListener("click", function () { show(k); tick(); }); });
  pp.addEventListener("click", function () { paused = !paused; label(); tick(); });
  box.addEventListener("mouseenter", function () { hold = true; clearTimeout(timer); });
  box.addEventListener("mouseleave", function () { hold = false; tick(); });
  box.addEventListener("focusin", function () { hold = true; clearTimeout(timer); });
  box.addEventListener("focusout", function () { hold = false; tick(); });
  label();
  if ("IntersectionObserver" in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; tick(); }).observe(box);
  else { visible = true; tick(); }
})();
