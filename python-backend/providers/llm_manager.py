import httpx
import re
from typing import Dict, Any, Optional

class LLMManager:
    def __init__(self):
        pass

    def _match_conversational_rule(self, prompt: str) -> Optional[str]:
        """
        Instant high-precision Sinhala, Singlish, and English conversational intelligence.
        """
        clean = prompt.lower().strip()
        has_sinhala = bool(re.search(r'[\u0D80-\u0DFF]', prompt))

        # 1. Greetings
        # "kohomada", "ayubowan", "hello", "hi", "hey", "oyaata kohomada"
        if re.search(r"\b(kohomada|kohomadha|oyaata kohomada|oyata kohomada|hondinda|සුවෙන්ද|කොහොමද)\b", clean):
            return "මම ඉතාම හොඳින් ඉන්නවා, ස්තූතියි! ඔබට අද මගෙන් උදව් අවශ්‍ය වන්නේ කෙසේද?"

        if re.search(r"\b(ayubowan|aayubowan|ආයුබෝවන්)\b", clean):
            return "ආයුබෝවන්! මම OSKA NEXUS. ඔබට උදව් කිරීමට මම සූදානම්."

        if re.search(r"^(hello|hi|hey|good day|halo)\b", clean):
            if has_sinhala or re.search(r"\b(oya|mata|kohomada|karanna)\b", clean):
                return "ආයුබෝවන්! ඔබට මගෙන් කුමක්ද කෙරෙන්න ඕනේ?"
            return "Hello! I am OSKA NEXUS. How can I assist you today?"

        # 2. Good Morning / Night
        if re.search(r"\b(subha udasanak|good morning|සුබ උදෑසනක්)\b", clean):
            return "සුබ උදෑසනක්! අද දවස ඔබට ඉතාමත් සාර්ථක දිනයක් වේවා."
        if re.search(r"\b(subha rathriyak|good night|සුබ රාත්‍රියක්)\b", clean):
            return "සුබ රාත්‍රියක්! හොඳින් විවේක ගන්න. මම අවශ්‍ය ඕනෑම වෙලාවක මෙහි රැඳී සිටිනවා."

        # 3. Identity: "who are you", "kawda oya", "oya kawda", "what is your name"
        if re.search(r"\b(who are you|what is your name|kawda oya|oya kawda|mokakda oyage nama|කවුද ඔයා|ඔයා කවුද)\b", clean):
            return "මම OSKA NEXUS. ඔබගේ පුද්ගලික Holographic Desktop AI සහායකයා. මට පරිගණකය පාලනය කිරීමටත්, ඔබ සමඟ කතා කිරීමටත් හැකියි."

        # 4. Capabilities: "what can you do", "oyata monda karanna puluwan", "oyata puluwan monada"
        if re.search(r"\b(what can you do|monda karanna puluwan|monawada karanna puluwan|oyata puluwan monada|මොනවද කරන්න පුළුවන්)\b", clean):
            return "මට හඳුනාගත් apps විවෘත කරන්න, volume වෙනස් කරන්න, වෙබ් සෙවීම් සහ notes හෝ reminders හදන්න පුළුවන්. සාමාන්‍ය කතාබහ සඳහා AI provider එකක් සම්බන්ධ කරන්න."

        # 5. Language capabilities: "sinhala puluwanda", "sinhala therenawada", "do you know sinhala"
        if re.search(r"\b(sinhala puluwanda|sinhala therenawada|sinhala katha karanna|sinhala dannawada|සිංහල තේරෙනවද|සිංහල පුළුවන්ද)\b", clean):
            return "මට සිංහල සහ Singlish desktop commands කිහිපයක් තේරෙනවා. සාමාන්‍ය සිංහල කතාබහ සඳහා Settings වලින් AI provider එකක් සම්බන්ධ කරන්න."

        # 6. Creator: "who made you", "oyawa haduwe kawda"
        if re.search(r"\b(who made you|who created you|haduwe kawda|oyawa haduwe|නිර්මාණය කළේ කවුද)\b", clean):
            return "මාව නිර්මාණය කරන ලද්දේ OSKA TECH ආයතනය විසිනි."

        # 7. Gratitude: "thank you", "thanks", "sthuthiyi", "bohoma sthuthiyi"
        if re.search(r"\b(thank you|thanks|sthuthiyi|bohoma sthuthiyi|godak sthuthiyi|ස්තූතියි|බොහෝම ස්තූතියි)\b", clean):
            return "ඔබට සාදරයෙන් පිළිගන්නවා! උදව් කිරීමට ලැබීම මගේ සතුටක්."

        # 8. Activity: "mokada karanne", "what are you doing"
        if re.search(r"\b(mokada karanne|what are you doing|mokada wenne|මොකද කරන්නේ)\b", clean):
            return "මම ඔබගේ ඩෙස්ක්ටොප් එකේ ඔබ ලබා දෙන විධානයකට සවන් දෙමින් සූදානමින් ඉන්නවා."

        return None

    def _query_web_summary(self, query: str) -> Optional[str]:
        """
        Retrieves a concise web knowledge snippet when offline rules don't match and no LLM key is configured.
        """
        try:
            # Query DuckDuckGo HTML for a concise result
            url = f"https://html.duckduckgo.com/html/?q={httpx.URL(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    from html.parser import HTMLParser
                    # Simple extraction of first snippet
                    snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', resp.text, re.DOTALL)
                    if snippets:
                        snippet = re.sub(r'<[^>]+>', '', snippets[0]).strip()
                        # Shorten to 1-2 clean sentences
                        sentences = snippet.split('. ')
                        short_text = ". ".join(sentences[:2])
                        if not short_text.endswith('.'):
                            short_text += '.'
                        return short_text
        except Exception as e:
            print(f"[LLM] Web knowledge fallback error: {e}")
        return None

    def generate_response(self, prompt: str, settings: Dict[str, str], system_instruction: Optional[str] = None) -> str:
        prompt = prompt.strip()
        if not prompt:
            return "Please enter a command."
        provider = settings.get('llm_provider', 'local_rules')
        if provider == 'local_rules':
            matched = self._match_conversational_rule(prompt)
            if matched:
                return matched
            if re.search(r'[\u0D80-\u0DFF]|\b(mata|mama|oya|oyata|karanna|mokakda|kohomada|sinhala)\b', prompt, re.I):
                return "දැනට මට basic desktop commands විතරයි කරන්න පුළුවන්. මේ වගේ සාමාන්‍ය සිංහල කතාබහ සඳහා Settings වලින් AI provider එකක් සම්බන්ධ කරන්න."
            return "I can run desktop commands and save notes or reminders. Connect an AI provider in Settings for general questions."

        from storage.database import get_connection
        conn = get_connection()
        try:
            history = [dict(r) for r in conn.execute("SELECT role, content FROM (SELECT id, role, content FROM chat_history WHERE command_intent = 'conversation' ORDER BY id DESC LIMIT 12) ORDER BY id")]
        finally:
            conn.close()
        if system_instruction:
            history = []
        instruction = system_instruction or "You are OSKA NEXUS, a warm, natural Windows desktop assistant by OSKA TECH. Answer briefly in 1-3 sentences. Reply in everyday spoken Sinhala for Sinhala or Singlish, and English for English. Use the recent conversation for follow-up questions. Never claim to have executed actions you did not execute."
        key = settings.get('llm_api_key', '').strip()
        model = settings.get('llm_model', '').strip()
        if provider == 'xai':
            key = settings.get('xai_api_key', '').strip()
            model = settings.get('xai_model', 'grok-4.7').strip() or 'grok-4.7'
        if provider in ['gemini', 'openai', 'xai'] and not key:
            raise ValueError(f'Add your {provider} API key in Settings first.')
        try:
            with httpx.Client(timeout=30) as client:
                if provider == 'gemini':
                    if not model.startswith('gemini-'): model = 'gemini-3.1-flash-lite'
                    contents = [{'role': 'model' if m['role'] == 'assistant' else 'user', 'parts': [{'text': m['content']}]} for m in history]
                    contents.append({'role':'user','parts':[{'text':prompt}]})
                    response = client.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent', headers={'x-goog-api-key':key}, json={'systemInstruction': {'parts':[{'text':instruction}]}, 'contents':contents, 'generationConfig':{'maxOutputTokens':1024}})
                    response.raise_for_status()
                    result = ''.join(p.get('text','') for p in response.json().get('candidates',[{}])[0].get('content',{}).get('parts',[]) if not p.get('thought'))
                elif provider == 'ollama':
                    if not model or model.startswith(('gpt-', 'gemini-')): model = 'llama3'
                    messages = [{'role':'system','content':instruction}, *history, {'role':'user','content':prompt}]
                    response = client.post(settings.get('ollama_endpoint', 'http://localhost:11434').rstrip('/')+'/api/chat', json={'model':model,'messages':messages,'stream':False})
                    response.raise_for_status()
                    result = response.json().get('message',{}).get('content','')
                elif provider == 'xai':
                    response = client.post(
                        'https://api.x.ai/v1/responses',
                        headers={'Authorization': f'Bearer {key}'},
                        json={'model':model, 'input':[{'role':'system','content':instruction}, *history, {'role':'user','content':prompt}],
                              'store':False, 'max_output_tokens':1024},
                        timeout=60,
                    )
                    response.raise_for_status()
                    data = response.json()
                    result = ''.join(part.get('text','') for item in data.get('output',[]) if item.get('type') == 'message'
                                     for part in item.get('content',[]) if part.get('type') == 'output_text')
                elif provider == 'openai':
                    if not model or model.startswith('gemini-') or model == 'llama3': model = 'gpt-4o-mini'
                    response = client.post('https://api.openai.com/v1/chat/completions', headers={'Authorization':f'Bearer {key}'}, json={'model':model,'messages':[{'role':'system','content':instruction}, *history, {'role':'user','content':prompt}]})
                    response.raise_for_status()
                    result = response.json()['choices'][0]['message']['content']
                else:
                    raise ValueError('Select a supported AI provider in Settings.')
            if not result or not result.strip():
                raise ValueError('The AI provider returned no text. Check the model and try again.')
            return result.strip()
        except httpx.HTTPStatusError as exc:
            if provider == 'xai':
                try:
                    error = str(exc.response.json().get('error', '')).lower()
                except (ValueError, AttributeError):
                    error = ''
                if exc.response.status_code in [402, 403, 429] and any(word in error for word in ['credit', 'billing', 'license', 'spending']):
                    raise RuntimeError('xAI cannot answer because this account has no usable API credits or license. Check billing in console.x.ai, or select your configured Gemini provider.') from None
                if exc.response.status_code == 401:
                    raise RuntimeError('xAI rejected the API key. Check the xAI key in Settings.') from None
            raise RuntimeError(f'{provider} returned HTTP {exc.response.status_code}. Check your API key, model, quota and service access in Settings.') from None
        except httpx.TimeoutException:
            raise RuntimeError(f'{provider} took too long to reply. Try again or choose a faster model in Settings.') from None
        except httpx.RequestError:
            raise RuntimeError(f'Cannot connect to {provider}. Check your connection and provider endpoint.') from None
