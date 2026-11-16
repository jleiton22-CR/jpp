(function () {
var root = document.documentElement;
var nav = document.getElementById("nav");
function onScroll() { nav.classList.toggle("scrolled", window.scrollY > 8); }
window.addEventListener("scroll", onScroll, { passive: true });
onScroll();
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
show(i >= 0 ? i : 0, false);
if (i >= 0) document.getElementById("features").scrollIntoView();
}
window.addEventListener("hashchange", fromHash);
fromHash();
var first = location.hash.slice(1);
if (!panels.some(function (p) { return p && p.id === first; })) window.scrollTo(window.scrollX, window.scrollY);
})();
(function () {
var links = Array.prototype.slice.call(document.querySelectorAll(".nav-links a[href*='#']"));
if (!links.length || !document.getElementById("features")) return;
var items = links.map(function (a) { var id = a.getAttribute("href").split("#")[1]; return { a: a, id: id, el: document.getElementById(id) }; });
var ticking = false;
function update() {
ticking = false;
var line = window.innerHeight * 0.35, current = null;
var compareOn = document.querySelector(".ftab#tab-compare[aria-selected='true']");
items.forEach(function (it) {
var sec = it.id === "compare" ? document.getElementById("features") : it.el;
if (!sec) return;
var r = sec.getBoundingClientRect();
if (r.top <= line && r.bottom > line) {
if (it.id === "compare" && !compareOn) return;
if (it.id === "features" && compareOn) return;
current = it;
}
});
items.forEach(function (it) { if (it === current) it.a.setAttribute("aria-current", "true"); else it.a.removeAttribute("aria-current"); });
}
function req() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
window.addEventListener("scroll", req, { passive: true });
document.addEventListener("click", req);
window.addEventListener("hashchange", req);
update();
})();