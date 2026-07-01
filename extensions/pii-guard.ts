/**
 * SaaSClaw PII Guard — Pi extension for content-level PII sanitization.
 *
 * Calls the PII Guard microservice (Presidio) over HTTP.
 * Falls back to built-in regex when the service is unreachable.
 *
 * Placement: ~/.pi/agent/extensions/pii-guard.ts (global auto-discovery)
 */

import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { appendFileSync, existsSync, mkdirSync } from "node:fs";
import { join } from "node:path";

// ── Config ──────────────────────────────────────────────────────────────

const SERVICE_URL = process.env.PII_GUARD_URL || "http://127.0.0.1:8900";
const TIMEOUT_MS = 2000;

// ── Types ───────────────────────────────────────────────────────────────

interface Redaction {
  label: string;
  placeholder: string;
  original: string;
}

interface ServiceResponse {
  text: string;
  redactions: Redaction[];
}

// ── Audit Log ───────────────────────────────────────────────────────────

const LOG_DIR = "/var/log/saasclaw";
const LOG_FILE = join(LOG_DIR, "pii-guard.log");

function auditLog(message: string, details?: Record<string, unknown>) {
  const entry = JSON.stringify({
    ts: new Date().toISOString(),
    msg: message,
    ...details,
  });
  if (existsSync(LOG_DIR)) {
    try { appendFileSync(LOG_FILE, entry + "\n"); return; } catch { /* noop */ }
  }
  process.stderr.write(`[pii-guard] ${entry}\n`);
}

// ── Service call ───────────────────────────────────────────────────────

let serviceHealthy: boolean | null = null;

async function callService(text: string): Promise<ServiceResponse | null> {
  if (serviceHealthy === false) return null;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    const resp = await fetch(`${SERVICE_URL}/sanitize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    serviceHealthy = true;
    return await resp.json();
  } catch {
    serviceHealthy = false;
    return null;
  }
}

// ── Regex fallback (mirrors Python pii_guard.py PATTERNS) ──────────────

interface Pattern {
  regex: RegExp;
  placeholder: string;
  label: string;
}

const PATTERNS: Pattern[] = [
  { regex: /\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b/g, placeholder: "{{SSN}}", label: "SSN" },
  { regex: /\b(?:4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}|5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}|3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}|6(?:011|5\d{2})[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})\b/g, placeholder: "{{CC}}", label: "Credit Card" },
  { regex: /\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g, placeholder: "{{PHONE}}", label: "Phone" },
  { regex: /\b[A-Za-z0-9._%+-]+@(?!localhost\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, placeholder: "{{EMAIL}}", label: "Email" },
  { regex: /\b\d+\s+[A-Za-z0-9\s,.]+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Ln|Lane|Rd|Road|Ct|Court|Pl|Place|Way|#\d+)\s*,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b/g, placeholder: "{{ADDRESS}}", label: "Address" },
  { regex: /\b(?:bank[_\s-]*routing|routing[_\s-]*(?:number|no\.?|#)?)\s*:?\s*\d{9}\b/gi, placeholder: "{{ROUTING}}", label: "Bank Routing" },
  { regex: /\b(?:bank[_\s-]*account|account[_\s-]*(?:number|no\.?|#)?)\s*:?\s*\d{8,17}\b/gi, placeholder: "{{ACCT}}", label: "Bank Account" },
  { regex: /date[_\s-]*of[_\s-]*birth[\s":,]*\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}/gi, placeholder: "{{DOB}}", label: "Date of Birth" },
  { regex: /\bdob[\s":,]*\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}\b/gi, placeholder: "{{DOB}}", label: "Date of Birth" },
  { regex: /\b(?:passport[_\s-]?(?:number|no\.?|#|id)?)\s*:?\s*[A-Z]?\d{8,9}\b/gi, placeholder: "{{PASSPORT}}", label: "Passport" },
  { regex: /\b(?:salary|annual[_\s-]*salary|base[_\s-]*pay|compensation|hourly[_\s-]*rate|wage|pay[_\s-]*rate|pay[_\s-]*details|earnings|income)\s*:?\s*\$?[\d,]+(?:\.\d{2})?(?:\s*(?:per\s*)?(?:year|annum|month|hour|hr))?\b/gi, placeholder: "{{SALARY}}", label: "Salary" },
  { regex: /\bAKIA[0-9A-Z]{16}\b/g, placeholder: "{{AWS_KEY}}", label: "AWS Key" },
  { regex: /\b(?:mysql|postgres|postgresql|mongodb|redis):\/\/[^\s:]+:[^\s@]+@[^\s]+\b/gi, placeholder: "{{DB_CONN}}", label: "DB Connection" },
  { regex: /\b(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\b/g, placeholder: "{{IP}}", label: "IP Address" },
];

function sanitizeRegex(text: string): { clean: string; redactions: Redaction[] } {
  const redactions: Redaction[] = [];
  let clean = text;

  for (const pattern of PATTERNS) {
    pattern.regex.lastIndex = 0;
    let match: RegExpExecArray | null;
    const originals: string[] = [];
    while ((match = pattern.regex.exec(clean)) !== null) {
      originals.push(match[0]);
    }
    if (originals.length > 0) {
      pattern.regex.lastIndex = 0;
      clean = clean.replace(pattern.regex, pattern.placeholder);
      for (const orig of originals) {
        redactions.push({
          label: pattern.label,
          placeholder: pattern.placeholder,
          original: orig.substring(0, 50),
        });
      }
    }
  }

  return { clean, redactions };
}

// ── Sanitization (service-first, regex fallback) ────────────────────────

async function sanitizeText(text: string): Promise<{ clean: string; redactions: Redaction[] }> {
  // Try Presidio service first
  const svc = await callService(text);
  if (svc) return { clean: svc.text, redactions: svc.redactions };

  // Fallback to regex
  return sanitizeRegex(text);
}

// ── Extension ───────────────────────────────────────────────────────────

export default function (pi: ExtensionAPI) {
  pi.on("session_start", (_event, ctx) => {
    auditLog("pii-guard loaded", { cwd: ctx.cwd, service: SERVICE_URL });
  });

  // Sanitize messages before each LLM call (context event)
  pi.on("context", async (event, ctx) => {
    const messages = event.messages;
    let totalRedactions = 0;
    const allRedactions: Redaction[] = [];

    for (const message of messages) {
      if (typeof message.content === "string") {
        const { clean, redactions } = await sanitizeText(message.content);
        if (redactions.length > 0) {
          message.content = clean;
          totalRedactions += redactions.length;
          allRedactions.push(...redactions);
        }
      } else if (Array.isArray(message.content)) {
        for (const block of message.content) {
          if (block.type === "text" && typeof block.text === "string") {
            const { clean, redactions } = await sanitizeText(block.text);
            if (redactions.length > 0) {
              block.text = clean;
              totalRedactions += redactions.length;
              allRedactions.push(...redactions);
            }
          }
        }
      }
    }

    if (totalRedactions > 0) {
      const summary = allRedactions.map(r => `${r.label}(${r.placeholder})`).join(", ");
      auditLog("redacted context", { count: totalRedactions, patterns: summary, cwd: ctx.cwd });
      ctx.ui.notify(`🔒 PII Guard: ${totalRedactions} pattern(s) redacted before LLM call`, "info");
    }

    return { messages };
  });

  // Sanitize tool results as they come back
  pi.on("tool_result", async (event, ctx) => {
    if (event.content && Array.isArray(event.content)) {
      let modified = false;
      for (const block of event.content) {
        if (block.type === "text" && typeof block.text === "string") {
          const { clean, redactions } = await sanitizeText(block.text);
          if (redactions.length > 0) {
            block.text = clean;
            modified = true;
            const summary = redactions.map(r => `${r.label}(${r.placeholder})`).join(", ");
            auditLog("redacted tool_result", { tool: event.toolName, count: redactions.length, patterns: summary, cwd: ctx.cwd });
            ctx.ui.notify(`🔒 PII Guard: ${redactions.length} pattern(s) redacted from ${event.toolName}`, "info");
          }
        }
      }
      if (modified) return { content: event.content };
    }
  });
}
