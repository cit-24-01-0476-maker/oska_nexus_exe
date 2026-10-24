import unittest
from unittest.mock import patch
import httpx
from test_core import main


class XAIProviderTests(unittest.TestCase):
    def settings(self):
        return {'llm_provider':'xai','llm_api_key':'gemini-fixture-key','llm_model':'gemini-3.1-flash-lite',
                'xai_api_key':'xai-fixture-key','xai_model':'grok-4.7'}

    def response(self, body, status=200):
        return httpx.Response(status, request=httpx.Request('POST','https://api.x.ai/v1/responses'),json=body)

    def test_dedicated_key_model_and_responses_endpoint(self):
        response=self.response({'output':[{'type':'reasoning','content':[{'type':'output_text','text':'private reasoning'}]},
                                          {'type':'message','content':[{'type':'output_text','text':'ආයුබෝවන්!'}]}]})
        with patch('providers.llm_manager.httpx.Client') as client:
            post=client.return_value.__enter__.return_value.post
            post.return_value=response
            result=main.llm_manager.generate_response('සිංහලෙන් ආචාර කරන්න',self.settings())
            self.assertEqual(result,'ආයුබෝවන්!')
            self.assertEqual(post.call_args.args[0],'https://api.x.ai/v1/responses')
            self.assertEqual(post.call_args.kwargs['headers']['Authorization'],'Bearer xai-fixture-key')
            self.assertEqual(post.call_args.kwargs['json']['model'],'grok-4.7')
            self.assertFalse(post.call_args.kwargs['json']['store'])
            self.assertNotIn('gemini-fixture-key',str(post.call_args))

    def test_gemini_key_is_never_sent_to_xai_when_its_key_is_missing(self):
        settings=self.settings(); settings['xai_api_key']=''
        with patch('providers.llm_manager.httpx.Client') as client:
            with self.assertRaisesRegex(ValueError,'xai API key'):
                main.llm_manager.generate_response('Hello',settings)
            client.assert_not_called()

    def test_zero_credit_error_is_actionable_and_redacted(self):
        response=self.response({'error':"Your newly created team doesn't have any credits or licenses yet."},403)
        with patch('providers.llm_manager.httpx.Client') as client:
            client.return_value.__enter__.return_value.post.return_value=response
            with self.assertRaisesRegex(RuntimeError,'credits or license') as caught:
                main.llm_manager.generate_response('Hello',self.settings())
            self.assertNotIn('xai-fixture-key',str(caught.exception))
            self.assertIn('Gemini',str(caught.exception))

    def test_auth_rejection_and_timeout(self):
        with patch('providers.llm_manager.httpx.Client') as client:
            post=client.return_value.__enter__.return_value.post
            post.return_value=self.response({'error':'Unauthorized'},401)
            with self.assertRaisesRegex(RuntimeError,'rejected the API key'):
                main.llm_manager.generate_response('Hello',self.settings())
            post.side_effect=httpx.ReadTimeout('timed out')
            with self.assertRaisesRegex(RuntimeError,'took too long'):
                main.llm_manager.generate_response('Hello',self.settings())

    def test_empty_output_is_not_a_successful_reply(self):
        with patch('providers.llm_manager.httpx.Client') as client:
            client.return_value.__enter__.return_value.post.return_value=self.response({'output':[]})
            with self.assertRaisesRegex(ValueError,'no text'):
                main.llm_manager.generate_response('Hello',self.settings())

    def test_structured_editor_instruction_is_forwarded(self):
        with patch('providers.llm_manager.httpx.Client') as client:
            post=client.return_value.__enter__.return_value.post
            post.return_value=self.response({'output':[{'type':'message','content':[{'type':'output_text','text':'{"body":"Edited"}'}]}]})
            main.llm_manager.generate_response('Edit this draft',self.settings(),system_instruction='Return JSON only.')
            payload=post.call_args.kwargs['json']
            self.assertEqual(payload['input'][0],{'role':'system','content':'Return JSON only.'})
            self.assertEqual(len(payload['input']),2)

    def test_secret_settings_are_not_broadcast(self):
        settings={**self.settings(),'porcupine_access_key':'wake-fixture-key'}
        with patch.object(main,'get_all_settings',return_value=settings), patch.object(main,'broadcast_sync') as broadcast:
            main.publish_settings()
            public=broadcast.call_args_list[0].args[0]['settings']
            self.assertEqual(public['llm_provider'],'xai')
            self.assertNotIn('xai_api_key',public)
            self.assertNotIn('llm_api_key',public)
            self.assertNotIn('porcupine_access_key',public)

if __name__=='__main__':
    unittest.main()
