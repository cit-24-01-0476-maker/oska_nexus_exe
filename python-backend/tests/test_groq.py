import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from providers.llm_manager import LLMManager

class TestGroqProvider(unittest.TestCase):
    def setUp(self):
        self.mgr = LLMManager()

    def test_groq_missing_key(self):
        settings = {'llm_provider': 'groq', 'groq_api_key': '', 'llm_api_key': ''}
        with self.assertRaises(ValueError):
            self.mgr.generate_response("hello", settings)

    def test_groq_response_mock(self):
        settings = {
            'llm_provider': 'groq',
            'groq_api_key': 'test-groq-key',
            'groq_model': 'openai/gpt-oss-120b'
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'choices': [{'message': {'content': 'ආයුබෝවන්! මම OSKA NEXUS.'}}]
        }
        with patch('httpx.Client.post', return_value=mock_resp):
            resp = self.mgr.generate_response("hello", settings)
            self.assertIn("ආයුබෝවන්", resp)

    def test_groq_live_if_env(self):
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            return
        settings = {
            'llm_provider': 'groq',
            'groq_api_key': key,
            'groq_model': 'openai/gpt-oss-120b'
        }
        resp = self.mgr.generate_response("Say hello in Sinhala", settings)
        self.assertTrue(len(resp) > 0)

if __name__ == '__main__':
    unittest.main()
