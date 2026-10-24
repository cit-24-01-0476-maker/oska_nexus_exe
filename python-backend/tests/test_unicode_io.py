import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np

from test_core import main
from assistant.text_io import configure_unicode_streams, safe_print
from voice.stt_whisper import FasterWhisperSTT

SINHALA = 'සිංහල තේරෙනවද'


class UnicodeSpeechTests(unittest.TestCase):
    def test_google_sinhala_survives_legacy_windows_log_encoding(self):
        engine = FasterWhisperSTT()
        buffer = io.BytesIO()
        legacy = io.TextIOWrapper(buffer, encoding='cp1252', errors='strict')
        with patch.object(engine, '_transcribe_google', return_value=SINHALA), patch('sys.stdout', legacy):
            self.assertEqual(engine.transcribe(np.zeros(16000, dtype=np.float32)), SINHALA)
        legacy.flush()
        self.assertIn(b'\\u0', buffer.getvalue())

    def test_offline_sinhala_survives_legacy_windows_log_encoding(self):
        engine = FasterWhisperSTT()
        engine._model = SimpleNamespace(transcribe=lambda *a, **k: ([SimpleNamespace(text=SINHALA)], SimpleNamespace(language='si')))
        legacy = io.TextIOWrapper(io.BytesIO(), encoding='cp1252', errors='strict')
        with patch.object(engine, '_transcribe_google', return_value=None), patch('sys.stdout', legacy):
            self.assertEqual(engine.transcribe(np.zeros(16000, dtype=np.float32)), SINHALA)

    def test_utf8_configuration_preserves_sinhala_bytes(self):
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding='cp1252')
        with patch('sys.stdout', stream), patch('sys.stderr', None):
            configure_unicode_streams()
            safe_print(SINHALA)
            self.assertEqual(stream.encoding, 'utf-8')
        stream.flush()
        self.assertEqual(buffer.getvalue().decode('utf-8').strip(), SINHALA)

    def test_unavailable_log_stream_cannot_break_a_command(self):
        closed = io.TextIOWrapper(io.BytesIO(), encoding='cp1252')
        closed.close()
        safe_print(SINHALA, file=closed)
        with patch('sys.stdout', None), patch('sys.stderr', None):
            configure_unicode_streams()
            safe_print(SINHALA)

    def test_backend_startup_reconfigures_redirected_windows_streams(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix='oska-utf8-') as data:
            code = (
                "import os,sys; sys.stdout.reconfigure(encoding='cp1252',errors='strict'); "
                "sys.stderr.reconfigure(encoding='cp1252',errors='strict'); "
                f"os.environ['OSKA_DATA_DIR']={data!r}; sys.path.insert(0,'python-backend'); "
                "import main; assert sys.stdout.encoding == 'utf-8'; "
                f"print({SINHALA!r}); main.tts_engine.stop()"
            )
            completed = subprocess.run([sys.executable,'-c',code],cwd=root,capture_output=True,timeout=30)
            self.assertEqual(completed.returncode,0,completed.stderr.decode('utf-8',errors='replace'))
            self.assertIn(SINHALA,completed.stdout.decode('utf-8'))

    def test_recognized_sinhala_reaches_command_and_conversation_layers(self):
        engine = FasterWhisperSTT()
        legacy = io.TextIOWrapper(io.BytesIO(),encoding='cp1252',errors='strict')
        with patch.object(engine,'_transcribe_google',return_value='වෙලාව කීයද'), patch('sys.stdout',legacy):
            text=engine.transcribe(np.zeros(16000,dtype=np.float32))
        with patch.object(main,'speak'):
            result=main.handle_command_text(text)
        self.assertEqual(result['status'],'SUCCESS')
        self.assertEqual(result['intent'],'get_time')
        self.assertIn('වේලාව',result['response'])
        answer=main.llm_manager.generate_response(SINHALA,{'llm_provider':'local_rules'})
        self.assertIn('සිංහල',answer)

    def test_recognized_sinhala_reaches_configured_ai_without_text_loss(self):
        import httpx
        question='මට අද පාඩම් කරන්න සැලැස්මක් හදලා දෙන්න'
        answer='මුලින් විනාඩි විසි පහක් පාඩම් කරලා කෙටි විවේකයක් ගන්න.'
        engine=FasterWhisperSTT()
        legacy=io.TextIOWrapper(io.BytesIO(),encoding='cp1252',errors='strict')
        with patch.object(engine,'_transcribe_google',return_value=question), patch('sys.stdout',legacy):
            text=engine.transcribe(np.zeros(16000,dtype=np.float32))
        previous=main.get_all_settings()
        main.set_setting('llm_provider','gemini')
        main.set_setting('llm_api_key','test-only-key')
        response=httpx.Response(200,request=httpx.Request('POST','https://generativelanguage.googleapis.com/'),json={'candidates':[{'content':{'parts':[{'text':answer}]}}]})
        try:
            with patch('providers.llm_manager.httpx.Client') as client, patch.object(main,'speak'), patch.object(main.command_executor,'execute',side_effect=AssertionError('A conversational request must not execute desktop actions')):
                client.return_value.__enter__.return_value.post.return_value=response
                result=main.handle_command_text(text)
                posted=client.return_value.__enter__.return_value.post.call_args.kwargs['json']
            self.assertEqual(result['status'],'SUCCESS')
            self.assertEqual(result['response'],answer)
            self.assertEqual(posted['contents'][-1]['parts'][0]['text'],question)
        finally:
            main.set_setting('llm_provider',previous['llm_provider'])
            main.set_setting('llm_api_key',previous['llm_api_key'])

    def test_sinhala_planning_questions_do_not_launch_apps_or_routines(self):
        from commands.parser import CommandParser
        for prompt in ['මට අද පාඩම් කරන්න සැලැස්මක් හදලා දෙන්න','Chrome කියන්නේ මොකක්ද','Tell me about VS Code','Make a study plan for tomorrow']:
            self.assertEqual(CommandParser.parse(prompt)['intent'],'conversation',prompt)
        for prompt, intent in [('පාඩම් කරන්න','trigger_routine'),('Open Chrome','open_app'),('What time is it?','get_time'),('Show RAM usage','get_system_metrics')]:
            self.assertEqual(CommandParser.parse(prompt)['intent'],intent,prompt)

if __name__ == '__main__':
    unittest.main()
