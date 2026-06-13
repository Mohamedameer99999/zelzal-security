const API = '';

async function api(path, method='GET', body=null) {
  const opts = {method, headers:{'Content-Type':'application/json'}};
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  return r.json();
}

function fmtSize(b) {
  if (!b) return '0';
  const mb = b / (1024*1024);
  return mb < 1 ? b/1024 < 1 ? b+' B' : (b/1024).toFixed(1)+' KB' : mb.toFixed(1)+' MB';
}

function fmtTime(ts) {
  if (!ts || ts === '-') return '-';
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString('ar-EG', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  } catch { return ts; }
}

function escape(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

function drawLineChart(canvas, data, color, label) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width = canvas.offsetWidth * 2;
  const H = canvas.height = 200 * 2;
  ctx.scale(1, 1);
  const pad = {t:20,r:20,b:30,l:40};
  const w = W - pad.l - pad.r;
  const h = H - pad.t - pad.b;
  ctx.clearRect(0,0,W,H);
  if (!data || data.length < 2) {
    ctx.fillStyle = '#555';
    ctx.font = '24px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('في انتظار البيانات...', W/2, H/2);
    return;
  }
  const max = Math.max(...data, 1);
  const min = 0;
  const range = max - min || 1;
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.shadowColor = color;
  ctx.shadowBlur = 10;
  ctx.beginPath();
  data.forEach((v, i) => {
    const x = pad.l + (i / (data.length-1)) * w;
    const y = pad.t + h - ((v - min) / range) * h;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.shadowBlur = 0;
  // fill
  ctx.lineTo(pad.l + w, pad.t + h);
  ctx.lineTo(pad.l, pad.t + h);
  ctx.closePath();
  const g = ctx.createLinearGradient(0, pad.t, 0, pad.t + h);
  g.addColorStop(0, color + '40');
  g.addColorStop(1, color + '00');
  ctx.fillStyle = g;
  ctx.fill();
  // labels
  ctx.fillStyle = '#555';
  ctx.font = '20px sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText((max).toFixed(1), pad.l, pad.t - 8);
  ctx.fillText('0', pad.l, pad.t + h + 5);
  ctx.textAlign = 'center';
  ctx.fillText('الآن', pad.l + w, pad.t + h + 28);
  if (data.length > 2) {
    const mid = Math.floor(data.length/2);
    ctx.fillStyle = '#444';
    ctx.font = '18px sans-serif';
    ctx.fillText('-' + Math.round(data.length * (30/data.length)) + 'د', pad.l + (mid/data.length)*w, pad.t + h + 28);
  }
}

// STATE
let devices = [];
let alerts = [];
let bwHistory = [];
let netHistory = [];
let bwCanvas, histCanvas;

function renderDevices() {
  const tbody = document.getElementById('devicesBody');
  tbody.innerHTML = devices.map(d => `<tr>
    <td>${escape(d.ip)}</td>
    <td style="direction:ltr;font-size:0.8em">${escape(d.mac || '—')}</td>
    <td>${escape(d.hostname || '—')}</td>
    <td>${escape(d.vendor || '—')}</td>
    <td>${fmtTime(d.last_seen)}</td>
    <td><span class="badge ${d.status}">${d.status === 'online' ? '🟢 متصل' : '🔴 غير متصل'}</span></td>
  </tr>`).join('');
}

function renderAlerts() {
  const el = document.getElementById('alertsList');
  if (!alerts.length) {
    el.innerHTML = '<div style="padding:30px;text-align:center;color:#555">لا توجد تنبيهات</div>';
    return;
  }
  el.innerHTML = alerts.map(a => `<div class="alert-item">
    <span class="sev ${a.severity}"></span>
    <span class="msg">${escape(a.message)}</span>
    <span class="time">${fmtTime(a.timestamp)}</span>
    ${a.acknowledged ? '' : `<button class="ack-btn" onclick="ackAlert(${a.id})">✓</button>`}
  </div>`).join('');
}

function renderBWChart() {
  if (!bwCanvas) bwCanvas = document.getElementById('bwChart');
  const vals = bwHistory.map(h => (h.recv_speed || 0) / (1024*1024) * 8);
  drawLineChart(bwCanvas, vals, '#00f5a0', 'Mbps');
}

function renderHistoryChart() {
  if (!histCanvas) histCanvas = document.getElementById('historyChart');
  const vals = netHistory.map(h => h.online_devices || 0);
  drawLineChart(histCanvas, vals, '#00d9f5', 'الأجهزة');
}

function renderStats() {
  const online = devices.filter(d => d.status === 'online').length;
  const status = document.getElementById('navStatus');
  status.className = 'status-dot ' + (online > 0 ? 'green' : 'red');
  document.getElementById('navDevices').textContent = devices.length + ' أجهزة';
  document.getElementById('statDevices').textContent = devices.length;
  document.getElementById('statOnline').textContent = online;
  document.getElementById('statAlerts').textContent = alerts.filter(a => !a.acknowledged).length;
}

async function ackAlert(id) {
  await api('/api/ack-alert', 'POST', {id});
  await loadAlerts();
}

async function loadAll() {
  try {
    const [status, devs, alrts, bw, net] = await Promise.all([
      api('/api/status'),
      api('/api/devices'),
      api('/api/alerts'),
      api('/api/bandwidth'),
      api('/api/network-history'),
    ]);
    devices = devs;
    alerts = alrts;
    bwHistory = bw;
    netHistory = net;
    document.getElementById('navUptime').textContent = status.scans?.last_scan !== '-' ? 'آخر فحص: ' + fmtTime(status.scans?.last_scan) : 'جاري البدء...';
    document.getElementById('statSpeed').textContent = status.bandwidth?.current_mbps?.toFixed(1) || '0';
    document.getElementById('statSent').textContent = status.bandwidth?.sent_mb || '0';
    document.getElementById('statRecv').textContent = status.bandwidth?.recv_mb || '0';
    renderStats();
    renderDevices();
    renderAlerts();
    renderBWChart();
    renderHistoryChart();
  } catch (e) {
    console.error('Load error:', e);
  }
}

// LICENSE
async function checkLicense() {
  try {
    const data = await api('/api/license/status');
    const overlay = document.getElementById('licenseOverlay');
    const badge = document.getElementById('licenseBadge');
    const infoEl = document.getElementById('licenseInfo');
    if (data.valid) {
      overlay.style.display = 'none';
      badge.style.display = 'inline';
      infoEl.innerHTML = `<span style="color:#00f5a0">✅ ${data.message}</span>`;
    } else {
      overlay.style.display = 'flex';
      badge.style.display = 'none';
      infoEl.innerHTML = `<span style="color:#ff4444">❌ ${data.message}</span>`;
    }
  } catch (e) {
    console.error('License check error:', e);
  }
}

async function activateLicense(key) {
  const msgEl = document.getElementById('licenseMsg');
  msgEl.style.display = 'none';
  try {
    const data = await api('/api/license/activate', 'POST', {key});
    msgEl.style.display = 'block';
    if (data.success) {
      msgEl.style.color = '#00f5a0';
      msgEl.textContent = '✅ ' + (data.message || 'تم التفعيل بنجاح');
      setTimeout(checkLicense, 1000);
    } else {
      msgEl.style.color = '#ff4444';
      msgEl.textContent = '❌ ' + (data.message || 'فشل التفعيل');
    }
  } catch (e) {
    msgEl.style.display = 'block';
    msgEl.style.color = '#ff4444';
    msgEl.textContent = '❌ تعذر الاتصال بالخادم';
  }
}

// ARP
async function loadArpAlerts() {
  try {
    const alerts = await api('/api/arp/check');
    const tbody = document.getElementById('arpBody');
    if (!alerts || !alerts.length) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#555;padding:20px">لا توجد إنذارات ARP</td></tr>';
      return;
    }
    tbody.innerHTML = alerts.map(a => `<tr>
      <td>${escape(a.ip)}</td>
      <td style="direction:ltr;font-size:0.8em">${escape(a.macs ? a.macs.join(', ') : '—')}</td>
      <td><span class="badge warning">${escape(a.type)}</span></td>
      <td>${escape(a.time || '—')}</td>
    </tr>`).join('');
  } catch (e) {
    console.error('ARP load error:', e);
  }
}

// POLL
checkLicense();
loadAll();
loadArpAlerts();
setInterval(loadAll, 5000);
setInterval(loadArpAlerts, 10000);
