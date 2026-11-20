(function () {
var box = document.getElementById("pg");
if (!box) return;
var $ = function (id) { return document.getElementById(id); };
var MAX_BYTES = 25 * 1024 * 1024;
var MAX_SHOW = 200;
var root = box.getAttribute("data-root") || "";
var msg = JSON.parse(box.getAttribute("data-msg"));
var SAMPLE = "month,region,product,units,revenue\n" +
"2026-01,North,Editor,120,2400\n2026-01,South,Editor,80,1600\n2026-01,North,Plugin,40,600\n" +
"2026-02,North,Editor,150,3000\n2026-02,South,Editor,95,1900\n2026-02,South,Plugin,60,900\n" +
"2026-03,North,Editor,170,3400\n2026-03,South,Editor,110,2200\n2026-03,North,Plugin,75,1125\n" +
"2026-03,South,Plugin,90,1350\n";
var db = null, SQL = null, loading = null, ran = false;
function count(name, title) {
try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: name, title: title, event: true }); } catch (e) {}
}
function status(text, bad) { var s = $("pg-status"); s.textContent = text; s.className = "pg-status" + (bad ? " bad" : ""); }
function loadEngine() {
if (SQL) return Promise.resolve(SQL);
if (loading) return loading;
status(msg.loading);
loading = new Promise(function (ok, fail) {
var s = document.createElement("script");
s.src = root + "vendor/sql-wasm.js";
s.onload = function () {
window.initSqlJs({ locateFile: function (f) { return root + "vendor/" + f; } }).then(function (m) { SQL = m; ok(m); }, fail);
};
s.onerror = function () { fail(new Error("load")); };
document.head.appendChild(s);
});
loading.catch(function () { loading = null; });
return loading;
}
function parseCSV(text) {
if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
var first = text.split("\n", 1)[0];
var sep = ",", best = 0;
[",", ";", "\t"].forEach(function (c) { var n = first.split(c).length; if (n > best) { best = n; sep = c; } });
var rows = [], row = [], cell = "", q = false, i = 0, n = text.length;
while (i < n) {
var ch = text[i];
if (q) {
if (ch === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += ch;
} else if (ch === '"') q = true;
else if (ch === sep) { row.push(cell); cell = ""; }
else if (ch === "\n") { row.push(cell); rows.push(row); row = []; cell = ""; }
else if (ch !== "\r") cell += ch;
i++;
}
if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
return rows.filter(function (r) { return !(r.length === 1 && r[0] === ""); });
}
function columnNames(head) {
var seen = {};
return head.map(function (h, i) {
var n = String(h).trim().replace(/[^A-Za-z0-9_]+/g, "_").replace(/^_+|_+$/g, "");
if (!n) n = "col" + (i + 1);
if (/^[0-9]/.test(n)) n = "c_" + n;
var base = n, k = 2;
while (seen[n.toLowerCase()]) n = base + "_" + k++;
seen[n.toLowerCase()] = 1;
return n;
});
}
function loadRows(rows, label) {
if (rows.length < 2) { status(msg.empty, true); return Promise.resolve(); }
return loadEngine().then(function (m) {
if (db) db.close();
db = new m.Database();
var names = columnNames(rows[0]);
var data = rows.slice(1);
var types = names.map(function (_, c) {
var allInt = true, allNum = true, seen = 0;
for (var r = 0; r < data.length; r++) {
var v = data[r][c];
if (v === undefined || v === "") continue;
seen++;
if (!/^-?[0-9]+$/.test(v)) allInt = false;
if (!/^-?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$/.test(v)) { allNum = false; break; }
}
return seen && allInt ? "INTEGER" : seen && allNum ? "REAL" : "TEXT";
});
db.run("CREATE TABLE data (" + names.map(function (nm, c) { return '"' + nm + '" ' + types[c]; }).join(", ") + ")");
var st = db.prepare("INSERT INTO data VALUES (" + names.map(function () { return "?"; }).join(",") + ")");
db.run("BEGIN");
for (var r = 0; r < data.length; r++) {
var line = names.map(function (_, c) { var v = data[r][c]; return v === undefined || v === "" ? null : (types[c] === "TEXT" ? v : Number(v)); });
st.run(line);
}
db.run("COMMIT");
st.free();
$("pg-cols").textContent = msg.table.replace("{cols}", names.map(function (nm, c) { return nm + " (" + types[c].toLowerCase() + ")"; }).join(", ")).replace("{n}", data.length);
$("pg-run").disabled = false;
$("pg-sql").disabled = false;
status(msg.ready.replace("{name}", label).replace("{n}", data.length));
if (!$("pg-sql").value) $("pg-sql").value = "SELECT * FROM data LIMIT 10;";
}).catch(function () { status(msg.fail, true); });
}
function show(res) {
var out = $("pg-out");
out.textContent = "";
if (!res.length) { status(msg.nothing); return; }
var r = res[res.length - 1];
var t = document.createElement("table");
var h = document.createElement("tr");
r.columns.forEach(function (c) { var th = document.createElement("th"); th.textContent = c; h.appendChild(th); });
t.appendChild(h);
r.values.slice(0, MAX_SHOW).forEach(function (v) {
var tr = document.createElement("tr");
v.forEach(function (x) { var td = document.createElement("td"); td.textContent = x === null ? "NULL" : String(x); if (typeof x === "number") td.className = "num"; tr.appendChild(td); });
t.appendChild(tr);
});
out.appendChild(t);
status(msg.rows.replace("{n}", r.values.length) + (r.values.length > MAX_SHOW ? " " + msg.shown.replace("{m}", MAX_SHOW) : ""));
}
function run() {
if (!db) return;
try { show(db.exec($("pg-sql").value)); }
catch (e) { $("pg-out").textContent = ""; status(msg.error + " " + (e && e.message ? e.message : ""), true); return; }
if (!ran) { ran = true; count("playground-run", "Playground: first query"); }
$("pg-after").hidden = false;
}
function readFile(f) {
if (!f) return;
if (f.size > MAX_BYTES) { status(msg.big, true); return; }
status(msg.reading);
var rd = new FileReader();
rd.onload = function () { loadRows(parseCSV(String(rd.result)), f.name); };
rd.onerror = function () { status(msg.fail, true); };
rd.readAsText(f);
}
$("pg-sample").addEventListener("click", function () { loadRows(parseCSV(SAMPLE), msg.sample_name); });
$("pg-file").addEventListener("change", function (e) { readFile(e.target.files[0]); });
$("pg-run").addEventListener("click", run);
$("pg-sql").addEventListener("keydown", function (e) { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); run(); } });
["dragover", "dragenter"].forEach(function (ev) { box.addEventListener(ev, function (e) { e.preventDefault(); box.classList.add("drag"); }); });
["dragleave", "drop"].forEach(function (ev) { box.addEventListener(ev, function () { box.classList.remove("drag"); }); });
box.addEventListener("drop", function (e) { e.preventDefault(); if (e.dataTransfer && e.dataTransfer.files[0]) readFile(e.dataTransfer.files[0]); });
})();