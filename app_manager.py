#!/usr/bin/env python3
import json, os, re, signal, subprocess, sys
from http.server import HTTPServer, BaseHTTPRequestHandler


def html_escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')


PORT = 8080

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>App Killer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#fff;color:#1d1d1f;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{max-width:400px;width:90%;text-align:center;padding:40px 32px}
.card h1{font-size:22px;font-weight:600;margin-bottom:8px}
.card p{font-size:14px;color:#86868b;margin-bottom:28px;line-height:1.4}
.app-info{background:#f5f5f7;border-radius:16px;padding:28px 24px;margin-bottom:24px;min-height:160px;display:flex;flex-direction:column;align-items:center;justify-content:center;transition:opacity .3s}
.app-info .icon{width:56px;height:56px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:600;color:#fff;margin-bottom:12px}
.app-info .name{font-size:17px;font-weight:580}
.app-info .pkg{font-size:12px;color:#86868b;font-family:SFMono-Regular,Consolas,monospace;margin-top:4px;word-break:break-all}
.app-info .meta{font-size:12px;color:#86868b;margin-top:8px;display:flex;gap:10px}
.app-info .meta span{background:#e8e8ed;padding:2px 10px;border-radius:4px;font-size:11px}
.app-info.empty{min-height:auto;padding:40px}
.app-info.empty .icon{background:#e8e8ed!important;color:#86868b;font-size:32px}
.app-info.loading{opacity:.4}
.btn{display:inline-flex;align-items:center;gap:6px;padding:12px 32px;border-radius:12px;border:none;font-size:15px;font-weight:500;cursor:pointer;transition:all .2s;width:100%;justify-content:center}
.btn-primary{background:#007aff;color:#fff}
.btn-primary:hover{background:#0066d6}
.btn-primary:disabled{opacity:.4;cursor:not-allowed}
.btn-danger{background:#ff3b30;color:#fff}
.btn-danger:hover{background:#d62d20}
.btn-danger:disabled{opacity:.4;cursor:not-allowed}
.btn-secondary{background:#f5f5f7;color:#1d1d1f}
.btn-secondary:hover{background:#e8e8ed}
.toast{position:fixed;bottom:30px;left:50%;transform:translateX(-50%) translateY(80px);background:#1d1d1f;color:#fff;padding:12px 24px;border-radius:12px;font-size:13px;opacity:0;transition:all .4s;pointer-events:none;white-space:nowrap}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast.ok{background:#34c759}
.toast.err{background:#ff3b30}
.hidden{display:none}
</style>
</head>
<body>
<div class="card">
  <h1>App Killer</h1>
  <p>La app que está abierta en tu teléfono<br>aparece acá. Desinstalala con un clic.</p>
  <div class="app-info" id="appInfo">
    <div class="loading">Esperando app...</div>
  </div>
  <button class="btn btn-danger hidden" id="btnUninstall">Desinstalar</button>
  <button class="btn btn-secondary" id="btnRefresh" style="margin-top:10px">↻ Refrescar</button>
</div>
<div class="toast" id="toast"></div>

<script>
const $=id=>document.getElementById(id);
const info=$('appInfo');
const btn=$('btnUninstall');
const toast=$('toast');
let currentPkg=null;

function showToast(type,msg){
  toast.className='toast '+type+' show';
  toast.textContent=msg;
  clearTimeout(toast._t);
  toast._t=setTimeout(()=>toast.classList.remove('show'),3200);
}

async function load(){
  info.className='app-info loading';
  btn.classList.add('hidden');
  currentPkg=null;
  try{
    const r=await fetch('/api/foreground');
    const d=await r.json();
    if(d.error){info.innerHTML='<div class="icon" style="background:#e8e8ed;color:#86868b;font-size:32px">!</div><p style="color:#86868b;margin-top:8px;font-size:13px">'+d.error+'</p>';return}
    render(d);
  }catch(e){
    info.innerHTML='<div class="icon" style="background:#e8e8ed;color:#86868b;font-size:32px">✕</div><p style="color:#86868b;margin-top:8px;font-size:13px">Error de conexión</p>';
  }
}

function render(d){
  currentPkg=d.packageName;
  const initial=(d.appName||d.packageName).charAt(0).toUpperCase();
  const colors=['#007aff','#34c759','#ff9500','#ff3b30','#af52de','#5856d6','#ff2d55','#00c7be'];
  const ci=Math.abs(d.packageName.split('').reduce((s,c)=>s+c.charCodeAt(0),0))%colors.length;
  info.className='app-info';
  info.innerHTML=
    '<div class="icon" style="background:'+colors[ci]+'">'+initial+'</div>'+
    '<div class="name">'+(d.appName||d.packageName)+'</div>'+
    '<div class="pkg">'+d.packageName+'</div>'+
    '<div class="meta">'+
      (d.version?'<span>v'+d.version+'</span>':'')+
      (d.isSystem?'<span>Sistema</span>':'<span>Usuario</span>')+
    '</div>';
  btn.classList.remove('hidden');
  btn.textContent='Desinstalar';
  btn.disabled=false;
  btn.onclick=()=>uninstall(d.packageName, d.isSystem);
}

async function uninstall(pkg, isSystem){
  btn.disabled=true;
  btn.textContent='Desinstalando...';
  try{
    const r=await fetch('/api/uninstall',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({packageName:pkg,isSystem:isSystem})});
    const d=await r.json();
    if(d.success){
      showToast('ok','Desinstalada correctamente');
      info.innerHTML='<div class="icon" style="background:#34c759;font-size:32px">✓</div><p style="color:#86868b;margin-top:8px;font-size:13px">App eliminada</p>';
      btn.classList.add('hidden');
    }else{
      showToast('err','Error: '+(d.error||'desconocido'));
      btn.disabled=false;
      btn.textContent='Desinstalar';
    }
  }catch(e){
    showToast('err','Error de conexión');
    btn.disabled=false;
    btn.textContent='Desinstalar';
  }
}

$('btnRefresh').onclick=load;
load();
setInterval(load,5000);
</script>
</body>
</html>
"""


def adb(*args, timeout=15):
    cmd = ['adb'] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or f'exit code {r.returncode}')
        return r.stdout
    except FileNotFoundError:
        raise RuntimeError('adb no encontrado en PATH')


def get_foreground_app():
    """Get the currently foreground app from the device."""
    # Method 1: dumpsys window (works on most devices)
    try:
        out = adb('shell', 'dumpsys', 'window', 'windows', timeout=10)
        for line in out.split('\n'):
            line = line.strip()
            if 'mCurrentFocus' in line or 'mFocusedApp' in line or 'mInputMethod' in line:
                m = re.search(r'([a-zA-Z][\w.]+\.[\w.]+)/', line)
                if m:
                    pkg = m.group(1)
                    if not pkg.startswith('com.android.systemui'):
                        return pkg
    except RuntimeError:
        pass

    # Method 2: dumpsys activity
    try:
        out = adb('shell', 'dumpsys', 'activity', 'activities', timeout=10)
        for line in out.split('\n'):
            if 'ResumedActivity:' in line or 'mFocusedApp=' in line:
                m = re.search(r'([a-zA-Z][\w.]+\.[\w.]+)/', line)
                if m:
                    pkg = m.group(1)
                    if not pkg.startswith('com.android.systemui'):
                        return pkg
    except RuntimeError:
        pass

    raise RuntimeError('No se detectó ninguna app en primer plano. Abrí una app en tu teléfono.')


_SYSTEM_PACKAGES = None


def _load_system_packages():
    global _SYSTEM_PACKAGES
    if _SYSTEM_PACKAGES is None:
        try:
            out = adb('shell', 'pm', 'list', 'packages', '-s', timeout=10)
            _SYSTEM_PACKAGES = set(
                line.replace('package:', '').strip()
                for line in out.split('\n')
                if line.startswith('package:')
            )
        except RuntimeError:
            _SYSTEM_PACKAGES = set()
    return _SYSTEM_PACKAGES


def get_app_info(pkg):
    """Get version, label and system/user status for a package."""
    info = {'packageName': pkg, 'appName': html_escape(pkg), 'version': None,
            'isSystem': pkg in _load_system_packages()}
    try:
        out = adb('shell', 'dumpsys', 'package', pkg, timeout=10)
        vm = re.search(r'versionName=(\S+)', out)
        if vm:
            info['version'] = vm.group(1).strip()
        lm = re.search(r'ApplicationInfo\{[^}]*?\blabel=([^\s,}]+)', out)
        if lm:
            info['appName'] = html_escape(lm.group(1))
    except RuntimeError:
        pass
    return info


def uninstall_pkg(pkg, is_system):
    try:
        if is_system:
            adb('shell', 'pm', 'uninstall', '--user', '0', pkg, timeout=20)
        else:
            adb('uninstall', pkg, timeout=20)
        return True, None
    except RuntimeError as e:
        err = str(e).strip()
        if 'DELETE_FAILED' in err:
            err = 'No se pudo eliminar. App protegida por el sistema.'
        elif 'not installed for' in err.lower():
            err = 'La app ya no está instalada.'
        return False, err


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/uninstall':
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            pkg = data.get('packageName', '')
            is_sys = data.get('isSystem', False)
            ok, err = uninstall_pkg(pkg, is_sys)
            self.json({'success': ok, 'error': err, 'packageName': pkg})
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/api/foreground':
            try:
                pkg = get_foreground_app()
                info = get_app_info(pkg)
                self.json(info)
            except RuntimeError as e:
                self.json({'error': str(e)})
        elif self.path in ('/favicon.ico',):
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode())

    def json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, fmt, *args):
        if ' 400' in args[0] or ' 500' in args[0]:
            super().log_message(fmt, *args)


def main():
    try:
        adb('get-state', timeout=5)
    except RuntimeError as e:
        print(' ADB:', e)
        sys.exit(1)

    devices = adb('devices', timeout=5)
    connected = [l.split('\t') for l in devices.strip().split('\n')[1:] if '\tdevice' in l]
    if not connected:
        print(' No hay dispositivos conectados.')
        sys.exit(1)

    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f' Abre http://localhost:{PORT} en tu navegador')
    print(' Abrí una app en tu teléfono y aparecerá en la web.')

    def shutdown(sig, frame):
        print('\n Deteniendo...')
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    server.serve_forever()


if __name__ == '__main__':
    main()
