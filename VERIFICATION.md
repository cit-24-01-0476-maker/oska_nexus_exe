# Verification and remaining setup

The application now has a shared HTTP error handler, reconnect state snapshots,
notes CRUD, scheduled reminders with completion/deletion and once-only delivery,
multi-step routines, focus timers, actual audit logs, provider error reporting,
and guarded power confirmations. Desktop settings now connect to tray/startup
behavior. The release includes its Python runtime and dependencies.

## Checks

- `npm run build`: TypeScript and production frontend build.
- `npm run lint`: application lint, excluding generated and third-party files.
- `npm run test:backend`: 44 isolated backend tests using temporary databases;
  destructive actions, application launches and audio playback are mocked.
- `cargo check --offline` in `src-tauri`: native shell compilation.
- `.venv\Scripts\python.exe scripts/smoke_backend.py`: launches the packaged
  executable on port 8766 with a temporary database, verifies startup and state,
  settings, microphone/voice enumeration, metrics, routines, notes, reminders,
  and audit routes, then stops it.
- Browser checks: backend connection, Sinhala note creation, reminder creation
  and completion, a complete chat request/reply persisted in history, and
  restoration of all four quick routines after a delayed backend startup.
- Native release launch: dashboard rendered, bundled backend started and connected
  through HTTP/WebSocket, and missing wake configuration reported as SETUP_REQUIRED.

## Setup that requires the user's environment

- Hands-free **Hey Oska** requires a Picovoice AccessKey and a valid custom
  Windows `.ppn` model for that phrase. Missing configuration is reported;
  the engine no longer silently substitutes another wake phrase.
- General AI conversation requires a selected provider, a valid model and
  provider credentials (or a running local Ollama server). Provider calls were
  checked with mocks; live paid provider requests need the user's credentials.
- Speech input tries online Sinhala/English recognition before Faster-Whisper.
  Offline Whisper needs its selected model downloaded once. Neural speech output
  needs internet; Windows SAPI is the offline fallback. Real speech accuracy and
  audibility require a microphone/speakers and a spoken test by the user.
- Reminders fire while OSKA is running. Overdue reminders are delivered on the
  next start. Date/time selections use the machine's local timezone. Title
  parsing supports `in 10 minutes`, `in 2 hours`, `at 5 PM`, and `tomorrow at 9 AM`;
  other phrasing defaults to one hour unless an explicit time is selected.
- Shutdown/restart were tested with mocks, including cancellation, expiry and
  replay protection. No real shutdown/restart was performed.
- Startup and tray settings compile, but a real Windows login cycle and a clean
  machine installer test remain environment checks.

The configured Gemini model is selected in Settings. This installation was
verified with `gemini-3.1-flash-lite`; model availability is account-specific.

## Video-reference update (1.1)

- Focused black-background assistant view with a complete, properly framed cyan
  face; animated mouth nodes and wireframe move together during speech. The
  Dashboard button restores notes, reminders, settings and other existing pages.
- Listening waits for the end of speech (1.3 seconds of silence), with an
  8-second no-speech timeout and a 30-second maximum turn. Stop cancels recording
  and turns off continuous conversation. Noise-only input is not transcribed.
- Email drafts stay local while editing. The assistant keeps the latest draft
  across follow-up commands and app restarts. The editor accepts manual changes;
  an explicit Open in Gmail action opens a compose URL for review and sending.
- Basic offline examples: `draft email subject: Project update body: The prototype
  is ready for review.`, `Sign as Example User`, `Subject: Revised update`,
  `Replace "prototype" with "application"`, `Recipient: example@example.com`.
  The reference's sick-leave scenario also has an offline template for explicit
  today/tomorrow requests in English/Singlish. Natural-language writing and
  open-ended edits require a configured Gemini/OpenAI/Ollama provider.
- Automated tests cover the reference-style draft → signature → replacement
  flow, draft persistence, URL encoding and explicit browser opening, malformed
  AI output, non-email command routing, recording cancellation, long utterances,
  silence and short noise spikes. Browser UI checks verified draft creation and
  follow-up signature editing in an isolated database with audio suppressed.
- No real email was sent. Gmail compose navigation was mocked during automated
  tests. Live provider generation, real speech accuracy, audibility and actual
  hands-free activation still require the user's provider/microphone setup.
- This update produces a **1.1.0 Setup executable**; the previous 1.0.0 MSI is
  retained as the earlier release.

## Sinhala encoding fix (1.1.1)

The reported Windows `charmap` error was reproduced with a CP1252 stdout stream:
Google speech recognition returned Sinhala, then a diagnostic `print` raised
`UnicodeEncodeError` before the transcript could reach command processing.
Backend startup now selects UTF-8 stdout/stderr before importing libraries;
the desktop launcher also sets Python's UTF-8 environment. Speech diagnostics
fall back to ASCII escapes on legacy/closed streams without altering the actual
Sinhala transcript or interrupting recognition.

Regression checks cover online and offline Sinhala under CP1252, real subprocess
startup with redirected streams, UTF-8 byte preservation, recognized Sinhala
reaching command processing and a mocked Gemini response, and Sinhala planning
questions reaching conversation instead of accidentally starting Study Mode.
The focused view links directly to AI Settings and identifies Local Rules mode
as basic commands. Local Rules responses no longer promise unrestricted Sinhala
conversation. A configured provider and live microphone test are still needed
to verify general conversation and real speech accuracy.

## xAI / Grok support (1.1.2)

Settings now includes xAI / Grok with a separate `xai_api_key` and `xai_model`;
switching to xAI does not overwrite the configured Gemini key/model. Requests use
the xAI Responses endpoint, `store: false`, and extract assistant message text
without displaying reasoning items. All provider keys are excluded from settings
WebSocket broadcasts. Missing credentials, authentication failures, timeouts,
empty output and insufficient credits produce explicit errors.

The supplied xAI account returned HTTP 403 stating that it has no credits or
licenses. The key was saved locally for later use; Gemini remains active.
No credits were purchased. Live Grok generation is unverified until account
access is available. Seven additional tests cover the endpoint, dedicated key,
output parsing, structured edits, billing/auth errors, timeouts and redaction.

Primary API reference: https://docs.x.ai/developers/model-capabilities/text/generate-text
