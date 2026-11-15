// jplus2 website: a line under the navigation after scrolling, and sections that appear as they come into view.
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
      if (e.isIntersecting) { e.target.classList.add("in"); seen.unobserve(e.target); }
    });
  }, { rootMargin: "0px 0px -8% 0px" });
  items.forEach(function (el) { seen.observe(el); });
})();
