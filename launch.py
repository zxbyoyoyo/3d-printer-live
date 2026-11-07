"""Avatar printer: Chrome on macOS/Linux, WebView2 desktop on Windows."""
import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from functools import partial
from scene_relay import SceneRelay
from urllib.parse import urlparse, parse_qs
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVER_PORTS = (8080, 8081, 8181, 8088, 8090, 8095, 8282, 8388)


def browser_candidates(platform=None):
    platform = platform or sys.platform
    if platform == 'darwin':
        return [str(base / app / 'Contents/MacOS' / exe)
                for base in (Path('/Applications'), Path.home() / 'Applications')
                for app, exe in (('Google Chrome.app', 'Google Chrome'),
                                 ('Microsoft Edge.app', 'Microsoft Edge'),
                                 ('Chromium.app', 'Chromium'))]
    if platform == 'win32':
        return [str(Path(base) / app) for base in
                (os.environ.get('PROGRAMFILES', r'C:\Program Files'),
                 os.environ.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)'),
                 os.environ.get('LOCALAPPDATA', '')) if base
                for app in ('Google/Chrome/Application/chrome.exe',
                            'Microsoft/Edge/Application/msedge.exe')]
    return [shutil.which(name) for name in ('google-chrome', 'chromium', 'chromium-browser') if shutil.which(name)]


def find_browser():
    override = os.environ.get('PRINTER_BROWSER')
    if override and Path(override).is_file():
        return override
    return next((p for p in browser_candidates() if Path(p).is_file()), None)


def process_options(platform=None):
    return {'creationflags': 0x08000000} if (platform or sys.platform) == 'win32' else {}


def open_browser(url, size=(1280, 720), debug=False):
    exe = find_browser()
    if not exe:
        return False
    args = [exe, '--app=' + url if sys.platform == 'win32' else '--new-window',
            '--window-size=%d,%d' % size]
    if debug:
        args += ['--remote-debugging-port=9223', '--remote-debugging-address=127.0.0.1',
                 '--user-data-dir=' + str(ROOT / '.bridge-profile'),
                 '--no-first-run', '--no-default-browser-check', '--lang=zh-CN']
    args += ['--disable-backgrounding-occluded-windows', '--disable-renderer-backgrounding',
             '--disable-background-timer-throttling', url]
    subprocess.Popen(args, **process_options())
    return True

def room_id(raw):
    match = re.fullmatch(r'(?:https?://live\.douyin\.com/)?(\d{5,25})(?:[/?#].*)?', str(raw).strip())
    if not match:
        raise ValueError('请输入有效的直播间号或直播链接')
    return match[1]

def listening(port):
    with socket.socket() as sock:
        sock.settimeout(.3)
        return sock.connect_ex(('127.0.0.1', port)) == 0

_LOCAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def local_get(url, timeout_s=1.5):
    # 本机健康检查必须直连：系统代理（Clash 等）会拦截 127.0.0.1 请求。
    return _LOCAL_OPENER.open(url, timeout=timeout_s)

def bridge_status():
    for port in range(8765, 8775):
        try:
            with local_get(f'http://127.0.0.1:{port}/health', 1.5) as response:
                data = json.load(response)
            if data.get('service') == 'avatar-printer' and os.path.normcase(data.get('identity', '')) == os.path.normcase(str(ROOT)):
                return dict(ok=True, port=port, url=f'ws://127.0.0.1:{port}')
        except Exception:
            pass
    return dict(ok=False)


def wait_bridge(process):
    for _ in range(30):
        if process.poll() is not None:
            raise RuntimeError('数据桥启动失败，请查看 desktop-bridge.log')
        status = bridge_status()
        if status['ok']:
            return status
        time.sleep(.1)
    raise RuntimeError('数据桥启动超时，请查看 desktop-bridge.log')


ACTIVE_PORT = 8080

def ensure_server():
    global ACTIVE_PORT
    # 8080 被代理等程序占用时自动换备用端口（8081/8181/8088）。
    for port in SERVER_PORTS:
        if not listening(port):
            ACTIVE_PORT = port
            break
        try:
            with local_get(f'http://127.0.0.1:{port}/', 3) as response:
                if 'AVATAR PRINT STUDIO' in response.read(100000).decode('utf-8', errors='replace'):
                    ACTIVE_PORT = port
                    return f'http://127.0.0.1:{port}/', None
        except Exception:
            pass
    else:
        raise RuntimeError('没有空闲的本机端口，请关闭旧头像打印程序后重试')
    relay = SceneRelay()
    bridge_process = None
    class Handler(SimpleHTTPRequestHandler):
        def end_headers(self):
            # Ctrl+R must load edited local pages and their scripts immediately.
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            super().end_headers()

        # 叠加一个本地控制端点：让浏览器页面也能拉起“独立应用窗口”（无浏览器界面）。
        def _guard(self):
            # 只允许本机页面调用（防其它网站借用本地服务拉进程）。
            if self.headers.get('Host', '') != '127.0.0.1:' + str(ACTIVE_PORT):
                return False
            return self.headers.get('Sec-Fetch-Site', '') == 'same-origin'

        def _spawn_app(self, url, size=(1280, 720), extra=None):
            return open_browser(url, size, debug=bool(extra))

        def do_POST(self):
            if self.path != '/__scene-message' or not self._guard():
                return self._json(403, '{"error":"forbidden"}')
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 65536:
                    raise ValueError('bad length')
                body = json.loads(self.rfile.read(length))
                relay.publish(body['client'], body['message'])
                return self._json(200, '{"ok":true}')
            except (ValueError, KeyError, TypeError):
                return self._json(400, '{"error":"invalid message"}')

        def do_GET(self):
            nonlocal bridge_process
            if self.path == '/__bridge-status':
                if not self._guard():
                    return self._json(403, '{"ok":false}')
                return self._json(200, json.dumps(bridge_status()))
            if self.path.startswith('/__scene-events?'):
                if not self._guard():
                    return self._json(403, '{"error":"forbidden"}')
                try:
                    query = parse_qs(urlparse(self.path).query)
                    client = query['client'][0]
                    after = int(query['after'][0]) if 'after' in query else None
                    return self._json(200, json.dumps(relay.poll(client, after)))
                except (ValueError, KeyError):
                    return self._json(400, '{"error":"invalid cursor"}')
            if self.path.startswith('/__open-live'):
                if not self._guard():
                    return self._json(403, '{"ok":false,"error":"forbidden"}')
                q = parse_qs(urlparse(self.path).query)
                room = ''.join(ch for ch in (q.get('room') or [''])[0] if ch.isdigit())[-25:]
                if not re.fullmatch(r'\d{5,25}', room):
                    return self._json(400, '{"ok":false,"error":"bad room"}')
                size = (720, 1280) if (q.get('portrait') or ['0'])[0] == '1' else (1280, 720)
                extra = (q.get('debug') or ['0'])[0] == '1'
                if not self._spawn_app('https://live.douyin.com/' + room, size, extra):
                    return self._json(500, '{"ok":false,"error":"no browser found"}')
                return self._json(200, '{"ok":true}')
            if self.path.startswith('/__start-bridge'):
                if not self._guard():
                    return self._json(403, '{"ok":false,"error":"forbidden"}')
                q = parse_qs(urlparse(self.path).query)
                room = ''.join(ch for ch in (q.get('room') or [''])[0] if ch.isdigit())[-25:]
                if not re.fullmatch(r'\d{5,25}', room):
                    try:
                        room = ''.join(ch for ch in (ROOT / '.bridge-room').read_text(encoding='utf-8') if ch.isdigit())[-25:]
                    except Exception:
                        room = ''
                if not re.fullmatch(r'\d{5,25}', room):
                    return self._json(400, '{"ok":false,"error":"no room"}')
                if bridge_status()["ok"]:
                    return self._json(200, '{"ok":true,"already":true}')
                node = shutil.which('node')
                if not node:
                    return self._json(500, '{"ok":false,"error":"node not found"}')
                (ROOT / '.bridge-room').write_text(room, encoding='utf-8')
                env = os.environ.copy()
                if listening(9224):
                    env['PRINTER_CDP_PORT'] = '9224'
                with open(ROOT / 'desktop-bridge.log', 'ab') as log:
                    bridge_process = subprocess.Popen([node, str(ROOT / 'douyin-bridge.mjs'), room], cwd=str(ROOT),
                                     env=env, stdout=log, stderr=log, **process_options())
                try:
                    return self._json(200, json.dumps(wait_bridge(bridge_process)))
                except RuntimeError as exc:
                    return self._json(500, json.dumps(dict(ok=False, error=str(exc))))
            if self.path.startswith('/__stop-bridge'):
                if not self._guard():
                    return self._json(403, '{"ok":false,"error":"forbidden"}')
                if bridge_process and bridge_process.poll() is None:
                    bridge_process.terminate()
                    bridge_process.wait(timeout=5)
                bridge_process = None
                return self._json(200, '{"ok":true}')
            if self.path.startswith('/__open-scene'):
                if not self._guard():
                    return self._json(403, '{"ok":false,"error":"forbidden"}')
                q = parse_qs(urlparse(self.path).query)
                spath = (q.get('path') or [''])[0]
                orient = (q.get('orient') or ['landscape'])[0]
                sizes = {'landscape': (1280, 720), 'landscape-1080p': (1920, 1080),
                         'portrait': (720, 1280), 'portrait-1080p': (1080, 1920)}
                w, h = sizes.get(orient, (1280, 720))
                if not re.fullmatch(r'/[A-Za-z0-9_\-]+\.html\?scene=1', spath):
                    return self._json(400, '{"ok":false,"error":"bad path"}')
                if not open_browser('http://127.0.0.1:' + str(ACTIVE_PORT) + spath, (w, h)):
                    return self._json(500, '{"ok":false,"error":"no browser found"}')
                return self._json(200, '{"ok":true}')
            # Ignore validators from versions cached before no-store was enabled.
            for header in ('If-Modified-Since', 'If-None-Match'):
                if header in self.headers:
                    del self.headers[header]
            return super().do_GET()

        def _json(self, code, body):
            data = body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    class PrinterServer(ThreadingHTTPServer):
        def server_close(self):
            nonlocal bridge_process
            if bridge_process and bridge_process.poll() is None:
                bridge_process.terminate()
                try:
                    bridge_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    bridge_process.kill()
                    bridge_process.wait()
            super().server_close()

    server = PrinterServer(('127.0.0.1', ACTIVE_PORT), partial(Handler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{ACTIVE_PORT}/', server

class DesktopApi:
    def __init__(self):
        self._live = None
        self._bridge = None
        self._room = None
        self._scene_windows = []
        self._scene_process = None
        self._lock = threading.RLock()
        self._restart_requested = False

    def restart_program(self):
        with self._lock:
            if self._restart_requested:
                return '正在重启…'
            self._restart_requested = True
        def shutdown():
            import webview
            for win in list(webview.windows)[::-1]:
                win.destroy()
        threading.Timer(0.5, shutdown).start()
        return '正在完整重启程序…'

    def get_capture_compatibility(self):
        return (ROOT / '.capture-compat').exists()

    def set_capture_compatibility(self, enabled):
        if not isinstance(enabled, bool):
            raise ValueError('无效的兼容模式设置')
        config = ROOT / '.capture-compat'
        if enabled:
            config.write_text('software-rendering', encoding='utf-8')
        else:
            config.unlink(missing_ok=True)
        return self.restart_program()

    def save_rules_png(self, data_url):
        import base64
        import webview
        if not isinstance(data_url, str) or not data_url.startswith('data:image/png;base64,') or len(data_url) > 20000000:
            raise ValueError('无效的 PNG 图片')
        data = base64.b64decode(data_url.split(',', 1)[1], validate=True)
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('无效的 PNG 图片')
        result = webview.windows[0].create_file_dialog(webview.FileDialog.SAVE,
            save_filename='直播打印规则.png', file_types=('PNG 图片 (*.png)',))
        if not result:
            return '已取消保存。'
        path = Path(result[0] if isinstance(result, (tuple, list)) else result)
        if path.suffix.lower() != '.png':
            path = path.with_suffix('.png')
        path.write_bytes(data)
        return '已保存 PNG：' + str(path)

    def open_scene_window(self, path=None, orient='landscape'):
        if orient not in {'landscape','landscape-1080p','portrait','portrait-1080p'}:
            orient = 'landscape'

        # A separate process prevents process-based capture from selecting the
        # control panel instead of the output window.
        if self._scene_process and self._scene_process.poll() is None:
            return '直播小窗已在独立进程运行，请从任务栏切换到直播小窗。'
        self._scene_process = subprocess.Popen(
            [sys.executable, str(ROOT / 'launch.py'), '--scene-view',
             '--scene-orient', orient], cwd=ROOT)
        return '已打开独立进程直播小窗，请重新选择捕获窗口。'


    def resize_scene(self, w, h):
        # 场景小窗内切换横竖屏：调整所有由本应用打开的场景窗口尺寸。
        try:
            w, h = max(200, min(int(w), 4096)), max(200, min(int(h), 4096))
        except Exception:
            return 'bad size'
        for win in list(self._scene_windows):
            try:
                if not getattr(win, 'closed', False):
                    win.resize(w, h)
            except Exception:
                pass
        return 'ok'

    def open_live_room(self, raw):
        with self._lock:
            room = room_id(raw)
            if self._live and self._live.poll() is None:
                if room == self._room:
                    return '直播窗口已打开，请切换登录 / Live window already open — switch to it and log in.'
                # 直接换房间：关掉旧窗口开新窗口；运行中的数据桥会自动跟随 .bridge-room 切换。
                try:
                    self._live.terminate()
                    self._live.wait(timeout=5)
                except Exception:
                    pass
                self._live = None
            if listening(9224):
                raise RuntimeError('端口 9224 被占用，请关闭旧直播窗口 / Port 9224 busy — close the old live window')
            self._room = room
            (ROOT / '.bridge-room').write_text(room, encoding='utf-8')
            env = os.environ.copy()
            env['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = '--remote-debugging-port=9224 --remote-debugging-address=127.0.0.1'
            self._live = subprocess.Popen([sys.executable, str(ROOT / 'launch.py'), '--live-room', room], cwd=ROOT, env=env)
            return '直播窗口已打开，登录后点“开始抓取” / Live window opened — log in, then click Start Capture.'

    def start_capture(self, raw):
        with self._lock:
            room = room_id(raw)
            if not self._live or self._live.poll() is not None or room != self._room:
                raise RuntimeError("请先打开该房间的直播窗口并登录 / Open this room's live window and log in first")
            if self._bridge and self._bridge.poll() is None:
                return '数据桥已在运行 / Bridge already running.'
            if bridge_status()["ok"]:
                return '数据桥已在运行，自动跟随换房 / Bridge running — follows room switches automatically.'
            with urllib.request.urlopen('http://127.0.0.1:9224/json/list', timeout=3) as response:
                pages = json.load(response)
            if not any(re.match(r'https://live\.douyin\.com/' + room + r'(?:[/?#]|$)', p.get('url', '')) for p in pages):
                raise RuntimeError('直播窗口尚未进入该直播间，请先完成登录或验证')
            node = shutil.which('node')
            if not node:
                raise RuntimeError('未找到 Node.js')
            env = os.environ.copy()
            env['PRINTER_CDP_PORT'] = '9224'
            with open(ROOT / 'desktop-bridge.log', 'ab') as log:
                self._bridge = subprocess.Popen([node, str(ROOT / 'douyin-bridge.mjs'), room], cwd=ROOT,
                    env=env, stdout=log, stderr=log, **process_options())
            status = wait_bridge(self._bridge)
            return f'数据桥已启动，端口 {status["port"]}，正在连接直播评论。'

    def stop_capture(self, raw=None):
        with self._lock:
            if self._bridge and self._bridge.poll() is None:
                self._bridge.terminate()
                self._bridge.wait(timeout=5)
            self._bridge = None
            return '抓取已停止 / Capture stopped.'

    def close(self):
        if self._scene_process and self._scene_process.poll() is None:
            self._scene_process.terminate()
            self._scene_process.wait(timeout=5)
        self.stop_capture()
        if self._live and self._live.poll() is None:
            self._live.terminate()
            self._live.wait(timeout=5)

def main():
    # Keep the rendering window active when the detached view is in front.
    browser_flags = os.environ.get('WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS', '')
    os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = browser_flags + (
        ' --disable-backgrounding-occluded-windows --disable-renderer-backgrounding'
        ' --disable-background-timer-throttling'
    )
    if (ROOT / '.capture-compat').exists():
        os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] += (
            ' --disable-gpu --disable-accelerated-video-decode'
        )
    parser = argparse.ArgumentParser()
    parser.add_argument('--live-room')
    parser.add_argument('--server-only', action='store_true')
    parser.add_argument('--browser', action='store_true', help='Use Chrome instead of WebView2')
    parser.add_argument('--room')
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--scene-view', action='store_true')
    parser.add_argument('--scene-orient', default='landscape')
    args = parser.parse_args()
    if args.scene_view and sys.platform == 'win32' and not args.browser:
        import webview
        sizes = {'landscape': (1280, 720), 'landscape-1080p': (1920, 1080),
                 'portrait': (720, 1280), 'portrait-1080p': (1080, 1920)}
        width, height = sizes.get(args.scene_orient, (1280, 720))
        api = DesktopApi()
        win = webview.create_window('直播小窗 · Avatar Printer',
            'http://127.0.0.1:' + str(ACTIVE_PORT) + '/live-view.html', js_api=api,
            width=width, height=height, background_color='#000000', resizable=True)
        api._scene_windows.append(win)
        webview.start(gui='edgechromium', private_mode=False,
            storage_path=str(ROOT / '.scene-webview-profile'))
        return
    if args.live_room and sys.platform == 'win32' and not args.browser:
        import webview
        webview.settings['REMOTE_DEBUGGING_PORT'] = 9224
        room = room_id(args.live_room)
        webview.create_window('直播间登录 · ' + room, 'https://live.douyin.com/' + room, width=1180, height=800)
        webview.start(gui='edgechromium', private_mode=False, storage_path=str(ROOT / '.live-webview-profile'))
        return
    url, server = ensure_server()
    api = DesktopApi()
    try:
        if args.server_only or args.browser or sys.platform != 'win32':
            if not args.server_only:
                target = url + ('live-view.html' if args.scene_view else '')
                if not open_browser(target):
                    raise RuntimeError('未找到 Chrome / Edge，请安装 Google Chrome 或设置 PRINTER_BROWSER')
            print('头像打印机服务：' + url, flush=True)
            print('直播素材：' + url + 'materials.html', flush=True)
            print('保持此终端窗口开启，按 Ctrl+C 停止服务和数据桥。', flush=True)
            threading.Event().wait()
        else:
            import webview
            webview.create_window('头像打印机 · 桌面版', url, js_api=api, width=1380, height=860,
                min_size=(900, 650), background_color='#0b0e14')
            def start_requested_room():
                if not args.room:
                    return
                try:
                    print(api.open_live_room(args.room), flush=True)
                    if args.capture:
                        for _ in range(30):
                            if listening(9224):
                                try:
                                    print(api.start_capture(args.room), flush=True)
                                    return
                                except (OSError, RuntimeError):
                                    pass
                            threading.Event().wait(1)
                        print('直播窗口未就绪，请完成登录后点击开始抓取', flush=True)
                except Exception as exc:
                    print(str(exc), flush=True)
            webview.start(start_requested_room, gui='edgechromium', private_mode=False, storage_path=str(ROOT / '.printer-webview-profile'))
    except KeyboardInterrupt:
        pass
    finally:
        api.close()
        if server:
            server.shutdown()
            server.server_close()
        if api._restart_requested:
            restart_args = [sys.executable, str(ROOT / 'launch.py')]
            if api._room:
                restart_args += ['--room', api._room]
            subprocess.Popen(restart_args, cwd=ROOT)

if __name__ == '__main__':
    main()
