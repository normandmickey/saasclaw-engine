# PII Protection in SaaSClaw Engine

This document describes how the SaaSClaw Engine protects sensitive personal information (PII) from being exposed to LLM providers during the AI agent build process.

## Why This Matters

When an AI coding agent builds an application, it reads project files and sends their contents to an LLM as context. If those files contain real employee data — SSNs, salaries, addresses, health information — that data is transmitted to the LLM provider's servers. This creates compliance risk under HIPAA, GLBA, FERPA, GDPR, state privacy laws, and employer liability frameworks.

SaaSClaw Engine addresses this with two complementary mechanisms: **PII Guard** (content-level sanitization) and **LLM Gateway Mode** (infrastructure-level isolation).

---

## PII Guard

### Overview

PII Guard (`saasclaw_engine.agent.pii_guard`) is a content scanning layer that runs on every message sent to an LLM. It detects sensitive patterns using regular expressions and replaces them with synthetic placeholders before the message reaches the provider.

### Detection Patterns

| Pattern | Example Input | Placeholder | Regex Notes |
|---------|--------------|-------------|-------------|
| SSN | `123-45-6789` | `{{SSN}}` | Validates non-000/666/9xx prefixes, rejects 00 groups |
| Credit Card | `4111-1111-1111-1111` | `{{CC}}` | Visa, Mastercard, Amex, Discover formats |
| Phone Number | `(555) 867-5309` | `(Phone)` | US formats with/without parens, dots, dashes |
| Email | `john@company.com` | `{{EMAIL}}` | Excludes `localhost` |
| Mailing Address | `456 Oak Ave, Springfield, IL 62704` | `{{ADDRESS}}` | Street suffix + city/state/zip pattern |
| Bank Routing | `routing: 021000021` | `{{ROUTING}}` | Requires context keyword (routing/aba/bank) |
| Bank Account | `account: 1234567890123456` | `{{ACCT}}` | Requires context keyword (account) |
| Date of Birth | `DOB: 01/15/1985` | `{{DOB}}` | Requires context keyword (DOB/born/date of birth) |
| Passport | `passport: X12345678` | `{{PASSPORT}}` | Optional leading letter + 8-9 digits |
| Driver License | `driver's license: D123456789` | `{{DL}}` | Requires context keyword |
| Salary | `salary: $85,000 per year` | `{{SALARY}}` | Requires context keyword (salary/wage/compensation/pay) |
| IP Address | `192.168.1.100` | `{{IP}}` | Standard IPv4 format |
| AWS Key | `AKIAIOSFODNN7EXAMPLE` | `{{AWS_KEY}}` | AKIA prefix + 16 alphanumeric chars |
| DB Connection | `postgres://admin:pass@db:5432/mydb` | `{{DB_CONN}}` | mysql/postgres/mongodb/redis URLs with credentials |

### Context-Aware Detection

Some patterns (bank accounts, DOBs, salaries, DLs, passports, routing numbers) require a **context keyword** to avoid false positives. A bare 9-digit number that happens to match a routing number pattern won't be flagged — it needs to appear near "routing", "account", "salary", etc.

This design choice trades some detection coverage for dramatically fewer false positives. In an HR/payroll context, false positives that redact important code values (port numbers, IDs, quantities) are more harmful than missed patterns.

### How It Integrates

**Runner path** (`agent/runner.py`):
```
User prompt → Agent builds message history → PII Guard sanitizes ALL messages → _call_llm() → LLM response
```
The `sanitize_messages()` function processes every message in the conversation history, including tool results that contain file contents. This runs on every LLM round, not just the first prompt.

**PiBridge path** (`agent/pi_bridge.py`):
```
User prompt → PII Guard sanitizes prompt → Pi subprocess (reads files, calls LLM) → Events back
```
The user message is sanitized before reaching Pi. Pi's internal LLM calls are not covered by PII Guard — use LLM Gateway Mode to ensure Pi's LLM stays local.

### Logging

PII Guard logs at two levels:

**`INFO`** — Summary of what was redacted:
```
INFO PII redacted: SSN({{SSN}}), Email({{EMAIL}}), Salary({{SALARY}})
```

**`WARNING`** — Caller-level notification with count:
```
WARNING PII redacted 3 pattern(s) before LLM call in round 2
WARNING PII redacted 5 pattern(s) from PiBridge message
WARNING PII redacted 1 pattern(s) from PiBridge steer
```

The actual sensitive values are **never logged** — only the placeholder types and counts.

### Audit Trail

To build a compliance audit trail, parse your service logs for `PII redacted` entries. Each entry includes:
- Timestamp (from log line)
- Pattern types redacted
- Source (runner round number, PiBridge message, steer)
- Count of redactions

Example log query:
```bash
journalctl -u saasclaw-web.service -u saasclaw-worker.service | grep "PII redacted"
```

---

## LLM Gateway Mode

### Overview

LLM Gateway Mode forces all agent LLM requests for a project through a self-hosted LLM endpoint (vLLM, Ollama, LM Studio, etc.). When enabled, cloud providers (OpenAI, Anthropic, Z.ai, Google, etc.) are blocked at the application level.

This provides **infrastructure-level** PII protection — even if PII Guard misses a pattern, the data still never leaves your server because the LLM call goes to your own hardware.

### Configuration

```python
# settings.py or .env
LLM_GATEWAY_URL = 'http://your-vllm-server:8080/v1'     # OpenAI-compatible endpoint
LLM_GATEWAY_MODEL = 'meta-llama/Llama-3.1-70B-Instruct'  # Model name (or empty for default)
LLM_GATEWAY_BLOCKED_PROVIDERS = ['zai', 'openai', 'anthropic', 'google', 'mistral', 'groq']
```

### Per-Project Toggle

Staff users can enable `require_gateway` on individual projects via the project settings page. The toggle is staff-only — regular users cannot disable it.

When enabled:
1. The resolved provider is checked against `LLM_GATEWAY_BLOCKED_PROVIDERS`
2. If blocked, provider is overridden to `'local'` and model is set to `LLM_GATEWAY_MODEL`
3. The LLM base URL is set to `LLM_GATEWAY_URL`
4. PII Guard still runs as defense-in-depth
5. A `WARNING` is logged: `Gateway required for project <slug>: blocking provider '<provider>', forcing local endpoint`

### vLLM Setup

vLLM exposes an OpenAI-compatible API by default. Start it with:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --host 0.0.0.0 \
  --port 8080
```

Then point `LLM_GATEWAY_URL` to `http://<vllm-ip>:8080/v1`.

---

## Limitations

| Area | Status | Notes |
|------|--------|-------|
| Text PII in prompts | ✅ Covered | Regex-based detection on all message content |
| Text PII in file contents | ✅ Covered | Tool results are sanitized before next LLM round |
| Pi subprocess internal LLM calls | ⚠️ Partial | User message sanitized, but Pi's own file reads and LLM calls happen inside Pi. Use gateway mode for full coverage. |
| Images/screenshots | ❌ Not covered | PII Guard is text-only. Visual PII (photos of documents, screenshots with SSNs) is not detected. |
| Deployed app runtime data | ❌ Out of scope | PII Guard protects the build process. Data in user-built apps is the application's responsibility. |
| Streaming LLM responses | ✅ Covered | Sanitization happens before the call; LLM responses are not re-scanned (they contain placeholders, not real data). |
| Pi subprocess internal LLM calls | ✅ **Now covered** | Pi extension (`pii-guard.ts`) intercepts the `context` and `tool_result` events inside Pi, sanitizing all messages before Pi's internal LLM calls. |
| Images/screenshots | ❌ Not covered | PII Guard is text-only. Visual PII is not detected. |
| Deployed app runtime data | ❌ Out of scope | Data in user-built apps is the application's own responsibility. |

---

## Extending PII Guard

### Adding Custom Patterns

Edit `saasclaw_engine/agent/pii_guard.py` and append to the `PATTERNS` list:

```python
PATTERNS.append((
    re.compile(r'your-pattern-here', re.IGNORECASE),
    '{{PLACEHOLDER}}',
    'Human-Readable Label'
))
```

For the Pi extension, edit `extensions/pii-guard.ts` and add to the `PATTERNS` array.

### Pi Extension (Full Pi Coverage)

Pi has its own internal LLM call path that the engine's PII Guard can't reach directly. The Pi extension (`extensions/pii-guard.ts`) covers this by:

1. Intercepting the `context` event — fires before **every** LLM call inside Pi
2. Intercepting the `tool_result` event — sanitizes tool output as it returns
3. Logging all redactions to stderr and `/var/log/saasclaw/pii-guard.log`

**Install:** Copy to `~/.pi/agent/extensions/pii-guard.ts` (auto-discovered globally).

```bash
mkdir -p ~/.pi/agent/extensions
cp extensions/pii-guard.ts ~/.pi/agent/extensions/pii-guard.ts
```

**Verify:**
```bash
pi -p --no-extensions "Read employees.json"  # PII visible
pi -p "Read employees.json"                    # PII redacted
```

### Disabling PII Guard

To disable PII Guard entirely (not recommended), call the functions with `enabled=False`:

```python
messages, redactions = sanitize_messages(messages, enabled=False)
```

Or remove the Pi extension file.

---

## Compliance Mapping

| Regulation | PII Guard Helps | Gateway Mode Helps | Notes |
|-----------|-----------------|-------------------|-------|
| HIPAA | Yes (PHI patterns) | Yes (data stays local) | Need BAA with LLM provider if not using gateway |
| GLBA | Yes (financial patterns) | Yes | Covers nonpublic personal information |
| FERPA | Partial (no student-specific patterns) | Yes | Add student ID patterns for full coverage |
| GDPR | Yes (broad PII coverage) | Yes | Addresses cross-border transfer concerns |
| BIPA | Partial (no biometric patterns) | Yes | Add face/voice patterns if processing biometrics |
| State laws (CPRA, etc.) | Yes | Yes | Broad coverage for most state requirements |
