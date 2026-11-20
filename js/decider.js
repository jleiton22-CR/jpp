(function () {
var box = document.getElementById("decider");
if (!box) return;
var $ = function (id) { return document.getElementById(id); };
var groups = {}, done = false;
var radios = [].slice.call(box.querySelectorAll("input[type=radio]"));
radios.forEach(function (r) { groups[r.name] = 1; });
var total = Object.keys(groups).length;
function count(name, title) {
try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: name, title: title, event: true }); } catch (e) {}
}
function update() {
var picked = radios.filter(function (r) { return r.checked; });
if (picked.length < total) { $("dc-status").textContent = picked.length ? box.getAttribute("data-need") : ""; return; }
$("dc-status").textContent = "";
var why = picked.filter(function (r) { return r.getAttribute("data-full") === "1"; });
var list = $("dc-why");
list.textContent = "";
why.forEach(function (r) { var li = document.createElement("li"); li.textContent = r.getAttribute("data-why"); list.appendChild(li); });
var full = why.length > 0;
$("dc-full").hidden = !full;
$("dc-lite").hidden = full;
$("dc-reset").hidden = false;
if (!done) { done = true; count(full ? "decider-result-full" : "decider-result-lite", "Decider: result " + (full ? "Full" : "Lite")); }
}
radios.forEach(function (r) { r.addEventListener("change", update); });
$("dc-reset").addEventListener("click", function () {
radios.forEach(function (r) { r.checked = false; });
$("dc-full").hidden = true; $("dc-lite").hidden = true; $("dc-reset").hidden = true; $("dc-status").textContent = "";
});
})();