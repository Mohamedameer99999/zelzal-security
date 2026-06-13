const API = '';
async function api(path, method='GET', body=null) {
  const opts = {method, headers:{'Content-Type':'application/json'}};
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  return r.json();
}

function escape(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

function fmtTime(ts) {
  if (!ts || ts === '-') return '-';
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString('ar-EG', {hour:'2-digit',minute:'2-digit'});
  } catch { return ts; }
}

async function runScan() {
  showResult('جاري فحص الشبكة...');
  const data = await api('/api/scan/network');
  showResult(JSON.stringify(data, null, 2));
  await loadAll();
}

async function runIDS() {
  showResult('جاري فحص IDS...');
  const data = await api('/api/ids');
  showResult(JSON.stringify(data, null, 2));
}

async function runUSB() {
  showResult('جاري فحص USB...');
  const data = await api('/api/usb');
  showResult(JSON.stringify(data, null, 2));
}

async function runAV() {
  showResult('جاري فحص الملفات...');
  const data = await api('/api/antivirus/scan');
  showResult(JSON.stringify(data, null, 2));
}

async function runKL() {
  showResult('جاري فحص Keylogger...');
  const data = await api('/api/keylogger');
  showResult(JSON.stringify(data, null, 2));
}

function showResult(text) {
  const panel = document.getElementById('resultPanel');
  const content = document.getElementById('resultContent');
  panel.style.display = 'block';
  content.textContent = text;
}

async function loadAlerts() {
  const alerts = await api('/api/alerts');
  const el = document.getElementById('alertsList');
  if (!alerts.length) {
    el.innerHTML = '<div style="padding:30px;text-align:center;color:#555">لا توجد تنبيهات</div>';
    return;
  }
  el.innerHTML = alerts.map(a => `<div class="alert-item">
    <span class="sev ${a.severity}"></span>
    <span class="msg">${escape(a.message)}</span>
    <span class="time">${fmtTime(a.timestamp)}</span>
  </div>`).join('');
  document.getElementById('statAlerts').textContent = alerts.length;
}

async function loadDevices() {
  const devs = await api('/api/devices');
  const tbody = document.getElementById('devicesBody');
  tbody.innerHTML = devs.map(d => `<tr>
    <td>${escape(d.ip)}</td>
    <td style="direction:ltr;font-size:0.8em">${escape(d.mac || '—')}</td>
    <td>${escape(d.hostname || '—')}</td>
    <td>${escape(d.vendor || '—')}</td>
    <td><span class="badge" style="color:${d.status==='online'?'#00f5a0':'#ff4444'}">${d.status === 'online' ? '🟢 متصل' : '🔴 غير متصل'}</span></td>
  </tr>`).join('');
  document.getElementById('statDevices').textContent = devs.length;
}

async function loadAll() {
  try {
    const status = await api('/api/status');
    document.getElementById('statThreats').textContent = status.stats?.unread_alerts || 0;
    await Promise.all([loadAlerts(), loadDevices()]);
  } catch(e) {
    console.error(e);
  }
}

loadAll();
setInterval(loadAll, 10000);
