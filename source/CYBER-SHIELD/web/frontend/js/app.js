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

async function checkLicense() {
  try {
    const data = await api('/api/license/status');
    if (data.valid) {
      document.getElementById('licenseOverlay').style.display = 'none';
      document.getElementById('dashboard').style.display = 'block';
      document.getElementById('licenseBadge').textContent = '🔑 ' + data.message;
      loadAll();
      setInterval(loadAll, 10000);
    } else {
      document.getElementById('licenseOverlay').style.display = 'flex';
      document.getElementById('dashboard').style.display = 'none';
    }
  } catch(e) {
    document.getElementById('licenseOverlay').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
  }
}

async function activateLicense(e) {
  e.preventDefault();
  const key = document.getElementById('licenseKey').value.trim();
  const btn = document.getElementById('activateBtn');
  const err = document.getElementById('licenseError');
  btn.disabled = true;
  btn.textContent = 'جاري التحقق...';
  err.textContent = '';
  try {
    const data = await api('/api/license/activate', 'POST', {key});
    if (data.success) {
      document.getElementById('licenseOverlay').style.display = 'none';
      document.getElementById('dashboard').style.display = 'block';
      document.getElementById('licenseBadge').textContent = '🔑 ' + data.message;
      loadAll();
      setInterval(loadAll, 10000);
    } else {
      err.textContent = data.error || 'خطأ في التفعيل';
    }
  } catch(e) {
    err.textContent = 'تعذر الاتصال بالخادم';
  }
  btn.disabled = false;
  btn.textContent = 'تفعيل الترخيص';
  return false;
}

async function runWiFi() {
  showResult('جاري فحص شبكات WiFi...');
  const data = await api('/api/wifi/scan');
  const networks = data.networks || [];
  if (networks.length === 0) {
    showResult('لا توجد شبكات WiFi متاحة');
    return;
  }
  let text = `عدد الشبكات: ${networks.length}\n${'='.repeat(50)}\n`;
  networks.forEach((n, i) => {
    text += `\n[${i+1}] ${n.ssid || '—'}\n`;
    text += `    BSSID: ${n.bssid || '—'}\n`;
    text += `    Signal: ${n.signal || '—'}\n`;
    text += `    Channel: ${n.channel || '—'}\n`;
    text += `    Auth: ${n.auth || '—'}\n`;
    text += `    Encryption: ${n.encryption || '—'}\n`;
  });
  showResult(text);
}

async function runARP() {
  const data = await api('/api/arp/check');
  const el = document.getElementById('arpList');
  const allAlerts = [...(data.alerts || []), ...(data.spoof || [])];
  if (!allAlerts.length) {
    el.innerHTML = '<div style="padding:30px;text-align:center;color:#00f5a0">✅ لا توجد هجمات ARP Spoofing</div>';
    return;
  }
  el.innerHTML = allAlerts.map(a => `<div class="arp-item">
    <span class="sev critical"></span>
    <span class="ip">${escape(a.ip)}</span>
    <span class="macs">${escape((a.macs||[]).join(', '))}</span>
    <span class="time">${a.time || '—'}</span>
  </div>`).join('');
}

async function startARPWatch() {
  await api('/api/arp/start', 'POST');
  showResult('✅ بدء مراقبة ARP');
}

async function stopARPWatch() {
  await api('/api/arp/stop', 'POST');
  showResult('⏹️ إيقاف مراقبة ARP');
}

checkLicense();
