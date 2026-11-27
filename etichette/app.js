/* Generatore di etichette per collezione di minerali (dati da Mindat). */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const STORE = "minlabels.collection.v1";
  const SETTINGS = "minlabels.settings.v1";
  const MINDAT_DIRECT = "https://api.mindat.org/v1/";

  const DEFAULTS = {
    w: 70, h: 35, font: 7.5, copies: 1, header: "", family: "serif",
    margin: 8, border: true, showmid: true, showflag: true, showcountry: true, key: "",
  };

  // ---------------------------------------------------------------- storage
  const load = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch { return d; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* quota / privato */ } };

  let items = load(STORE, []);
  let settings = Object.assign({}, DEFAULTS, load(SETTINGS, {}));
  const persist = () => save(STORE, items);

  // ---------------------------------------------------------------- util
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);

  function decodeEntities(s) {
    const t = document.createElement("textarea");
    t.innerHTML = s;
    return t.value;
  }

  // HTML Mindat ("SiO<sub>2</sub>") -> markup modificabile ("SiO_2_")
  function htmlToMarkup(html) {
    if (!html) return "";
    let s = String(html)
      .replace(/<sub>(.*?)<\/sub>/gi, "_$1_")
      .replace(/<sup>(.*?)<\/sup>/gi, "^$1^")
      .replace(/<[^>]+>/g, "");
    return decodeEntities(s).trim();
  }

  // markup -> HTML sicuro per l'etichetta
  function markupToHtml(m) {
    return esc(m)
      .replace(/_([^_]+)_/g, "<sub>$1</sub>")
      .replace(/\^([^^]+)\^/g, "<sup>$1</sup>");
  }

  // ---------------------------------------------------------------- paese / bandiera
  const COUNTRIES = window.COUNTRIES || {};
  function codeForCountry(name) {
    if (!name) return "";
    const n = name.trim().toLowerCase().replace(/\s+/g, " ");
    if (COUNTRIES[n]) return COUNTRIES[n];
    const stripped = n.replace(/^(the|republic of)\s+/, "").replace(/\s*\(.*\)$/, "");
    return COUNTRIES[stripped] || "";
  }
  function countryFromLocality(loc) {
    if (!loc) return "";
    const parts = loc.split(",").map((s) => s.trim()).filter(Boolean);
    for (let i = parts.length - 1; i >= Math.max(0, parts.length - 2); i--) {
      if (codeForCountry(parts[i])) return parts[i];
    }
    return parts[parts.length - 1] || "";
  }
  const flagUrl = (cc) => (cc ? `flags/${cc.toLowerCase()}.svg` : "");

  // ---------------------------------------------------------------- QR
  function qrSvg(text, sizeMm) {
    if (!text || typeof qrcode !== "function") return "";
    const qr = qrcode(0, "M");
    qr.addData(unescape(encodeURIComponent(text))); // UTF-8
    qr.make();
    const n = qr.getModuleCount();
    let d = "";
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) if (qr.isDark(r, c)) d += `M${c} ${r}h1v1h-1z`;
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${n} ${n}" width="${sizeMm}mm" height="${sizeMm}mm" shape-rendering="crispEdges"><path d="${d}" fill="#000"/></svg>`;
  }
  function qrTarget(it) {
    switch (it.qrmode) {
      case "none": return "";
      case "custom": return it.qrcustom || "";
      case "locality": return it.locid ? `https://www.mindat.org/loc-${it.locid}.html` : (it.mid ? `https://www.mindat.org/min-${it.mid}.html` : "");
      default: return it.mid ? `https://www.mindat.org/min-${it.mid}.html` : "";
    }
  }

  // ---------------------------------------------------------------- render etichetta
  function labelHtml(it) {
    const s = settings;
    const qrText = qrTarget(it);
    const qrSize = Math.max(10, Math.min(s.h - 9, s.w * 0.36));
    const flag = s.showflag && it.cc ? `<img class="flag" src="${esc(flagUrl(it.cc))}" alt="${esc(it.cc)}" onerror="this.remove()">` : "";
    const country = it.country || "";
    // Evita di ripetere il paese se è già in coda alla località
    let loc = it.loc || "";
    if (s.showcountry && country && loc.toLowerCase().endsWith(country.toLowerCase())) {
      loc = loc.slice(0, loc.length - country.length).replace(/[,\s]+$/, "");
    }
    const head = s.header || it.num
      ? `<div class="l-head"><span>${esc(s.header)}</span><span>${it.num ? "N. " + esc(it.num) : ""}</span></div>` : "";
    const countryLine = s.showcountry && (country || flag)
      ? `<div class="l-country">${flag}<span>${esc(country)}</span></div>` : "";
    const nameFlag = !s.showcountry && flag ? flag : "";
    const foot = s.showmid && it.mid ? `<div class="l-foot"><span>Mindat ID ${esc(it.mid)}</span></div>` : "";

    return `<div class="label ${s.family} ${s.border ? "bordered" : ""}" style="width:${s.w}mm;height:${s.h}mm;--fs:${s.font}pt">
      ${head}
      <div class="l-body">
        <div class="l-text">
          <div class="l-name">${nameFlag}<span class="nm">${esc(it.name || "—")}</span></div>
          ${it.formula ? `<div class="l-formula">${markupToHtml(it.formula)}</div>` : ""}
          ${loc ? `<div class="l-loc">${esc(loc)}</div>` : ""}
          ${countryLine}
          ${it.notes ? `<div class="l-notes">${esc(it.notes)}</div>` : ""}
          ${foot}
        </div>
        ${qrText ? `<div class="l-qr">${qrSvg(qrText, qrSize)}</div>` : ""}
      </div>
    </div>`;
  }

  // ---------------------------------------------------------------- Mindat API
  let apiMode = null; // "proxy" | "direct"
  async function detectApi() {
    const st = $("apiStatus");
    if (location.protocol.startsWith("http")) {
      try {
        const r = await fetch("api/__ping");
        if (r.ok) {
          const j = await r.json();
          if (j.proxy) {
            apiMode = "proxy";
            st.textContent = j.key ? "API: server locale ✓" : "API: server senza chiave";
            st.className = "status " + (j.key ? "ok" : "err");
            return;
          }
        }
      } catch { /* niente proxy */ }
    }
    apiMode = "direct";
    st.textContent = settings.key ? "API: diretta (chiave nel browser)" : "API: manca la chiave";
    st.className = "status " + (settings.key ? "" : "err");
  }

  async function api(path) {
    if (!apiMode) await detectApi();
    let res;
    try {
      if (apiMode === "proxy") {
        res = await fetch("api/" + path);
      } else {
        if (!settings.key) throw new Error("Inserisci la chiave API Mindat nelle impostazioni (oppure avvia server.py).");
        res = await fetch(MINDAT_DIRECT + path, { headers: { Authorization: "Token " + settings.key, Accept: "application/json" } });
      }
    } catch (e) {
      if (e.message.startsWith("Inserisci")) throw e;
      throw new Error("Richiesta bloccata (CORS o rete). Avvia «python3 server.py» e apri http://localhost:8765");
    }
    if (!res.ok) {
      let msg = res.status + " " + res.statusText;
      try { const j = await res.json(); if (j.detail) msg += ": " + j.detail; } catch { }
      throw new Error("Mindat: " + msg);
    }
    return res.json();
  }
  const resultsOf = (j) => (Array.isArray(j) ? j : j.results || []);

  const MIN_FIELDS = "id,name,mindat_formula,ima_formula,ima_status,entrytype";
  async function searchMinerals(term) {
    term = term.trim();
    if (/^\d+$/.test(term)) return [await api(`geomaterials/${term}/?fields=${MIN_FIELDS}`)];
    const q = encodeURIComponent(term);
    let list = resultsOf(await api(`geomaterials/?q=${q}&fields=${MIN_FIELDS}&page_size=25`));
    if (!list.length) list = resultsOf(await api(`geomaterials/?name=${q}&fields=${MIN_FIELDS}&page_size=25`));
    // prima i nomi che iniziano con il termine, poi gli approvati IMA
    const t = term.toLowerCase();
    const score = (m) => ((m.name || "").toLowerCase() === t ? 0 : (m.name || "").toLowerCase().startsWith(t) ? 1 : 2);
    return list.sort((a, b) => score(a) - score(b));
  }
  async function searchLocalities(term) {
    term = term.trim();
    if (/^\d+$/.test(term)) return [await api(`localities/${term}/?fields=id,txt,country`)];
    return resultsOf(await api(`localities/?txt=${encodeURIComponent(term)}&fields=id,txt,country&page_size=25`));
  }

  // ---------------------------------------------------------------- dropdown risultati
  function showResults(ul, rows, onPick) {
    ul.innerHTML = "";
    ul.hidden = false;
    if (!rows.length) { ul.innerHTML = '<li class="msg">Nessun risultato</li>'; return; }
    rows.forEach((r) => {
      const li = document.createElement("li");
      li.innerHTML = r.html;
      li.addEventListener("mousedown", (e) => { e.preventDefault(); ul.hidden = true; onPick(r.data); });
      ul.appendChild(li);
    });
  }
  const showMsg = (ul, msg) => { ul.hidden = false; ul.innerHTML = `<li class="msg">${esc(msg)}</li>`; };
  document.addEventListener("click", (e) => {
    document.querySelectorAll(".results").forEach((ul) => { if (!ul.parentElement.contains(e.target)) ul.hidden = true; });
  });

  function pickMineral(m) {
    $("f_name").value = m.name || "";
    $("f_mid").value = m.id || "";
    $("f_formula").value = htmlToMarkup(m.mindat_formula) || htmlToMarkup(m.ima_formula) || "";
    updatePreview();
  }
  function pickLocality(l) {
    $("f_loc").value = decodeEntities(l.txt || "");
    $("f_locid").value = l.id || "";
    const country = l.country || countryFromLocality(l.txt);
    $("f_country").value = country;
    $("f_cc").value = codeForCountry(country);
    updatePreview();
  }

  async function doMineralSearch() {
    const ul = $("minResults");
    const term = $("f_name").value;
    if (!term.trim()) return;
    showMsg(ul, "Cerco…");
    try {
      const rows = await searchMinerals(term);
      showResults(ul, rows.map((m) => ({
        data: m,
        html: `<b>${esc(m.name)}</b> <span class="sub">#${m.id}${m.ima_status ? " · " + esc([].concat(m.ima_status).join(", ")) : ""}</span><br><span class="sub">${markupToHtml(htmlToMarkup(m.mindat_formula || m.ima_formula))}</span>`,
      })), pickMineral);
    } catch (e) { showMsg(ul, e.message); }
  }
  async function doLocalitySearch() {
    const ul = $("locResults");
    const term = $("f_loc").value;
    if (!term.trim()) return;
    showMsg(ul, "Cerco…");
    try {
      const rows = await searchLocalities(term);
      showResults(ul, rows.map((l) => ({
        data: l,
        html: `${esc(decodeEntities(l.txt || ""))} <span class="sub">#${l.id}</span>`,
      })), pickLocality);
    } catch (e) { showMsg(ul, e.message); }
  }
  async function loadById() {
    const id = $("f_mid").value.trim();
    if (!/^\d+$/.test(id)) return;
    const ul = $("minResults");
    showMsg(ul, "Carico…");
    try { pickMineral(await api(`geomaterials/${id}/?fields=${MIN_FIELDS}`)); ul.hidden = true; }
    catch (e) { showMsg(ul, e.message); }
  }

  // ---------------------------------------------------------------- form
  const FIELDS = { uid: "f_uid", name: "f_name", mid: "f_mid", num: "f_num", formula: "f_formula", loc: "f_loc", locid: "f_locid", country: "f_country", cc: "f_cc", qrmode: "f_qrmode", qrcustom: "f_qrcustom", notes: "f_notes" };
  function readForm() {
    const o = {};
    for (const [k, id] of Object.entries(FIELDS)) o[k] = $(id).value.trim();
    o.cc = o.cc.toLowerCase();
    return o;
  }
  function fillForm(it) {
    for (const [k, id] of Object.entries(FIELDS)) $(id).value = it[k] ?? (k === "qrmode" ? "mineral" : "");
    $("formTitle").textContent = it.uid ? "Modifica esemplare" : "Nuovo esemplare";
    $("btnSave").textContent = it.uid ? "Salva modifiche" : "Aggiungi alla collezione";
    updatePreview();
    renderList();
  }
  function updatePreview() {
    const it = readForm();
    $("customQrWrap").hidden = it.qrmode !== "custom";
    const img = $("flagPreview");
    if (it.cc) { img.src = flagUrl(it.cc); img.hidden = false; img.onerror = () => { img.hidden = true; }; } else img.hidden = true;
    $("livePreview").innerHTML = labelHtml(it);
  }

  $("f_loc").addEventListener("change", () => {
    if (!$("f_country").value) {
      const c = countryFromLocality($("f_loc").value);
      $("f_country").value = c;
      $("f_cc").value = codeForCountry(c);
    }
    updatePreview();
  });
  $("f_country").addEventListener("input", () => { const cc = codeForCountry($("f_country").value); if (cc) $("f_cc").value = cc; updatePreview(); });
  $("specForm").addEventListener("input", updatePreview);
  $("f_qrmode").addEventListener("change", updatePreview);
  $("btnSearchMin").addEventListener("click", doMineralSearch);
  $("btnSearchLoc").addEventListener("click", doLocalitySearch);
  $("btnLoadId").addEventListener("click", loadById);
  $("f_mid").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); loadById(); } });
  $("f_name").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); doMineralSearch(); } });
  $("f_loc").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); doLocalitySearch(); } });

  $("specForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const it = readForm();
    if (!it.name) return;
    if (it.uid) {
      const i = items.findIndex((x) => x.uid === it.uid);
      if (i >= 0) items[i] = Object.assign(items[i], it);
    } else {
      it.uid = uid();
      it.sel = true;
      items.push(it);
    }
    persist();
    fillForm({});
  });
  $("btnReset").addEventListener("click", () => fillForm({}));

  // ---------------------------------------------------------------- lista
  function renderList() {
    const f = $("filter").value.trim().toLowerCase();
    const tb = $("list").querySelector("tbody");
    const editing = $("f_uid").value;
    const rows = items.filter((it) => !f || [it.name, it.loc, it.num, it.country, it.mid].join(" ").toLowerCase().includes(f));
    tb.innerHTML = rows.map((it) => `
      <tr data-uid="${it.uid}" class="${it.uid === editing ? "editing" : ""}">
        <td><input type="checkbox" class="sel" ${it.sel ? "checked" : ""}></td>
        <td>${esc(it.num)}</td>
        <td><b>${esc(it.name)}</b><div class="small">${markupToHtml(it.formula)}${it.mid ? " · #" + esc(it.mid) : ""}</div></td>
        <td>${it.cc ? `<img src="${esc(flagUrl(it.cc))}" alt="" style="height:11px;border:1px solid #ccc" onerror="this.remove()"> ` : ""}${esc(it.loc)}</td>
        <td class="btns"><button class="edit">Modifica</button> <button class="dup" title="Duplica">⧉</button> <button class="del danger" title="Elimina">✕</button></td>
      </tr>`).join("") || `<tr><td colspan="5" class="muted">Nessun esemplare. Cerca un minerale a sinistra e aggiungilo.</td></tr>`;
    const nSel = items.filter((x) => x.sel).length;
    $("count").textContent = `(${items.length}, ${nSel} selezionati)`;
    $("selAll").checked = items.length > 0 && nSel === items.length;
  }
  $("filter").addEventListener("input", renderList);
  $("list").addEventListener("click", (e) => {
    const tr = e.target.closest("tr[data-uid]");
    if (!tr) return;
    const it = items.find((x) => x.uid === tr.dataset.uid);
    if (!it) return;
    if (e.target.classList.contains("sel")) { it.sel = e.target.checked; persist(); renderList(); }
    else if (e.target.classList.contains("edit")) { fillForm(it); window.scrollTo({ top: 0, behavior: "smooth" }); }
    else if (e.target.classList.contains("dup")) { items.splice(items.indexOf(it) + 1, 0, Object.assign({}, it, { uid: uid() })); persist(); renderList(); }
    else if (e.target.classList.contains("del")) {
      if (confirm(`Eliminare «${it.name}»?`)) { items = items.filter((x) => x !== it); persist(); if ($("f_uid").value === it.uid) fillForm({}); else renderList(); }
    }
  });
  $("selAll").addEventListener("change", (e) => { items.forEach((x) => (x.sel = e.target.checked)); persist(); renderList(); });
  $("btnDelSel").addEventListener("click", () => {
    const n = items.filter((x) => x.sel).length;
    if (n && confirm(`Eliminare ${n} esemplari selezionati?`)) { items = items.filter((x) => !x.sel); persist(); fillForm({}); }
  });

  // ---------------------------------------------------------------- CSV
  const CSV_COLS = [["num", "numero"], ["name", "minerale"], ["mid", "mindat_id"], ["formula", "formula"], ["loc", "localita"], ["locid", "mindat_loc_id"], ["country", "paese"], ["cc", "codice_paese"], ["notes", "note"], ["qrmode", "qr"], ["qrcustom", "qr_personalizzato"]];
  const csvCell = (v) => { v = String(v ?? ""); return /[",;\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v; };
  function parseCsv(text) {
    const sep = (text.split("\n")[0].match(/;/g) || []).length > (text.split("\n")[0].match(/,/g) || []).length ? ";" : ",";
    const rows = []; let row = [], cell = "", q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) {
        if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c;
      } else if (c === '"') q = true;
      else if (c === sep) { row.push(cell); cell = ""; }
      else if (c === "\n" || c === "\r") { if (c === "\r" && text[i + 1] === "\n") i++; row.push(cell); rows.push(row); row = []; cell = ""; }
      else cell += c;
    }
    if (cell || row.length) { row.push(cell); rows.push(row); }
    return rows.filter((r) => r.some((x) => x.trim()));
  }
  $("btnExportCsv").addEventListener("click", () => {
    const lines = [CSV_COLS.map((c) => c[1]).join(",")].concat(items.map((it) => CSV_COLS.map((c) => csvCell(it[c[0]])).join(",")));
    const blob = new Blob(["﻿" + lines.join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "collezione-minerali.csv";
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });
  $("importCsv").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const rows = parseCsv((await file.text()).replace(/^﻿/, ""));
    e.target.value = "";
    if (rows.length < 2) return alert("CSV vuoto.");
    const head = rows[0].map((h) => h.trim().toLowerCase());
    const idx = Object.fromEntries(CSV_COLS.map(([k, h]) => [k, head.indexOf(h)]));
    if (idx.name < 0) return alert("Il CSV deve avere almeno la colonna «minerale». Colonne: " + CSV_COLS.map((c) => c[1]).join(", "));
    let n = 0;
    for (const r of rows.slice(1)) {
      const it = { uid: uid(), sel: true };
      for (const [k] of CSV_COLS) it[k] = idx[k] >= 0 ? (r[idx[k]] || "").trim() : "";
      if (!it.name) continue;
      if (!it.qrmode) it.qrmode = "mineral";
      if (!it.country && it.loc) it.country = countryFromLocality(it.loc);
      if (!it.cc && it.country) it.cc = codeForCountry(it.country);
      items.push(it); n++;
    }
    persist(); renderList();
    alert(`Importati ${n} esemplari.`);
  });

  // ---------------------------------------------------------------- impostazioni
  const SET_INPUTS = { w: "s_w", h: "s_h", font: "s_font", copies: "s_copies", header: "s_header", family: "s_family", margin: "s_margin", border: "s_border", showmid: "s_showmid", showflag: "s_showflag", showcountry: "s_showcountry", key: "s_key" };
  for (const [k, id] of Object.entries(SET_INPUTS)) {
    const el = $(id);
    if (el.type === "checkbox") el.checked = !!settings[k]; else el.value = settings[k];
    el.addEventListener("input", () => {
      const v = el.type === "checkbox" ? el.checked : el.type === "number" ? (parseFloat(el.value) || DEFAULTS[k]) : el.value.trim();
      settings[k] = v;
      save(SETTINGS, settings);
      if (k === "key") { apiMode = null; detectApi(); }
      applyPageStyle();
      updatePreview();
    });
  }
  function applyPageStyle() {
    let st = $("pageStyle");
    if (!st) { st = document.createElement("style"); st.id = "pageStyle"; document.head.appendChild(st); }
    st.textContent = `@page { size: A4; margin: ${settings.margin}mm; }`;
  }

  // ---------------------------------------------------------------- stampa
  $("btnPrint").addEventListener("click", () => {
    const sel = items.filter((x) => x.sel);
    if (!sel.length) return alert("Seleziona almeno un esemplare nella collezione.");
    const copies = Math.max(1, settings.copies | 0);
    $("sheet").innerHTML = sel.flatMap((it) => Array(copies).fill(labelHtml(it))).join("");
    // attende il caricamento delle bandiere prima di stampare
    const imgs = [...$("sheet").querySelectorAll("img")];
    Promise.all(imgs.map((i) => (i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; })))).then(() => window.print());
  });

  // ---------------------------------------------------------------- avvio
  applyPageStyle();
  fillForm({});
  detectApi();
})();
