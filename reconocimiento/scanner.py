import threading
import time
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange

_discovered = []
_lock = threading.Lock()

def _on_service_state_change(zeroconf, service_type, name, state_change):
    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        if info and info.addresses:
            ip = '.'.join(str(b) for b in info.addresses[0])
            port = info.port
            entry = {'name': name, 'ip': ip, 'port': port}
            with _lock:
                if entry not in _discovered:
                    _discovered.append(entry)

def start_mdns_scanner():
    zc = Zeroconf()
    ServiceBrowser(zc, "_http._tcp.local.", handlers=[_on_service_state_change])
    try:
        while True:
            time.sleep(0.1)
    finally:
        zc.close()

threading.Thread(target=start_mdns_scanner, daemon=True).start()

def get_discovered_cams():
    with _lock:
        return list(_discovered)