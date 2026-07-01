"""
PII Guard Service — FastAPI microservice wrapping Microsoft Presidio.

Exposes:
  POST /analyze     → detect PII in text
  POST /sanitize    → detect + redact with placeholders
  POST /sanitize/messages → redact LLM message list
  GET  /health      → service health + loaded recognizers
  GET  /patterns    → list active recognizers / entities

Bind to 127.0.0.1:8900 by default (localhost only).
"""

import logging
import os
import time
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer import RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from pydantic import BaseModel, Field

from .recognizers import (
    ALL_CUSTOM_RECOGNIZERS,
    ENTITY_TO_PLACEHOLDER,
    ENTITY_TO_LABEL,
)

logger = logging.getLogger("pii_guard_service")

# ── Config ────────────────────────────────────────────────────────────────

SERVICE_HOST = os.getenv("PII_GUARD_HOST", "127.0.0.1")
SERVICE_PORT = int(os.getenv("PII_GUARD_PORT", "8900"))
SPACY_MODEL = os.getenv("PII_GUARD_SPACY_MODEL", "en_core_web_sm")
MIN_SCORE = float(os.getenv("PII_GUARD_MIN_SCORE", "0.5"))

# ── Models ───────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    text: str
    language: str = "en"
    score_threshold: Optional[float] = None


class AnalyzeMatch(BaseModel):
    entity_type: str = Field(..., alias="entity_type")
    label: str
    match: str
    start: int
    end: int
    score: float
    placeholder: str


class SanitizeRequest(BaseModel):
    text: str
    language: str = "en"
    score_threshold: Optional[float] = None


class SanitizeResponse(BaseModel):
    text: str
    redactions: list[dict]


class MessageBlock(BaseModel):
    type: str = "text"
    text: Optional[str] = None
    image_url: Optional[dict] = None


class LLMMessage(BaseModel):
    role: str
    content: str | list[MessageBlock]


class SanitizeMessagesRequest(BaseModel):
    messages: list[LLMMessage]
    language: str = "en"
    score_threshold: Optional[float] = None


class SanitizeMessagesResponse(BaseModel):
    messages: list[dict]
    redactions: list[dict]


class HealthResponse(BaseModel):
    status: str
    spacy_loaded: bool
    spacy_model: str
    recognizer_count: int
    entities: list[str]
    uptime_s: float


class PatternInfo(BaseModel):
    entity: str
    placeholder: str
    source: str  # "presidio_builtin", "spacy_ner", "custom_regex"


# ── Engines (initialized once) ────────────────────────────────────────────

_analyzer: Optional[AnalyzerEngine] = None
_anonymizer: Optional[AnonymizerEngine] = None
_start_time = time.time()


# spaCy NER entities to remove
# All of these either conflict with our custom recognizers or produce
# unwanted false positives (e.g., labels being tagged as ORG/PERSON).
# Users can add PERSON/ORG/LOCATION detection via custom DB patterns
# if they want NER-based name detection.
_REMOVE_NLP_ENTITIES = {
    "PHONE_NUMBER", "EMAIL_ADDRESS", "EMAIL", "CREDIT_CARD",
    "URL", "DATE_TIME", "PERSON", "ORGANIZATION", "LOCATION",
    "NRP", "AGE", "ID",
}


def _load_custom_db_patterns() -> list:
    """Load custom patterns from Django DB and register as Presidio recognizers."""
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saasclaw_engine.config.settings")
        import django
        django.setup()
        from saasclaw_engine.studio_models.models import CustomPiiPattern

        recognizers = []
        for p in CustomPiiPattern.objects.filter(is_active=True):
            try:
                import re as re_mod
                re_mod.compile(p.regex)  # validate
                from presidio_analyzer import Pattern, PatternRecognizer
                entity_name = f"CUSTOM_{p.name.upper().replace(' ', '_')}"
                recog = PatternRecognizer(
                    supported_entity=entity_name,
                    patterns=[Pattern(name=p.name, regex=p.regex, score=0.85)],
                    supported_language="en",
                )
                ENTITY_TO_PLACEHOLDER[recog.supported_entities[0]] = p.placeholder
                recognizers.append(recog)
                logger.info("Loaded custom DB pattern: %s -> %s", p.name, p.placeholder)
            except Exception as e:
                logger.warning("Invalid custom PII pattern '%s': %s", p.name, e)
        return recognizers
    except Exception as e:
        logger.debug("Could not load custom DB patterns (Django may not be configured): %s", e)
        return []


def _init_analyzer():
    """Initialize the Presidio analyzer with spaCy NER + our custom recognizers.

    Uses a clean registry with no Presidio predefined pattern recognizers.
    Adds only the spaCy NLP recognizer (with conflicting entities removed)
    plus all custom regex recognizers from this module.
    """
    global _analyzer

    import spacy

    # Verify spaCy is loaded
    try:
        nlp = spacy.load(SPACY_MODEL)
        logger.info("spaCy model '%s' loaded (%d pipes)", SPACY_MODEL, len(nlp.pipe_names))
    except OSError:
        logger.error(
            "spaCy model '%s' not found. Run: python -m spacy download %s",
            SPACY_MODEL, SPACY_MODEL,
        )
        raise
    except ImportError:
        logger.error("spacy not installed. Install with: pip install spacy")
        raise

    # Build NLP engine from spaCy
    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": SPACY_MODEL}],
        }
    )
    nlp_engine = provider.create_engine()

    # Start with a clean registry (no Presidio built-in pattern recognizers)
    registry = RecognizerRegistry()

    # Add spaCy NLP recognizer, then strip entities we handle with regex
    registry.add_nlp_recognizer(nlp_engine=nlp_engine)
    for recog in registry.get_recognizers("en", ["PERSON", "ORGANIZATION", "LOCATION", "NRP", "AGE", "ID"]):
        filtered = [e for e in recog.supported_entities if e not in _REMOVE_NLP_ENTITIES]
        if len(filtered) < len(recog.supported_entities):
            logger.info("Filtered NLP entities from %s: removed %s", type(recog).__name__, set(recog.supported_entities) - set(filtered))
        recog.supported_entities = filtered

    # Register our custom regex recognizers
    for factory in ALL_CUSTOM_RECOGNIZERS:
        recog = factory()
        registry.add_recognizer(recog)
        logger.debug("Registered recognizer: %s", recog.supported_entities)

    # Register custom DB patterns
    for recog in _load_custom_db_patterns():
        registry.add_recognizer(recog)

    # Build analyzer with our custom registry
    _analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)


def _init_anonymizer():
    """Initialize the Presidio anonymizer."""
    global _anonymizer
    _anonymizer = AnonymizerEngine()


def get_analyzer() -> AnalyzerEngine:
    if _analyzer is None:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    return _analyzer


# ── FastAPI app ───────────────────────────────────────────────────────────

app = FastAPI(
    title="PII Guard Service",
    description="Presidio-based PII detection and sanitization microservice for SaaSClaw",
    version="2.0.0",
)


@app.on_event("startup")
def startup():
    logger.info("Initializing PII Guard service (Presidio + spaCy)...")
    _init_analyzer()
    _init_anonymizer()
    logger.info("PII Guard service ready on %s:%d", SERVICE_HOST, SERVICE_PORT)


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    analyzer = get_analyzer()
    entities = list(analyzer.registry.get_supported_entities())
    return HealthResponse(
        status="ok",
        spacy_loaded=True,
        spacy_model=SPACY_MODEL,
        recognizer_count=len(entities),
        entities=sorted(entities),
        uptime_s=round(time.time() - _start_time, 1),
    )


@app.get("/patterns", response_model=list[PatternInfo])
def patterns():
    """List all active recognizers and their placeholder mappings."""
    result = []
    for entity, placeholder in ENTITY_TO_PLACEHOLDER.items():
        result.append(PatternInfo(entity=entity, placeholder=placeholder, source="custom_regex"))

    # Add NLP-only entities (PERSON, ORG, etc.)
    analyzer = get_analyzer()
    for entity in analyzer.registry.get_supported_entities():
        if entity not in ENTITY_TO_PLACEHOLDER:
            label = ENTITY_TO_LABEL.get(entity, entity.replace("_", " ").title())
            result.append(PatternInfo(
                entity=entity,
                placeholder=f"{{{{{label.upper().replace(' ', '_')}}}}}",
                source="spacy_ner",
            ))
    return result


@app.post("/analyze", response_model=list[AnalyzeMatch])
def analyze(req: AnalyzeRequest):
    """Detect PII entities in text. Returns raw match positions."""
    analyzer = get_analyzer()
    threshold = req.score_threshold if req.score_threshold is not None else MIN_SCORE

    results = analyzer.analyze(
        text=req.text,
        language=req.language,
        score_threshold=threshold,
    )

    matches = []
    for r in results:
        placeholder = ENTITY_TO_PLACEHOLDER.get(r.entity_type, f"{{{{{r.entity_type}}}}}")
        label = ENTITY_TO_LABEL.get(r.entity_type, r.entity_type.replace("_", " ").title())
        matches.append(AnalyzeMatch(
            entity_type=r.entity_type,
            label=label,
            match=req.text[r.start:r.end],
            start=r.start,
            end=r.end,
            score=round(r.score, 3),
            placeholder=placeholder,
        ))

    return matches


def _sanitize_text(text: str, language: str, threshold: float) -> tuple[str, list[dict]]:
    """Core sanitize logic: detect with Presidio + redact with character-level claim map."""
    analyzer = get_analyzer()

    if not text:
        return text, []

    # Use Presidio analyzer to detect
    results = analyzer.analyze(text=text, language=language, score_threshold=threshold)
    if not results:
        return text, []

    # Build character-level claim map (first match at each position wins)
    claim = [None] * len(text)
    findings = []
    for r in sorted(results, key=lambda x: x.start):
        placeholder = ENTITY_TO_PLACEHOLDER.get(r.entity_type, f"{{{{{r.entity_type}}}}}")
        label = ENTITY_TO_LABEL.get(r.entity_type, r.entity_type.replace("_", " ").title())
        finding = {
            "label": label,
            "match": text[r.start:r.end],
            "start": r.start,
            "end": r.end,
            "placeholder": placeholder,
            "score": round(r.score, 3),
        }
        for i in range(r.start, min(r.end, len(text))):
            if claim[i] is None:
                claim[i] = finding
        findings.append(finding)

    # Walk text, build output
    result_chars = []
    log = []
    i = 0
    while i < len(text):
        if claim[i] is not None:
            finding = claim[i]
            if i == finding["start"]:
                result_chars.append(finding["placeholder"])
                log.append({
                    "label": finding["label"],
                    "placeholder": finding["placeholder"],
                    "original": finding["match"][:50],
                })
            i = finding["end"]
        else:
            result_chars.append(text[i])
            i += 1

    return "".join(result_chars), log


@app.post("/sanitize", response_model=SanitizeResponse)
def sanitize(req: SanitizeRequest):
    """Detect and redact PII from text. Returns sanitized text + redaction log."""
    threshold = req.score_threshold if req.score_threshold is not None else MIN_SCORE
    clean, log = _sanitize_text(req.text, req.language, threshold)

    if log:
        summary = ", ".join(f"{l['label']}({l['placeholder']})" for l in log)
        logger.info("PII redacted: %s", summary)

    return SanitizeResponse(text=clean, redactions=log)


@app.post("/sanitize/messages", response_model=SanitizeMessagesResponse)
def sanitize_messages(req: SanitizeMessagesRequest):
    """Detect and redact PII from an LLM message list (OpenAI format)."""
    threshold = req.score_threshold if req.score_threshold is not None else MIN_SCORE
    all_redactions = []
    sanitized = []

    for msg in req.messages:
        content = msg.content

        if isinstance(content, str):
            clean, redactions = _sanitize_text(content, req.language, threshold)
            all_redactions.extend(redactions)
            sanitized.append({"role": msg.role, "content": clean})
        elif isinstance(content, list):
            clean_blocks = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
                    clean_text, redactions = _sanitize_text(block["text"], req.language, threshold)
                    all_redactions.extend(redactions)
                    clean_blocks.append({**block, "text": clean_text})
                else:
                    clean_blocks.append(block)
            sanitized.append({"role": msg.role, "content": clean_blocks})
        else:
            sanitized.append({"role": msg.role, "content": content})

    return SanitizeMessagesResponse(messages=sanitized, redactions=all_redactions)


# ── Run standalone ───────────────────────────────────────────────────────

def main():
    import uvicorn
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    uvicorn.run(
        "saasclaw_engine.pii_guard_service.app:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        log_level="info",
        workers=1,  # spaCy model is process-local
    )


if __name__ == "__main__":
    main()
