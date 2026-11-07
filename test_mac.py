import json
import os
import socket
import subprocess
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch
import launch


class MacSupportTests(unittest.TestCase):
    def test_browser_candidates_include_mac_and_user_apps(self):
        paths = launch.browser_candidates('darwin')
        self.assertTrue(any('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' in p for p in paths))
        self.assertTrue(any(str(Path.home() / 'Applications') in p for p in paths))

    def test_no_windows_creationflags_on_mac(self):
        self.assertEqual(launch.process_options('darwin'), {})
        self.assertIn('creationflags', launch.process_options('win32'))

    def test_open_browser_uses_isolated_debug_profile(self):
        with patch.object(launch, 'find_browser', return_value='/test/Chrome'), patch.object(launch.subprocess, 'Popen') as popen:
            self.assertTrue(launch.open_browser('https://live.douyin.com/123456', debug=True))
            args = popen.call_args.args[0]
            self.assertIn('--remote-debugging-address=127.0.0.1', args)
            self.assertIn('--remote-debugging-port=9223', args)
            self.assertIn('--user-data-dir=' + str(launch.ROOT / '.bridge-profile'), args)

    def test_server_respects_available_port_and_serves_project_from_any_cwd(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        old = os.getcwd()
        with tempfile.TemporaryDirectory() as folder, patch.object(launch, 'SERVER_PORTS', (port,)):
            os.chdir(folder)
            server = None
            try:
                url, server = launch.ensure_server()
                self.assertEqual(url, f'http://127.0.0.1:{port}/')
                with launch.local_get(url) as r:
                    self.assertIn('AVATAR PRINT STUDIO', r.read().decode())
                req = urllib.request.Request(url + '__stop-bridge', headers={'Sec-Fetch-Site': 'same-origin'})
                with launch._LOCAL_OPENER.open(req) as r:
                    self.assertTrue(json.load(r)['ok'])
                bad = urllib.request.Request(url + '__stop-bridge', headers={'Sec-Fetch-Site': 'same-origin', 'Host': f'127.0.0.1:{port}9'})
                with self.assertRaises(urllib.error.HTTPError) as err:
                    launch._LOCAL_OPENER.open(bad)
                self.assertEqual(err.exception.code, 403)
            finally:
                os.chdir(old)
                if server:
                    server.shutdown()
                    server.server_close()


if __name__ == '__main__':
    unittest.main()
