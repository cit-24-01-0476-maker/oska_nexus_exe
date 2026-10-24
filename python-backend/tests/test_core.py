import os
import sys
import time
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
test_data = tempfile.TemporaryDirectory(prefix='oska-tests-')
os.environ['OSKA_DATA_DIR'] = test_data.name
import main
from fastapi.testclient import TestClient
from storage.database import get_connection
from storage.reminders import resolve_due_time, claim_due_reminders
from commands.parser import CommandParser


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.speech = patch.object(main, 'speak')
        cls.speech.start()
        cls.client = TestClient(main.app)

    @classmethod
    def tearDownClass(cls):
        cls.speech.stop()
        main.tts_engine.stop()

    def setUp(self):
        conn = get_connection()
        for table in ['notes', 'reminders', 'chat_history', 'audit_logs', 'email_drafts']:
            conn.execute(f'DELETE FROM {table}')
        conn.commit(); conn.close()
        main.pending_power = None

    def test_notes_crud_validation_and_missing(self):
        c = self.client
        self.assertEqual(c.post('/api/notes', json={'title':' ', 'content':'x'}).status_code, 422)
        result = c.post('/api/notes', json={'title':'සිංහල', 'content':'Chrome ගැන note එකක්'}).json()
        note_id = result['id']
        self.assertEqual(c.get('/api/notes').json()[0]['title'], 'සිංහල')
        self.assertEqual(c.put(f'/api/notes/{note_id}', json={'title':'Edited', 'content':'Updated'}).status_code, 200)
        self.assertEqual(c.get('/api/notes').json()[0]['content'], 'Updated')
        self.assertEqual(c.delete(f'/api/notes/{note_id}').status_code, 200)
        self.assertEqual(c.delete(f'/api/notes/{note_id}').status_code, 404)

    def test_reminders_crud_and_claim_once(self):
        c = self.client
        self.assertEqual(c.post('/api/reminders', json={'title':'past','due_time':time.time()-1}).status_code, 422)
        item = c.post('/api/reminders', json={'title':'tea in 5 minutes'}).json()
        self.assertAlmostEqual(item['due_time'], time.time()+300, delta=3)
        conn = get_connection(); conn.execute('UPDATE reminders SET due_time = ?', (time.time()-1,)); conn.commit(); conn.close()
        self.assertEqual(len(claim_due_reminders()), 1)
        self.assertEqual(claim_due_reminders(), [])
        self.assertEqual(c.patch(f"/api/reminders/{item['id']}", json={'completed':True}).status_code, 200)
        self.assertEqual(c.get('/api/reminders').json()[0]['completed'], 1)
        self.assertEqual(c.delete(f"/api/reminders/{item['id']}").status_code, 200)

    def test_clock_reminder_rollover(self):
        now = datetime(2026, 10, 24, 18, 0)
        self.assertEqual(datetime.fromtimestamp(resolve_due_time('submit at 5 PM', now)), datetime(2026,10,25,17))
        self.assertEqual(datetime.fromtimestamp(resolve_due_time('submit tomorrow at 9 AM', now)), datetime(2026,10,25,9))
        with self.assertRaises(ValueError): resolve_due_time('bad at 25:00', now)

    def test_note_and_reminder_contents_do_not_launch_apps(self):
        for text, intent in [('note down open chrome tomorrow','create_note'), ('remind me to restart in 5 minutes','create_reminder'), ('create note about VS Code','create_note')]:
            self.assertEqual(CommandParser.parse(text)['intent'], intent)
        for text, intent in [('What time is it?','get_time'), ('unmute','set_mute'), ('open chrome','open_app'), ('restart computer','request_restart')]:
            self.assertEqual(CommandParser.parse(text)['intent'], intent)

    def test_history_returns_latest_hundred(self):
        conn = get_connection()
        conn.executemany('INSERT INTO chat_history (role,content,created_at) VALUES (?,?,?)', [('user',str(i),time.time()) for i in range(120)])
        conn.commit(); conn.close()
        history = self.client.get('/api/chat/history').json()
        self.assertEqual(len(history),100)
        self.assertEqual(history[0]['content'],'20')
        self.assertEqual(history[-1]['content'],'119')

    def test_command_persists_response_and_audit(self):
        response = self.client.post('/api/command',json={'text':'What time is it?'}).json()
        self.assertEqual(response['status'],'SUCCESS')
        self.assertEqual(len(self.client.get('/api/chat/history').json()),2)
        self.assertEqual(self.client.get('/api/audit').json()[0]['action_type'],'GET_TIME')
        self.assertEqual(main.state_machine.context['response'],response['response'])
        self.assertEqual(self.client.post('/api/command',json={'text':'  '}).status_code,422)

    def test_power_requires_pending_unexpired_single_use_confirmation(self):
        c = self.client
        with patch.object(main,'execute_restart', return_value=(True,'mocked')) as restart:
            self.assertEqual(c.post('/api/power/confirm',json={'action':'request_restart','confirmed':True}).status_code,409)
            c.post('/api/command',json={'text':'restart computer'})
            self.assertEqual(c.post('/api/power/confirm',json={'action':'request_shutdown','confirmed':True}).status_code,409)
            self.assertEqual(c.post('/api/power/confirm',json={'action':'request_restart','confirmed':False}).json()['status'],'CANCELLED')
            restart.assert_not_called()
            c.post('/api/command',json={'text':'restart computer'})
            main.pending_power['expires'] = 0
            self.assertEqual(c.post('/api/power/confirm',json={'action':'request_restart','confirmed':True}).status_code,409)
            self.assertIsNone(main.state_machine.context['pending_confirmation'])
            c.post('/api/command',json={'text':'restart computer'})
            self.assertEqual(c.post('/api/power/confirm',json={'action':'request_restart','confirmed':True}).json()['status'],'SUCCESS')
            restart.assert_called_once()
            self.assertEqual(c.post('/api/power/confirm',json={'action':'request_restart','confirmed':True}).status_code,409)

    def test_custom_routine_trigger_and_duplicate(self):
        routine = {'id':'test-routine','name':'Test routine','description':'','trigger_phrase':'my custom mode','actions':[{'type':'notify','target':'Ready','label':'Notify'}]}
        self.assertEqual(self.client.post('/api/routines',json=routine).status_code,200)
        self.assertEqual(self.client.post('/api/routines',json=routine).status_code,409)
        with patch.object(main.routine_runner,'run_routine',return_value={'status':'SUCCESS','response':'Ready'}) as run:
            self.client.post('/api/command',json={'text':'my custom mode'})
            run.assert_called_once_with('test-routine')

    def test_invalid_settings_do_not_persist(self):
        previous = self.client.get('/api/settings').json()['tts_rate']
        self.assertEqual(self.client.post('/api/settings',json={'settings':{'tts_rate':'-1'}}).status_code,422)
        self.assertEqual(self.client.get('/api/settings').json()['tts_rate'],previous)

    def test_legacy_default_timer_upgrade_is_idempotent(self):
        import json
        from storage.database import init_db
        conn = get_connection()
        actions = json.loads(conn.execute("SELECT actions_json FROM routines WHERE id='routine-study'").fetchone()[0])
        old = [a for a in actions if a['type'] != 'timer']
        conn.execute("UPDATE routines SET actions_json=? WHERE id='routine-study'", (json.dumps(old),))
        conn.commit(); conn.close()
        init_db(); init_db()
        study = next(r for r in self.client.get('/api/routines').json() if r['id']=='routine-study')
        self.assertEqual(sum(a['type']=='timer' for a in study['actions']),1)

    def test_llm_requires_key_and_local_mode_never_uses_network(self):
        with patch('providers.llm_manager.httpx.Client') as network:
            result = main.llm_manager.generate_response('Explain quantum physics', {'llm_provider':'local_rules'})
            self.assertIn('Settings', result)
            network.assert_not_called()
            with self.assertRaises(ValueError):
                main.llm_manager.generate_response('Explain physics', {'llm_provider':'gemini'})

    def test_llm_provider_error_is_reported_without_key(self):
        import httpx
        request = httpx.Request('POST', 'https://generativelanguage.googleapis.com/v1beta/models/test:generateContent')
        response = httpx.Response(403, request=request)
        with patch('providers.llm_manager.httpx.Client') as client:
            client.return_value.__enter__.return_value.post.return_value = response
            with self.assertRaisesRegex(RuntimeError, 'HTTP 403') as caught:
                main.llm_manager.generate_response('Explain physics', {'llm_provider':'gemini','llm_api_key':'test-secret'})
            self.assertNotIn('test-secret',str(caught.exception))

    def test_untrusted_browser_origin_cannot_call_api(self):
        self.assertEqual(self.client.post('/api/tts/test',headers={'Origin':'https://untrusted.example'}).status_code,403)

    def test_only_one_voice_interaction_can_start(self):
        main.interaction_lock.acquire()
        try: self.assertEqual(self.client.post('/api/voice/listen').status_code,409)
        finally: main.interaction_lock.release()

    def test_websocket_initial_state(self):
        with self.client.websocket_connect('/ws') as ws:
            self.assertEqual(ws.receive_json()['type'],'initial_state')
            ws.send_json({'action':'ping'})
            self.assertEqual(ws.receive_json(),{'type':'pong'})

    def test_failed_routine_step_is_not_success(self):
        with patch('automation.routine_runner.set_system_volume',return_value=False), patch('automation.routine_runner.launch_application',return_value=(True,'mocked')), patch.object(main.tts_engine,'speak'), patch('automation.routine_runner.time.sleep'):
            result = main.routine_runner.run_routine('routine-study')
            self.assertNotEqual(result['status'],'SUCCESS')

if __name__ == '__main__':
    unittest.main()
