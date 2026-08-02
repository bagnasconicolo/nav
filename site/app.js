/* ============================================================
   NAV · Mappa da campo
   Leaflet + WMS Regione Piemonte + overlay georeferenziati + GPS
   ============================================================ */
'use strict';

/* ---------- proj4: UTM 32N (EPSG:32632) ---------- */
proj4.defs('EPSG:32632', '+proj=utm +zone=32 +datum=WGS84 +units=m +no_defs');

/* ---------- Mappa ---------- */
const map = L.map('map', {
  zoomControl: true,
  attributionControl: true,
  maxZoom: 22,
  zoom: 15,
  center: [44.301, 7.59],   // Zona A (cuneese)
  zoomSnap: 0.5,
  tap: true
});
L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);
map.zoomControl.setPosition('topleft');

// Pane dedicato al GPS, sempre sopra tutti i livelli (che stanno a z 472–520)
map.createPane('gpsPane');
map.getPane('gpsPane').style.zIndex = 640;
map.getPane('gpsPane').style.pointerEvents = 'none';

/* ============================================================
   Definizione dei livelli
   type: 'tile' | 'wms' | 'image'
   ============================================================ */
// crossOrigin:'anonymous' -> richieste CORS: i server inviano ACAO:* quindi
// i tile si caricano ed evitano il blocco ORB di Chrome sulle immagini no-cors.
const WMS_COMMON = { format: 'image/jpeg', transparent: false, version: '1.1.1', maxZoom: 22, crossOrigin: 'anonymous' };

const baseLayerDefs = [
  {
    id: 'osm', name: 'OpenStreetMap', sub: 'Mappa stradale', badge: 'MAPPA',
    type: 'tile',
    make: (pane) => L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 22, maxNativeZoom: 19, pane, crossOrigin: 'anonymous',
      attribution: '© OpenStreetMap'
    })
  },
  {
    id: 'opentopo', name: 'OpenTopoMap', sub: 'Topografica / curve di livello', badge: 'TOPO',
    type: 'tile',
    make: (pane) => L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      maxZoom: 22, maxNativeZoom: 17, pane, subdomains: 'abc', crossOrigin: 'anonymous',
      attribution: '© OpenTopoMap (CC-BY-SA)'
    })
  },
  {
    id: 'orto2024', name: 'Ortofoto AGEA 2024', sub: 'Regione Piemonte', badge: '2024',
    type: 'wms',
    make: (pane) => L.tileLayer.wms('https://opengis.csi.it/mp/regp_agea_2024/service?', {
      layers: 'regp_agea_2024', pane, ...WMS_COMMON,
      attribution: 'Ortofoto AGEA 2024 · CSI Piemonte'
    })
  },
  {
    id: 'orto2021', name: 'Ortofoto AGEA 2021', sub: 'Regione Piemonte', badge: '2021',
    type: 'wms',
    make: (pane) => L.tileLayer.wms('https://opengis.csi.it/mp/regp_agea_2021/service?', {
      layers: 'regp_agea_2021', pane, ...WMS_COMMON,
      attribution: 'Ortofoto AGEA 2021 · CSI Piemonte'
    })
  },
  {
    id: 'orto1980', name: 'Ortofoto 1980-90', sub: 'Regione Piemonte (storica)', badge: "'80-90",
    type: 'wms',
    make: (pane) => L.tileLayer.wms('https://geomap.reteunitaria.piemonte.it/mapproxy/service?', {
      layers: 'regp_ortofoto_1980_90', pane, ...WMS_COMMON,
      attribution: 'Ortofoto 1980-90 · CSI Piemonte'
    })
  }
];

// Overlay georeferenziati (da overlays.js)
const overlayDefs = (window.OVERLAYS || []).map(o => ({
  id: o.id, name: o.name, sub: (o.zone ? o.zone + ' · ' : '') + 'immagine georef.',
  badge: 'FOTO', foto: true, type: 'image', bounds: o.bounds, center: o.center,
  make: (pane) => L.imageOverlay(o.file, o.bounds, { pane, interactive: false })
}));

// Definizione completa. L'ordine qui è l'ordine di DEFAULT dal BASSO verso l'ALTO.
const LAYER_DEFS = [...baseLayerDefs, ...overlayDefs];

/* Stato di default (visibilità + opacità) */
const DEFAULT_STATE = {};
LAYER_DEFS.forEach(d => {
  DEFAULT_STATE[d.id] = { visible: d.id === 'osm' || d.foto === true, opacity: 1 };
});
// Ordine di default (dal TOP della lista, cioè più in alto sulla mappa, verso il basso):
//   foto -> ortofoto recenti -> storiche -> topo -> osm
const DEFAULT_ORDER = [
  ...overlayDefs.map(d => d.id),
  'orto2024', 'orto2021', 'orto1980', 'opentopo', 'osm'
];

/* ============================================================
   Gestore livelli
   ============================================================ */
const STORAGE_KEY = 'nav_field_map_v1';
const layers = {};   // id -> { def, leaflet, pane, visible, opacity }
let order = [];      // array di id, index 0 = TOP (più in alto)

function loadPersisted() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null; }
  catch (e) { return null; }
}
function persist() {
  const state = {};
  order.forEach(id => { state[id] = { visible: layers[id].visible, opacity: layers[id].opacity }; });
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ order, state })); } catch (e) {}
}

function initLayers() {
  const saved = loadPersisted();
  // ordine
  order = (saved && Array.isArray(saved.order)
    ? saved.order.filter(id => LAYER_DEFS.some(d => d.id === id))
    : DEFAULT_ORDER.slice());
  // aggiungi eventuali nuovi id non presenti nel salvataggio (in cima)
  LAYER_DEFS.forEach(d => { if (!order.includes(d.id)) order.unshift(d.id); });

  LAYER_DEFS.forEach(d => {
    const paneName = 'lyr-' + d.id;
    map.createPane(paneName);
    map.getPane(paneName).style.zIndex = 400;   // aggiornato da applyOrder()
    const st = (saved && saved.state && saved.state[d.id]) || DEFAULT_STATE[d.id];
    const leaflet = d.make(paneName);
    leaflet.setOpacity(st.opacity);
    layers[d.id] = { def: d, leaflet, pane: paneName, visible: !!st.visible, opacity: st.opacity };
    if (st.visible) leaflet.addTo(map);
  });
  applyOrder();
  buildList();
}

function applyOrder() {
  // order[0] = TOP  -> zIndex più alto (ma sotto ai marker/GPS a 600)
  const n = order.length;
  order.forEach((id, i) => {
    const z = 520 - i * 6;   // top ~520, scende; resta < 600 (pane marker)
    const pane = map.getPane(layers[id].pane);
    if (pane) pane.style.zIndex = z;
  });
  persist();
}

function setVisible(id, vis) {
  const L_ = layers[id];
  L_.visible = vis;
  if (vis) L_.leaflet.addTo(map); else map.removeLayer(L_.leaflet);
  persist();
  syncRow(id);
}
function setOpacity(id, op) {
  const L_ = layers[id];
  L_.opacity = op;
  L_.leaflet.setOpacity(op);
  persist();
}
function moveLayer(id, dir) {
  const i = order.indexOf(id);
  const j = i + dir;
  if (j < 0 || j >= order.length) return;
  order.splice(i, 1);
  order.splice(j, 0, id);
  applyOrder();
  buildList();
}
function reorderTo(id, targetId, after) {
  order = order.filter(x => x !== id);
  let idx = order.indexOf(targetId);
  if (after) idx += 1;
  order.splice(idx, 0, id);
  applyOrder();
  buildList();
}

/* ============================================================
   UI pannello livelli
   ============================================================ */
const layerList = document.getElementById('layerList');

function buildList() {
  layerList.innerHTML = '';
  order.forEach((id, i) => layerList.appendChild(makeRow(id, i)));
}

function makeRow(id, i) {
  const L_ = layers[id], d = L_.def;
  const li = document.createElement('li');
  li.className = 'layer' + (L_.visible ? '' : ' hiddenLayer');
  li.dataset.id = id;
  li.draggable = true;

  li.innerHTML = `
    <div class="layer-row">
      <span class="grip" title="Trascina">⋮⋮</span>
      <button class="eye ${L_.visible ? 'on' : ''}" aria-label="Mostra/nascondi">
        ${L_.visible ? eyeOpen() : eyeOff()}
      </button>
      <div class="layer-name">${d.name}<span class="sub">${d.sub || ''}</span></div>
      <span class="badge ${d.foto ? 'foto' : ''}">${d.badge || ''}</span>
      <div class="ord">
        <button class="up" ${i === 0 ? 'disabled' : ''} aria-label="Su">▲</button>
        <button class="down" ${i === order.length - 1 ? 'disabled' : ''} aria-label="Giù">▼</button>
      </div>
    </div>
    <div class="opacity-row">
      <input type="range" min="0" max="100" value="${Math.round(L_.opacity * 100)}" aria-label="Trasparenza ${d.name}">
      <span class="opacity-val">${Math.round(L_.opacity * 100)}%</span>
    </div>`;

  li.querySelector('.eye').addEventListener('click', () => setVisible(id, !L_.visible));
  li.querySelector('.up').addEventListener('click', () => moveLayer(id, -1));
  li.querySelector('.down').addEventListener('click', () => moveLayer(id, +1));
  const range = li.querySelector('input[type=range]');
  const valEl = li.querySelector('.opacity-val');
  range.addEventListener('input', () => {
    const op = range.value / 100;
    valEl.textContent = range.value + '%';
    setOpacity(id, op);
  });

  // Drag & drop (desktop + touch via draggable)
  li.addEventListener('dragstart', (e) => { li.classList.add('dragging'); e.dataTransfer.setData('text/plain', id); e.dataTransfer.effectAllowed = 'move'; });
  li.addEventListener('dragend', () => { li.classList.remove('dragging'); clearDropMarks(); });
  li.addEventListener('dragover', (e) => {
    e.preventDefault();
    const before = (e.clientY - li.getBoundingClientRect().top) < li.offsetHeight / 2;
    clearDropMarks();
    li.classList.add(before ? 'drop-before' : 'drop-after');
  });
  li.addEventListener('drop', (e) => {
    e.preventDefault();
    const dragged = e.dataTransfer.getData('text/plain');
    if (!dragged || dragged === id) return;
    const before = (e.clientY - li.getBoundingClientRect().top) < li.offsetHeight / 2;
    reorderTo(dragged, id, !before);
  });

  return li;
}
function clearDropMarks() {
  document.querySelectorAll('.drop-before,.drop-after').forEach(el => el.classList.remove('drop-before', 'drop-after'));
}
function syncRow(id) {
  const li = layerList.querySelector(`[data-id="${id}"]`);
  if (!li) return;
  const L_ = layers[id];
  li.classList.toggle('hiddenLayer', !L_.visible);
  const eye = li.querySelector('.eye');
  eye.classList.toggle('on', L_.visible);
  eye.innerHTML = L_.visible ? eyeOpen() : eyeOff();
}
function eyeOpen() { return '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>'; }
function eyeOff() { return '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.9 17.9A10.6 10.6 0 0 1 12 19c-7 0-11-7-11-7a19 19 0 0 1 5.1-5.9M9.9 4.2A10.6 10.6 0 0 1 12 4c7 0 11 7 11 7a19 19 0 0 1-2.2 3.1M1 1l22 22"/></svg>'; }

/* ============================================================
   Coordinate live (centro / mirino)
   ============================================================ */
const FORMATS = ['DD', 'DMS', 'UTM'];
let coordFmt = localStorage.getItem('nav_coordfmt') || 'DD';
const coordCenterVal = document.getElementById('coordCenterVal');
const coordCenterBlock = document.getElementById('coordCenter');

function pad(n, w = 2) { return String(Math.floor(n)).padStart(w, '0'); }
function toDMS(deg, isLat) {
  const hemi = isLat ? (deg >= 0 ? 'N' : 'S') : (deg >= 0 ? 'E' : 'O');
  const a = Math.abs(deg);
  const d = Math.floor(a);
  const mfull = (a - d) * 60;
  const m = Math.floor(mfull);
  const s = (mfull - m) * 60;
  return `${d}°${pad(m)}'${s.toFixed(1)}"${hemi}`;
}
function fmtCoord(lat, lng, fmt) {
  if (fmt === 'DMS') return `${toDMS(lat, true)} ${toDMS(lng, false)}`;
  if (fmt === 'UTM') {
    const [e, n] = proj4('EPSG:4326', 'EPSG:32632', [lng, lat]);
    return `32T  E ${Math.round(e)}  N ${Math.round(n)}`;
  }
  return `${lat.toFixed(5)}°  ${lng.toFixed(5)}°`;
}
function renderCenter() {
  const c = map.getCenter();
  coordCenterVal.textContent = fmtCoord(c.lat, c.lng, coordFmt);
}
function cycleFormat() {
  coordFmt = FORMATS[(FORMATS.indexOf(coordFmt) + 1) % FORMATS.length];
  localStorage.setItem('nav_coordfmt', coordFmt);
  renderCenter(); renderGpsChip();
  toast('Formato: ' + coordFmt);
}
coordCenterBlock.addEventListener('click', cycleFormat);
coordCenterBlock.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') cycleFormat(); });
map.on('move', renderCenter);

/* ============================================================
   GPS
   ============================================================ */
const gpsChip = document.getElementById('gpsChip');
const gpsChipText = document.getElementById('gpsChipText');
const btnLocate = document.getElementById('btnLocate');
let watchId = null, gpsMarker = null, gpsCircle = null, follow = false, lastFix = null;

function renderGpsChip() {
  if (!lastFix) return;
  const acc = lastFix.accuracy;
  gpsChipText.textContent = `±${acc < 10 ? acc.toFixed(1) : Math.round(acc)} m`;
}

function makeGpsIcon() {
  return L.divIcon({ className: '', html: '<div class="gps-marker"></div>', iconSize: [20, 20], iconAnchor: [10, 10] });
}

function onGps(pos) {
  const { latitude: lat, longitude: lng, accuracy } = pos.coords;
  lastFix = pos.coords;
  const ll = [lat, lng];
  if (!gpsMarker) {
    gpsCircle = L.circle(ll, { radius: accuracy, pane: 'gpsPane', color: '#38e0a6', weight: 1, fillColor: '#38e0a6', fillOpacity: 0.12, interactive: false }).addTo(map);
    gpsMarker = L.marker(ll, { icon: makeGpsIcon(), pane: 'gpsPane', interactive: false, keyboard: false, zIndexOffset: 1000 }).addTo(map);
  } else {
    gpsMarker.setLatLng(ll);
    gpsCircle.setLatLng(ll).setRadius(accuracy);
  }
  gpsChip.className = 'gps-chip on';
  renderGpsChip();
  if (follow) map.panTo(ll, { animate: true });
}

function onGpsError(err) {
  gpsChip.className = 'gps-chip err';
  let msg = 'GPS non disponibile';
  if (err.code === 1) msg = 'Permesso GPS negato';
  else if (err.code === 2) msg = 'Posizione non disponibile';
  else if (err.code === 3) msg = 'GPS: timeout';
  gpsChipText.textContent = msg;
  btnLocate.classList.remove('tracking');
  btnLocate.classList.add('err');
  if (!window.isSecureContext) toast('Il GPS richiede HTTPS o localhost.');
  else toast(msg);
}

function startGps() {
  if (!('geolocation' in navigator)) { toast('Geolocalizzazione non supportata'); return; }
  gpsChip.className = 'gps-chip on';
  gpsChipText.textContent = 'ricerca…';
  btnLocate.classList.remove('err');
  btnLocate.classList.add('tracking');
  follow = true;
  if (watchId === null) {
    watchId = navigator.geolocation.watchPosition(onGps, onGpsError, {
      enableHighAccuracy: true, maximumAge: 1000, timeout: 20000
    });
  }
  if (lastFix) { map.setView([lastFix.latitude, lastFix.longitude], Math.max(map.getZoom(), 17)); }
}
function toggleFollow() {
  if (watchId === null) { startGps(); return; }
  follow = !follow;
  btnLocate.classList.toggle('tracking', follow);
  if (follow && lastFix) map.panTo([lastFix.latitude, lastFix.longitude]);
  toast(follow ? 'Inseguimento GPS attivo' : 'Inseguimento in pausa');
}
btnLocate.addEventListener('click', toggleFollow);
// se l'utente trascina la mappa, sospendi l'inseguimento
map.on('dragstart', () => { if (follow) { follow = false; btnLocate.classList.remove('tracking'); } });

/* ============================================================
   Pannello: apri/chiudi + azioni
   ============================================================ */
const panel = document.getElementById('panel');
const btnLayers = document.getElementById('btnLayers');
document.getElementById('btnLayers').addEventListener('click', () => togglePanel());
document.getElementById('btnClosePanel').addEventListener('click', () => togglePanel(false));
function togglePanel(force) {
  const show = force === undefined ? panel.classList.contains('hidden') : force;
  panel.classList.toggle('hidden', !show);
  panel.setAttribute('aria-hidden', String(!show));
}

document.getElementById('btnFit').addEventListener('click', () => {
  const b = L.latLngBounds([]);
  overlayDefs.forEach(d => b.extend(L.latLngBounds(d.bounds)));
  if (b.isValid()) { map.fitBounds(b.pad(0.15)); toast('Inquadrate ' + overlayDefs.length + ' immagini'); }
});
document.getElementById('btnReset').addEventListener('click', () => {
  localStorage.removeItem(STORAGE_KEY);
  location.reload();
});

/* ============================================================
   Toast
   ============================================================ */
const toastEl = document.getElementById('toast');
let toastT = null;
function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.remove('hidden');
  clearTimeout(toastT);
  toastT = setTimeout(() => toastEl.classList.add('hidden'), 2600);
}

/* ============================================================
   Avvio
   ============================================================ */
initLayers();
renderCenter();
// inquadra le foto all'avvio se ce ne sono
(function initView() {
  const b = L.latLngBounds([]);
  overlayDefs.forEach(d => b.extend(L.latLngBounds(d.bounds)));
  if (b.isValid()) map.fitBounds(b.pad(0.4));
})();
