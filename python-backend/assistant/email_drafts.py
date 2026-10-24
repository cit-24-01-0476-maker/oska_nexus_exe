"""A local, editable mail draft. Opening Gmail is a separate explicit action."""
import json
import re
import time
from urllib.parse import urlencode
from storage.database import get_connection, log_audit

EMAIL = r'[A-Za-z0-9.!#$%&*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+'


class EmailDrafts:
    def __init__(self, llm):
        self.llm = llm

    def current(self):
        conn = get_connection()
        try:
            row = conn.execute('SELECT * FROM email_drafts ORDER BY id DESC LIMIT 1').fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def save(self, fields, create=False):
        allowed = {k: str(fields.get(k, '')).strip() for k in ['recipient', 'subject', 'body', 'signature']}
        if allowed['recipient'] and not re.fullmatch(EMAIL, allowed['recipient']):
            raise ValueError('Enter one valid recipient email address, or leave it blank.')
        if not allowed['body'] or len(allowed['body']) > 20000:
            raise ValueError('Email body must contain between 1 and 20000 characters.')
        if any(len(allowed[k]) > 250 for k in ['subject', 'signature', 'recipient']):
            raise ValueError('Email recipient, subject and signature must be at most 250 characters.')
        conn = get_connection()
        try:
            existing = None if create else conn.execute('SELECT id FROM email_drafts ORDER BY id DESC LIMIT 1').fetchone()
            values = (*allowed.values(), time.time())
            if existing:
                record_id = existing['id']
                conn.execute('UPDATE email_drafts SET recipient=?, subject=?, body=?, signature=?, updated_at=? WHERE id=?', (*values, record_id))
            else:
                cursor = conn.execute('INSERT INTO email_drafts (recipient,subject,body,signature,updated_at) VALUES (?,?,?,?,?)', values)
                record_id = cursor.lastrowid
            conn.commit()
            return dict(conn.execute('SELECT * FROM email_drafts WHERE id=?', (record_id,)).fetchone())
        finally:
            conn.close()

    def classify(self, text):
        clean = text.lower().strip()
        clean = re.sub(r'^(?:(?:hey\s+)?oska|friday|please)[,\s]+', '', clean)
        mail = bool(re.search(r'\b(e-?mail|gmail|mail)\b|ඊමේල්|මේල්|ලිපිය', clean))
        if self.current() and re.match(r'^(open|show|review|arinna)\b|^(අරින්න|පෙන්වන්න)', clean) and re.search(r'\b(gmail|draft)\b|මේල්', clean):
            return 'open' if 'gmail' in clean else 'show'
        if re.search(r'^(new email|new mail|new draft|අලුත් මේල්|අලුත් ඊමේල්)', clean):
            return 'create'
        if mail and re.search(r'\b(draft|compose|create|write|prepare|send|hadanna|hadala|liyanna|yawanna|ekak)\b|ලිය|හද|යව', clean):
            return 'edit' if self.current() and re.search(r'\b(this|that|edit|change|update|eka|ekata)\b|මේක|ඒකට|වෙනස්', clean) else 'create'
        if not self.current():
            return None
        if re.search(r'\b(open|show|review|arinna)\b|අරින්න|පෙන්වන්න', clean) and re.search(r'\b(gmail|draft)\b|මේල්', clean):
            return 'open' if 'gmail' in clean else 'show'
        if re.search(r'^(subject|recipient|body|signature)\s*:', clean):
            return 'edit'
        if re.search(r'\b(volume|reminder|remind|note|music|routine|shutdown|restart)\b', clean):
            return None
        if re.match(r'^(what|why|how|who)\b', clean):
            return None
        if re.search(r'\b(make|rewrite|shorten|translate|polish|rephrase)\s+(this|it|that|the draft|the email)\b|මේක.*(කෙටි|ලිය|ලස්සන|වෙනස්)', clean):
            return 'edit'
        if re.search(r'\b(add|append|replace|change|update|sign as|my name|mage nama|name eka|antimata|anthimata|ekathu|wenas|venas)\b|මගේ නම|අන්තිමට|එකතු|වෙනස්', clean):
            return 'edit'
        return None

    def handle(self, text, settings, operation=None):
        operation = operation or self.classify(text)
        sinhala = bool(re.search(r'[\u0D80-\u0DFF]|\b(mage|heta|hadanna|karanna|danna|antimata|anthimata)\b', text, re.I))
        if operation in ['show', 'open']:
            return self.result(self.current(), operation, sinhala)
        existing = self.current() if operation == 'edit' else None
        fields = self._literal_edit(text, existing) if existing else None
        if fields is None and settings.get('llm_provider', 'local_rules') != 'local_rules':
            instruction = (
                'You are an email drafting editor. Return ONLY a JSON object with exactly recipient, subject, body, signature string fields. '
                'Interpret Sinhala, Singlish and English. Apply the user request to the existing draft when present, retaining all unrelated details. '
                'Never invent email addresses or the user name. Leave unknown recipient/signature empty. '
                'Keep the signature separate from body. Draft in English unless the user requests another language. '
                'Do not send messages or claim a message has been sent. The user will review and open the draft themselves.'
            )
            prompt = json.dumps({'existing_draft': existing, 'user_request': text, 'user_name': settings.get('display_name', '')}, ensure_ascii=False)
            response = self.llm.generate_response(prompt, settings, system_instruction=instruction)
            try:
                clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip())
                fields = json.loads(clean)
                if not isinstance(fields, dict) or any(not isinstance(fields.get(k), str) for k in ['recipient', 'subject', 'body', 'signature']):
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError('The AI returned an invalid draft. Please try again or edit the draft fields directly.') from None
        if fields is None:
            fields = self._local_draft(text, settings) if not existing else None
        if fields is None:
            raise ValueError('Connect Gemini, OpenAI or Ollama in Settings for this natural-language edit. You can also use Subject:, Body:, Recipient:, Sign as…, or Replace “old” with “new”.')
        draft = self.save(fields, create=operation == 'create')
        log_audit('EDIT_EMAIL_DRAFT' if existing else 'CREATE_EMAIL_DRAFT', f"Draft {draft['id']}", 'SUCCESS')
        return self.result(draft, sinhala=sinhala)

    @staticmethod
    def result(draft, operation='edit', sinhala=False):
        if not draft:
            raise ValueError('Create an email draft first.')
        response = 'ඊමේල් draft එක ලෑස්තියි. බලලා වෙනස් කරන්න ඕන දේ මට කියන්න.' if sinhala else 'Email draft is ready. Review it below, or ask me to change it.'
        return {'intent': 'email_draft', 'status': 'SUCCESS', 'response': response, 'spoken_response': response,
                'data': {'email_draft': draft, 'open_requested': operation == 'open'}}

    @staticmethod
    def gmail_url(draft):
        body = draft['body'].rstrip()
        if draft.get('signature'):
            body += '\n\nBest regards,\n' + draft['signature']
        return 'https://mail.google.com/mail/?' + urlencode({'view':'cm', 'fs':'1', 'to':draft['recipient'], 'su':draft['subject'], 'body':body})

    @staticmethod
    def _literal_edit(text, existing):
        if not existing:
            return None
        fields = {k: existing[k] for k in ['recipient', 'subject', 'body', 'signature']}
        direct = re.match(r'^(subject|recipient|body|signature)\s*:\s*(.*)$', text.strip(), re.I | re.S)
        if direct:
            fields[direct[1].lower()] = direct[2]
            return fields
        signature = re.search(r'(?:sign as|my name is|mage nama|name eka|මගේ නම)\s+(.+?)(?:\s+(?:at the end|kiyala|දාන්න|කියලා|add karanna).*)?$', text, re.I)
        if signature:
            fields['signature'] = signature[1].strip(' .')
            return fields
        quoted_name = re.search(r'["“](.+?)["”]\s*(?:kiyala|කියලා)', text, re.I)
        if quoted_name and re.search(r'\b(name|nama|antimata|anthimata)\b|නම|අන්තිමට', text, re.I):
            fields['signature'] = quoted_name[1]
            return fields
        replacement = re.search(r'replace\s+["“\'](.+?)["”\']\s+with\s+["“\'](.+?)["”\']', text, re.I)
        if replacement:
            if replacement[1] not in fields['body']:
                raise ValueError('That text is not in the current draft. Check the draft or use Body: to replace it.')
            fields['body'] = fields['body'].replace(replacement[1], replacement[2])
            return fields
        append = re.match(r'^(?:add|append)\s*:\s*(.+)$', text.strip(), re.I | re.S)
        if append:
            fields['body'] += '\n\n' + append[1]
            return fields
        recipient = re.search(EMAIL, text)
        if recipient and re.search(r'\b(recipient|send to|to address)\b', text, re.I):
            fields['recipient'] = recipient[0]
            return fields
        return None

    @staticmethod
    def _local_draft(text, settings):
        address = re.search(EMAIL, text)
        fields = {'recipient': address[0] if address else '', 'subject':'', 'body':'', 'signature':settings.get('display_name', '')}
        subject = re.search(r'subject\s*:\s*(.+?)(?=\s+(?:body|recipient)\s*:|$)', text, re.I | re.S)
        body = re.search(r'body\s*:\s*(.+)$', text, re.I | re.S)
        if body:
            fields.update(subject=subject[1].strip() if subject else 'Message', body=body[1].strip())
            return fields
        if re.search(r'\b(sick|ill|unwell|asaneepa|asanipa|saneepa na)\b|අසනීප|සනීප නෑ|සනීප නැ', text, re.I):
            day = 'tomorrow' if re.search(r'\b(tomorrow|heta)\b|හෙට', text, re.I) else 'today' if re.search(r'\b(today|ada)\b|අද', text, re.I) else None
            if not day:
                raise ValueError('Tell me which day the sick leave is for, or connect an AI provider for a more detailed draft.')
            fields['subject'] = 'Sick Leave Request'
            fields['body'] = f'Dear Manager,\n\nI am feeling unwell and will be unable to attend work {day}. I would like to request sick leave.\n\nThank you for your understanding.'
            if re.search(r'\b(online|remotely|from home)\b|ඔන්ලයින්|ගෙදර ඉඳන්', text, re.I):
                fields['body'] += '\n\nI am available to work remotely if needed.'
            return fields
        raise ValueError('Connect an AI provider for natural-language email writing, or dictate: draft email subject: … body: …')
