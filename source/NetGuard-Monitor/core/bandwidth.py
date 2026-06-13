import psutil, time, threading
from datetime import datetime

_prev_net = None
_prev_time = None
_bandwidth_data = {'current_speed': 0, 'total_sent': 0, 'total_recv': 0, 'history': []}

def _measure():
    global _prev_net, _prev_time
    net = psutil.net_io_counters()
    now = time.time()
    if _prev_net is not None and _prev_time is not None:
        delta = now - _prev_time
        if delta > 0:
            sent_speed = (net.bytes_sent - _prev_net.bytes_sent) / delta
            recv_speed = (net.bytes_recv - _prev_net.bytes_recv) / delta
            _bandwidth_data['current_speed'] = recv_speed + sent_speed
            _bandwidth_data['total_sent'] = net.bytes_sent
            _bandwidth_data['total_recv'] = net.bytes_recv
            _bandwidth_data['history'].append({
                'timestamp': datetime.now().isoformat(),
                'sent_speed': sent_speed,
                'recv_speed': recv_speed,
                'total_sent': net.bytes_sent,
                'total_recv': net.bytes_recv,
            })
            if len(_bandwidth_data['history']) > 720:
                _bandwidth_data['history'] = _bandwidth_data['history'][-720:]
    _prev_net = net
    _prev_time = now

def get_bandwidth():
    _measure()
    return {
        'current_speed': round(_bandwidth_data['current_speed'], 2),
        'total_sent': _bandwidth_data['total_sent'],
        'total_recv': _bandwidth_data['total_recv'],
        'sent_mb': round(_bandwidth_data['total_sent'] / (1024*1024), 2),
        'recv_mb': round(_bandwidth_data['total_recv'] / (1024*1024), 2),
        'current_mbps': round(_bandwidth_data['current_speed'] * 8 / (1024*1024), 2),
    }

def get_history(minutes=30):
    if not _bandwidth_data['history']:
        return []
    cutoff = (datetime.now().timestamp() - minutes * 60)
    return [h for h in _bandwidth_data['history'] if datetime.fromisoformat(h['timestamp']).timestamp() > cutoff]

def start_monitoring(interval=2):
    def _loop():
        while True:
            try:
                _measure()
            except:
                pass
            time.sleep(interval)
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
