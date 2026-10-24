"""Launch an isolated packaged backend and check its real HTTP endpoints."""
import json
import os
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='oska-smoke-') as data:
    env = {**os.environ, 'OSKA_DATA_DIR':data, 'OSKA_PORT':'8766'}
    log = root / 'build' / 'backend-smoke.log'
    with log.open('w') as output:
        process = subprocess.Popen([str(root / 'build/backend/oska-backend/oska-backend.exe')], env=env, stdout=output, stderr=output, creationflags=0x08000000)
        try:
            for _ in range(60):
                if process.poll() is not None:
                    raise RuntimeError(f'Packaged backend exited: {log.read_text()}')
                try:
                    with urllib.request.urlopen('http://127.0.0.1:8766/api/state',timeout=1) as res:
                        assert json.load(res)['state'] == 'IDLE'
                    break
                except OSError:
                    time.sleep(.5)
            else: raise RuntimeError(f'Backend did not become ready. See {log}')
            for path in ['settings','audio/devices','tts/voices','metrics','routines','notes','reminders','audit','email/draft']:
                with urllib.request.urlopen(f'http://127.0.0.1:8766/api/{path}',timeout=10) as res:
                    value = json.load(res)
                    print(f'{path}: OK ({len(value)} entries)')
            draft = {'recipient':'', 'subject':'Smoke test', 'body':'Local verification only.', 'signature':''}
            request = urllib.request.Request('http://127.0.0.1:8766/api/email/draft', data=json.dumps(draft).encode(), headers={'Content-Type':'application/json'}, method='PUT')
            with urllib.request.urlopen(request,timeout=10) as res:
                assert json.load(res)['draft']['subject'] == 'Smoke test'
            print('email draft save: OK')
            print('Packaged backend HTTP smoke test passed.')
        finally:
            process.terminate()
            process.wait(timeout=10)
