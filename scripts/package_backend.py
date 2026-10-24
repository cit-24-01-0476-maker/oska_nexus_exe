"""Build a self-contained Windows backend; rebuild when sources change."""
import os
import subprocess
import sys
import ssl
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
exe = root / 'build' / 'backend' / 'oska-backend' / 'oska-backend.exe'
sources = [p for p in (root / 'python-backend').rglob('*.py') if not {'venv', '__pycache__', 'tests'}.intersection(p.parts)]
sources += [root / 'python-backend' / 'requirements.txt', Path(__file__)]
stamp = root / 'build' / 'backend-source.sha256'
digest = hashlib.sha256(b''.join(p.read_bytes() for p in sorted(sources))).hexdigest()
if exe.exists() and stamp.exists() and stamp.read_text() == digest:
    print('Backend package is up to date.')
    sys.exit(0)
python = root / '.venv' / 'Scripts' / 'python.exe'
if not python.exists():
    raise SystemExit('Create .venv and install python-backend/requirements.txt and pyinstaller first. See README.md.')
args = [str(python), '-m', 'PyInstaller', '--noconfirm', '--onedir', '--name', 'oska-backend',
        '--distpath', str(root / 'build' / 'backend'), '--workpath', str(root / 'build' / 'pyinstaller'),
        '--specpath', str(root / 'build'), '--paths', str(root / 'python-backend'),
        '--hidden-import', 'pyttsx3.drivers.sapi5', '--hidden-import', 'uvicorn.logging',
        '--hidden-import', 'pyautogui', '--collect-all', 'PIL',
        '--collect-all', 'faster_whisper', '--collect-all', 'ctranslate2', '--collect-all', 'pvporcupine',
        '--collect-all', 'onnxruntime', '--collect-all', 'sounddevice', '--collect-all', 'edge_tts',
        str(root / 'python-backend' / 'main.py')]
# Preserve extra trust-store files used by the selected Python distribution.
for certificate in Path(ssl.__file__).parent.glob('codex-*.pem'):
    args.extend(['--add-data', f'{certificate}{os.pathsep}.'])
subprocess.run(args, cwd=root, check=True)
stamp.write_text(digest)
