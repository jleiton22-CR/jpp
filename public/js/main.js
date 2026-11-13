// J++ website: a line under the navigation after scrolling, and sections that appear as they come into view.
(function () {
  var root = document.documentElement;
  var nav = document.getElementById("nav");
  function onScroll() { nav.classList.toggle("scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

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
