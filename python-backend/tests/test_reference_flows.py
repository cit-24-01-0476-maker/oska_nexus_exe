import json
import unittest
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch
import numpy as np
from test_core import main, get_connection
from fastapi.testclient import TestClient
from voice.activity import VoiceActivity


class ReferenceFlowTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        conn = get_connection()
        for table in ['email_drafts', 'chat_history', 'audit_logs']:
            conn.execute(f'DELETE FROM {table}')
        conn.commit(); conn.close()
        self.speech = patch.object(main, 'speak')
        self.speech.start()
        main.set_setting('llm_provider', 'local_rules')
        main.set_setting('auto_conversation', 'false')

    def tearDown(self):
        self.speech.stop()
        main.voice_cancelled.clear()

    def command(self, text):
        return self.client.post('/api/command', json={'text':text}).json()

    def create(self):
        result = self.command('Draft an email to my manager: I am unwell tomorrow but can work remotely.')
        self.assertEqual(result['status'],'SUCCESS', result)
        return result['data']['email_draft']

    def test_video_style_draft_then_signature_same_draft(self):
        first = self.create()
        self.assertIn('tomorrow',first['body'])
        self.assertIn('remotely',first['body'])
        changed = self.command('Sign as Example User')['data']['email_draft']
        self.assertEqual(changed['id'],first['id'])
        self.assertEqual(changed['body'],first['body'])
        self.assertEqual(changed['signature'],'Example User')
        latest = self.client.get('/api/email/draft').json()['draft']
        self.assertEqual(latest['signature'],'Example User')

    def test_mail_content_cannot_trigger_desktop_actions(self):
        with patch.object(main.command_executor,'execute') as execute:
            result = self.command('Draft email subject: Restart computer body: Please explain how to restart a computer.')
            self.assertEqual(result['status'],'SUCCESS', result)
            execute.assert_not_called()

    def test_singlish_draft_and_followup_name(self):
        result = self.command('mage boss ta mail ekak hadanna heta mata asaneepa online wada karanna puluwan')
        self.assertEqual(result['status'],'SUCCESS', result)
        self.assertIn('tomorrow',result['data']['email_draft']['body'])
        self.assertIn('ලෑස්තියි',result['response'])
        updated = self.command('mage nama Example User kiyala anthimata danna')
        self.assertEqual(updated['data']['email_draft']['signature'],'Example User')

    def test_replace_preserves_recipient_and_signature(self):
        self.create()
        self.command('Recipient: example@example.com')
        self.command('Sign as Example User')
        changed = self.command('Replace "tomorrow" with "Monday"')['data']['email_draft']
        self.assertIn('Monday',changed['body'])
        self.assertEqual(changed['recipient'],'example@example.com')
        self.assertEqual(changed['signature'],'Example User')

    def test_no_browser_open_until_explicit_request(self):
        with patch('windows.apps.open_url',return_value=(True,'mocked')) as browser:
            draft = self.create()
            browser.assert_not_called()
            opened = self.command('Open this draft in Gmail')
            self.assertEqual(opened['status'],'SUCCESS', opened)
            browser.assert_called_once()
            url = urlparse(browser.call_args.args[0])
            self.assertEqual(url.netloc,'mail.google.com')
            self.assertEqual(parse_qs(url.query)['body'][0],draft['body'])

    def test_manual_editor_validates_recipient(self):
        draft = self.create()
        draft['recipient']='invalid address'
        self.assertEqual(self.client.put('/api/email/draft',json=draft).status_code,422)
        self.assertEqual(self.client.get('/api/email/draft').json()['draft']['recipient'],'')

    def test_structured_ai_edit_has_existing_context_and_is_validated(self):
        draft = self.create()
        fields = {k:draft[k] for k in ['recipient','subject','body','signature']}
        fields['subject']='Updated subject'
        with patch.object(main.llm_manager,'generate_response',return_value=json.dumps(fields)) as model:
            self.assertEqual(main.email_drafts.classify('Make this more professional'),'edit')
            result = main.email_drafts.handle('Make this more professional',{'llm_provider':'gemini'},'edit')
            self.assertEqual(result['data']['email_draft']['subject'],'Updated subject')
            prompt = json.loads(model.call_args.args[0])
            self.assertEqual(prompt['existing_draft']['id'],draft['id'])
            self.assertIn('JSON',model.call_args.kwargs['system_instruction'])
        with patch.object(main.llm_manager,'generate_response',return_value='not json'):
            with self.assertRaises(ValueError):
                main.email_drafts.handle('Make this warmer',{'llm_provider':'gemini'},'edit')
        self.assertEqual(main.email_drafts.current()['subject'],'Updated subject')

    def test_active_draft_does_not_capture_other_commands(self):
        self.create()
        for text in ['Open Chrome','add reminder to drink water','change volume to 30','what is my name?']:
            self.assertIsNone(main.email_drafts.classify(text),text)

    def test_cancelled_voice_never_transcribes_or_executes(self):
        main.voice_cancelled.set()
        main.interaction_lock.acquire()
        with patch.object(main.audio_capture,'start_recording'), patch.object(main.audio_capture,'wait_for_utterance',return_value=False), patch.object(main.audio_capture,'stop_recording',return_value=np.zeros(16000)), patch.object(main.whisper_stt,'transcribe') as stt:
            main.process_voice_interaction()
            stt.assert_not_called()
        self.assertFalse(main.interaction_lock.locked())

    def test_stop_endpoint_disables_continuous_conversation(self):
        main.set_setting('auto_conversation','true')
        self.assertEqual(self.client.post('/api/voice/stop').status_code,200)
        self.assertTrue(main.voice_cancelled.is_set())
        self.assertEqual(main.get_all_settings()['auto_conversation'],'false')


class VoiceActivityTests(unittest.TestCase):
    def test_silence_never_counts_as_a_command(self):
        activity=VoiceActivity(0)
        for i in range(80): activity.feed(.001,.1,i/10)
        self.assertFalse(activity.has_speech)
        self.assertFalse(activity.finished(7.9))
        self.assertTrue(activity.finished(8))

    def test_long_utterance_is_not_cut_at_four_seconds(self):
        activity=VoiceActivity(0)
        for i in range(100):
            activity.feed(.03,.1,i/10)
            self.assertFalse(activity.finished(i/10))
        self.assertTrue(activity.has_speech)
        self.assertFalse(activity.finished(10.5))
        self.assertTrue(activity.finished(11.3))
        self.assertTrue(activity.finished(30))

    def test_short_noise_spike_does_not_end_recording(self):
        activity=VoiceActivity(0)
        activity.feed(.04,.064,1)
        self.assertFalse(activity.has_speech)
        self.assertFalse(activity.finished(3))

if __name__ == '__main__':
    unittest.main()
