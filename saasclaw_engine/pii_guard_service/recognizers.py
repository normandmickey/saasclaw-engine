"""
Custom Presidio recognizers for patterns spaCy doesn't catch.

Each recognizer wraps the existing regex from the legacy pii_guard module
and exposes it as a Presidio PatternRecognizer.

Entity names are kept in UPPER_CASE (e.g. "SSN", "EMAIL") to match the
original PATTERNS labels used in the legacy regex fallback.
"""

from presidio_analyzer import Pattern, PatternRecognizer


# ── Label constants (must match original PATTERNS labels exactly) ─────────

ENTITY_TO_PLACEHOLDER = {
    "SSN": "{{SSN}}",
    "CREDIT_CARD": "{{CC}}",
    "PHONE": "({{PHONE}})",
    "EMAIL": "{{EMAIL}}",
    "ADDRESS": "{{ADDRESS}}",
    "BANK_ROUTING": "{{ROUTING}}",
    "BANK_ACCOUNT": "{{ACCT}}",
    "SALARY": "{{SALARY}}",
    "DATE_OF_BIRTH": "{{DOB}}",
    "PASSPORT": "{{PASSPORT}}",
    "DRIVER_LICENSE": "{{DL}}",
    "AWS_KEY": "{{AWS_KEY}}",
    "DB_CONNECTION": "{{DB_CONN}}",
    "IP_ADDRESS": "{{IP}}",
}

ENTITY_TO_LABEL = {
    "SSN": "SSN",
    "CREDIT_CARD": "Credit Card",
    "PHONE": "Phone",
    "EMAIL": "Email",
    "ADDRESS": "Address",
    "BANK_ROUTING": "Bank Routing",
    "BANK_ACCOUNT": "Bank Account",
    "SALARY": "Salary",
    "DATE_OF_BIRTH": "Date of Birth",
    "PASSPORT": "Passport",
    "DRIVER_LICENSE": "Driver License",
    "AWS_KEY": "AWS Key",
    "DB_CONNECTION": "Database Connection",
    "IP_ADDRESS": "IP Address",
}


def _pat(regex: str, score: float = 0.85) -> Pattern:
    return Pattern(name=regex[:40], regex=regex, score=score)


def ssn_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="SSN",
        patterns=[_pat(r"(?<!\d)(?!000|666)\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}(?!\d)", 0.95)],
        supported_language="en",
    )


def credit_card_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=[_pat(
            r"(?<!\d)(?:4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}"
            r"|5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}"
            r"|3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}"
            r"|6(?:011|5\d{2})[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})(?!\d)", 0.9)],
        supported_language="en",
    )


def phone_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="PHONE",
        patterns=[_pat(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", 0.7)],
        supported_language="en",
    )


def email_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="EMAIL",
        patterns=[_pat(r"\b[A-Za-z0-9._%+-]+@(?!localhost\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", 0.9)],
        supported_language="en",
    )


def address_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="ADDRESS",
        patterns=[_pat(
            r"\b\d+\s+[A-Za-z0-9\s,.]+(?:St|Street|Ave|Avenue|Blvd|Boulevard"
            r"|Dr|Drive|Ln|Lane|Rd|Road|Ct|Court|Pl|Place|Way|#\d+)\s*,\s*"
            r"[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b", 0.6)],
        supported_language="en",
    )


def routing_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="BANK_ROUTING",
        patterns=[_pat(
            r'(?i)\b(?:routing|aba|bank[_\s-]*routing)[_\s-]*(?:number|no\.?|#)?[\s"]*:?[\s"]*\d{9}\b', 0.8)],
        supported_language="en",
    )


def bank_account_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="BANK_ACCOUNT",
        patterns=[_pat(
            r'(?i)\b(?:account[_\s-]*(?:number|no\.?|#)?)[\s"]*:?\s*"?\d{8,17}\b', 0.8)],
        supported_language="en",
    )


def salary_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="SALARY",
        patterns=[_pat(
            r'(?i)\b(?:salary|annual[_\s-]*salary|base[_\s-]*pay|compensation'
            r"|hourly[_\s-]*rate|wage|pay[_\s-]*rate)[\s\"]*:?\s*\"?[\$]?[\d,]+"
            r"(?:\.\d{2})?(?:\s*(?:per\s*)?(?:year|annum|month|hour|hr))?\b", 0.85)],
        supported_language="en",
    )


def dob_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="DATE_OF_BIRTH",
        patterns=[_pat(
            r"(?i)(?:date[_\s-]*of[_\s-]*birth|dob|born(?:\s+on)?|birth[_\s-]?date|birthday)"
            r'[\s":,]*\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}', 0.85)],
        supported_language="en",
    )


def passport_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="PASSPORT",
        patterns=[_pat(r'(?i)\b(?:passport[_\s-]?(?:number|no\.?|#|id)?)[\s"]:?\s*"?[A-Z]?\d{8,9}\b', 0.8)],
        supported_language="en",
    )


def drivers_license_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="DRIVER_LICENSE",
        patterns=[_pat(
            r"""(?i)\b(?:driver(?:'s|\\')?\s*(?:license|lic(?:ense)?)\s*(?:number|no\.?#)?)\s*:?\s*[A-Z]?\d{7,13}\b""", 0.8)],
        supported_language="en",
    )


def aws_key_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="AWS_KEY",
        patterns=[_pat(r"\bAKIA[0-9A-Z]{16}\b", 0.95)],
        supported_language="en",
    )


def db_connection_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="DB_CONNECTION",
        patterns=[_pat(
            r"(?i)\b(?:mysql|postgres(?:ql)?|mongodb|redis)://"
            r"(?:[\w._-]+(?::[^\s@]+)?|:[^\s@]+)@"
            r"[\w.-]+(?::\d+)?(?:/[\w./-]*)?", 0.9)],
        supported_language="en",
    )


def ip_address_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="IP_ADDRESS",
        patterns=[_pat(
            r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?!\d)", 0.7)],
        supported_language="en",
    )


ALL_CUSTOM_RECOGNIZERS = [
    ssn_recognizer,
    credit_card_recognizer,
    phone_recognizer,
    email_recognizer,
    address_recognizer,
    routing_recognizer,
    bank_account_recognizer,
    salary_recognizer,
    dob_recognizer,
    passport_recognizer,
    drivers_license_recognizer,
    aws_key_recognizer,
    db_connection_recognizer,
    ip_address_recognizer,
]
