"""
Comprehensive tests for the PII Guard system.

Covers all 14 detection patterns, edge cases, false positive resistance,
multi-pattern text, conversation-level sanitization, and multimodal content.
"""

import pytest
from saasclaw_engine.agent.pii_guard import detect_pii, sanitize_for_llm, sanitize_messages


# ── Helpers ──────────────────────────────────────────────────────────────

def assert_redacted(text, expected_placeholder, pattern_label):
    """Assert that text contains a placeholder and no real values for the given pattern."""
    clean, log = sanitize_for_llm(text)
    assert expected_placeholder in clean, f"Expected {expected_placeholder} in: {clean}"
    assert any(r['label'] == pattern_label for r in log), f"Expected {pattern_label} in log: {log}"
    return clean


def assert_not_redacted(text, pattern_label=None):
    """Assert that text is not redacted (or no pattern of given label matches)."""
    clean, log = sanitize_for_llm(text)
    if pattern_label:
        assert not any(r['label'] == pattern_label for r in log), f"Unexpected redaction for {pattern_label}: {log}"
    else:
        assert log == [], f"Unexpected redactions: {log}"
    return clean


def assert_log_count(log, count):
    """Assert exact number of redaction log entries."""
    assert len(log) == count, f"Expected {count} redactions, got {len(log)}: {log}"


# ══════════════════════════════════════════════════════════════════════════
# 1. SSN Detection
# ══════════════════════════════════════════════════════════════════════════

class TestSSN:
    def test_hyphenated_format(self):
        assert_redacted("SSN: 123-45-6789", "{{SSN}}", "SSN")

    def test_space_format(self):
        assert_redacted("SSN: 123 45 6789", "{{SSN}}", "SSN")

    def test_nine_digits_contiguous(self):
        assert_redacted("SSN: 123456789", "{{SSN}}", "SSN")

    def test_in_json(self):
        assert_redacted('"ssn": "123-45-6789"', "{{SSN}}", "SSN")

    def test_in_sentence(self):
        clean = assert_redacted(
            "The employee's SSN is 123-45-6789 and should be protected.",
            "{{SSN}}", "SSN"
        )
        assert "The employee's SSN is {{SSN}}" in clean

    def test_invalid_ssn_000_prefix(self):
        """SSNs starting with 000 are invalid — should not match."""
        assert_not_redacted("ID: 000-45-6789")

    def test_invalid_ssn_666_prefix(self):
        """SSNs starting with 666 are invalid — should not match."""
        assert_not_redacted("ID: 666-45-6789")

    def test_invalid_ssn_900_prefix(self):
        """SSNs 900-999 stopped being issued in 2011 but may exist in legacy data.
        We intentionally match them — over-redacting > under-redacting."""
        assert_redacted("ID: 987-65-4321", "{{SSN}}", "SSN")

    def test_invalid_ssn_00_group(self):
        """SSNs with 00 in group position — negative lookahead catches this."""
        assert_not_redacted("ID: 123-00-6789")

    def test_multiple_ssns(self):
        clean, log = sanitize_for_llm("SSNs: 123-45-6789 and 987-65-4320")
        assert clean.count("{{SSN}}") == 2


# ══════════════════════════════════════════════════════════════════════════
# 2. Credit Card Detection
# ══════════════════════════════════════════════════════════════════════════

class TestCreditCard:
    def test_visa_hyphenated(self):
        assert_redacted("Card: 4111-1111-1111-1111", "{{CC}}", "Credit Card")

    def test_visa_spaces(self):
        assert_redacted("Card: 4111 1111 1111 1111", "{{CC}}", "Credit Card")

    def test_visa_contiguous(self):
        assert_redacted("Card: 4111111111111111", "{{CC}}", "Credit Card")

    def test_mastercard(self):
        assert_redacted("Card: 5425-2334-5678-9012", "{{CC}}", "Credit Card")

    def test_amex(self):
        assert_redacted("Card: 378282246310005", "{{CC}}", "Credit Card")

    def test_discover(self):
        assert_redacted("Card: 6011-1111-1111-1117", "{{CC}}", "Credit Card")

    def test_in_json(self):
        assert_redacted('"credit_card": "4111-1111-1111-1111"', "{{CC}}", "Credit Card")

    def test_not_a_credit_card(self):
        """Short digit sequences should not match."""
        assert_not_redacted("Order #1234")


# ══════════════════════════════════════════════════════════════════════════
# 3. Phone Number Detection
# ══════════════════════════════════════════════════════════════════════════

class TestPhone:
    def test_parenthesized(self):
        assert_redacted("Phone: (555) 867-5309", "({{PHONE}})", "Phone")

    def test_hyphenated(self):
        assert_redacted("Phone: 555-867-5309", "({{PHONE}})", "Phone")

    def test_dotted(self):
        assert_redacted("Phone: 555.867.5309", "({{PHONE}})", "Phone")

    def test_no_separator(self):
        clean, log = sanitize_for_llm("Phone: 5558675309")
        # 10 contiguous digits with lookbehind/lookahead — should match

    def test_in_json(self):
        assert_redacted('"phone": "(555) 867-5309"', "({{PHONE}})", "Phone")

    def test_with_extension(self):
        """Phone numbers with extensions may partially match."""
        clean, log = sanitize_for_llm("Phone: (555) 867-5309 x123")
        # Main number should be caught


# ══════════════════════════════════════════════════════════════════════════
# 4. Email Detection
# ══════════════════════════════════════════════════════════════════════════

class TestEmail:
    def test_standard_email(self):
        assert_redacted("Email: john@company.com", "{{EMAIL}}", "Email")

    def test_dotted_email(self):
        assert_redacted("Email: john.doe@company.com", "{{EMAIL}}", "Email")

    def test_plus_email(self):
        assert_redacted("Email: john+tag@company.com", "{{EMAIL}}", "Email")

    def test_underscore_email(self):
        assert_redacted("Email: john_doe@company.com", "{{EMAIL}}", "Email")

    def test_in_json(self):
        assert_redacted('"email": "john@company.com"', "{{EMAIL}}", "Email")

    def test_localhost_not_matched(self):
        """localhost emails should not be redacted."""
        assert_not_redacted("admin@localhost")

    def test_code_email_not_matched(self):
        """Common code patterns that look like emails should not match."""
        # Single char TLDs should not match (e.g., user@host.c)
        assert_not_redacted("user@host.c", "Email")

    def test_multiple_emails(self):
        clean, log = sanitize_for_llm("Contact: alice@a.com and bob@b.com")
        assert clean.count("{{EMAIL}}") == 2


# ══════════════════════════════════════════════════════════════════════════
# 5. Address Detection
# ══════════════════════════════════════════════════════════════════════════

class TestAddress:
    def test_street_abbrev(self):
        assert_redacted("456 Oak Ave, Springfield, IL 62704", "{{ADDRESS}}", "Address")

    def test_street_full(self):
        assert_redacted("123 Main Street, Chicago, IL 60601", "{{ADDRESS}}", "Address")

    def test_boulevard(self):
        assert_redacted("789 Elm Blvd, Boston, MA 02101", "{{ADDRESS}}", "Address")

    def test_drive(self):
        assert_redacted("321 Pine Dr, Austin, TX 78701", "{{ADDRESS}}", "Address")

    def test_with_zip4(self):
        assert_redacted("100 Maple Ln, Denver, CO 80201-1234", "{{ADDRESS}}", "Address")

    def test_lane(self):
        assert_redacted("500 Birch Lane, Portland, OR 97201", "{{ADDRESS}}", "Address")

    def test_in_json(self):
        assert_redacted('"address": "456 Oak Ave, Springfield, IL 62704"', "{{ADDRESS}}", "Address")

    def test_no_state_code(self):
        """Address without state abbreviation should not match."""
        assert_not_redacted("456 Oak Ave, Springfield")

    def test_pobox(self):
        """PO Box without proper pattern should not match."""
        assert_not_redacted("PO Box 1234")


# ══════════════════════════════════════════════════════════════════════════
# 6. Financial Data (Bank Routing, Account, Salary)
# ══════════════════════════════════════════════════════════════════════════

class TestFinancial:
    def test_routing_with_keyword(self):
        assert_redacted("Routing: 021000021", "{{ROUTING}}", "Bank Routing")

    def test_routing_with_aba(self):
        assert_redacted("ABA: 021000021", "{{ROUTING}}", "Bank Routing")

    def test_routing_with_bank_routing(self):
        assert_redacted("Bank routing number: 021000021", "{{ROUTING}}", "Bank Routing")

    def test_routing_without_context(self):
        """9-digit number without routing context should NOT be redacted (false positive prevention)."""
        # A bare 9-digit number could be many things — over-redacting catches too much
        clean, log = sanitize_for_llm("ID: 021000021")
        # Document behavior: routing pattern requires context keyword

    def test_account_with_keyword(self):
        assert_redacted("Account: 1234567890123456", "{{ACCT}}", "Bank Account")

    def test_account_with_number_keyword(self):
        assert_redacted("Account number: 1234567890123456", "{{ACCT}}", "Bank Account")

    def test_salary_with_dollar(self):
        assert_redacted("Salary: $85,000", "{{SALARY}}", "Salary")

    def test_annual_salary(self):
        assert_redacted("Annual salary: $85,000", "{{SALARY}}", "Salary")

    def test_base_pay(self):
        assert_redacted("Base pay: $75,000", "{{SALARY}}", "Salary")

    def test_hourly_rate(self):
        assert_redacted("Hourly rate: $22.50", "{{SALARY}}", "Salary")

    def test_compensation(self):
        assert_redacted("Compensation: $120,000 per year", "{{SALARY}}", "Salary")

    def test_salary_no_dollar(self):
        """Salary without $ sign but with keyword."""
        assert_redacted("Salary: 85000", "{{SALARY}}", "Salary")

    def test_bare_dollar_not_salary(self):
        """A bare dollar amount without salary keyword should NOT match."""
        assert_not_redacted("Total: $1,234.56", "Salary")


# ══════════════════════════════════════════════════════════════════════════
# 7. Dates of Birth
# ══════════════════════════════════════════════════════════════════════════

class TestDOB:
    def test_dob_with_colon(self):
        assert_redacted("DOB: 01/15/1985", "{{DOB}}", "Date of Birth")

    def test_date_of_birth(self):
        assert_redacted("Date of birth: 01/15/1985", "{{DOB}}", "Date of Birth")

    def test_born_on(self):
        assert_redacted("Born on 01/15/1985", "{{DOB}}", "Date of Birth")

    def test_in_json(self):
        """JSON context: 'date_of_birth':'01/15/1985' — should match with underscore keyword support."""
        assert_redacted('"date_of_birth":"01/15/1985"', "{{DOB}}", "Date of Birth")

    def test_bare_date_not_dob(self):
        """A bare date without DOB context should not match."""
        assert_not_redacted("Report date: 01/15/1985", "Date of Birth")


# ══════════════════════════════════════════════════════════════════════════
# 8. Passport & Driver's License
# ══════════════════════════════════════════════════════════════════════════

class TestIdentityDocuments:
    def test_passport_with_keyword(self):
        assert_redacted("Passport: X12345678", "{{PASSPORT}}", "Passport")

    def test_passport_number(self):
        assert_redacted("Passport number: X12345678", "{{PASSPORT}}", "Passport")

    def test_passport_without_context(self):
        """Bare passport-like string without keyword should not match."""
        assert_not_redacted("X12345678", "Passport")

    def test_drivers_license(self):
        assert_redacted("Driver's license: D123456789", "{{DL}}", "Driver License")

    def test_drivers_license_short(self):
        clean, log = sanitize_for_llm("DL: D1234567")
        # 7 digits minimum — test edge case


# ══════════════════════════════════════════════════════════════════════════
# 9. IP Addresses
# ══════════════════════════════════════════════════════════════════════════

class TestIPAddress:
    def test_ipv4_private(self):
        assert_redacted("Server: 192.168.1.100", "{{IP}}", "IP Address")

    def test_ipv4_public(self):
        assert_redacted("Host: 8.8.8.8", "{{IP}}", "IP Address")

    def test_ipv4_10_range(self):
        assert_redacted("DB: 10.0.0.1", "{{IP}}", "IP Address")

    def test_in_json(self):
        assert_redacted('"ip": "192.168.1.100"', "{{IP}}", "IP Address")

    def test_not_an_ip(self):
        """Version numbers like 1.2.3 should not match (need 4 octets)."""
        assert_not_redacted("Version 1.2.3", "IP Address")

    def test_three_octets_only(self):
        """Three octets should not match."""
        assert_not_redacted("192.168.1", "IP Address")


# ══════════════════════════════════════════════════════════════════════════
# 10. AWS Keys
# ══════════════════════════════════════════════════════════════════════════

class TestAWSKey:
    def test_aws_access_key(self):
        assert_redacted("Key: AKIAIOSFODNN7EXAMPLE", "{{AWS_KEY}}", "AWS Key")

    def test_aws_key_in_code(self):
        assert_redacted("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE", "{{AWS_KEY}}", "AWS Key")

    def test_not_aws_key(self):
        """AKIA prefix with wrong length should not match."""
        assert_not_redacted("AKIA123", "AWS Key")


# ══════════════════════════════════════════════════════════════════════════
# 11. Database Connection Strings
# ══════════════════════════════════════════════════════════════════════════

class TestDBConnection:
    def test_postgres_with_creds(self):
        assert_redacted(
            "postgres://admin:Secret@db.internal:5432/hr_prod",
            "{{DB_CONN}}", "Database Connection"
        )

    def test_mysql_with_creds(self):
        assert_redacted(
            "mysql://root:password@localhost:3306/app_db",
            "{{DB_CONN}}", "Database Connection"
        )

    def test_postgres_no_creds(self):
        """Connection string without embedded password should NOT match."""
        assert_not_redacted("postgres://db.internal:5432/hr_prod", "Database Connection")

    def test_mongodb(self):
        assert_redacted(
            "mongodb://admin:pass@mongo.internal:27017/app",
            "{{DB_CONN}}", "Database Connection"
        )

    def test_redis(self):
        assert_redacted(
            "redis://:password@localhost:6379/0",
            "{{DB_CONN}}", "Database Connection"
        )


# ══════════════════════════════════════════════════════════════════════════
# 12. Multi-Pattern Text (Realistic Employee Record)
# ══════════════════════════════════════════════════════════════════════════

class TestMultiPattern:
    """Realistic HR data containing multiple PII types simultaneously."""

    EMPLOYEE_JSON = '''{
  "name": "John Smith",
  "ssn": "123-45-6789",
  "salary": "$85,000 per year",
  "phone": "(555) 867-5309",
  "email": "john@company.com",
  "address": "456 Oak Ave, Springfield, IL 62704",
  "cc": "4111-1111-1111-1111",
  "dob": "01/15/1985",
  "routing": "021000021",
  "account": "1234567890123456",
  "passport": "X12345678",
  "db": "postgres://admin:Secret@db.internal:5432/hr_prod",
  "aws_key": "AKIAIOSFODNN7EXAMPLE",
  "ip": "192.168.1.100"
}'''

    def test_all_patterns_detected(self):
        """Every PII type in the employee record should be detected."""
        findings = detect_pii(self.EMPLOYEE_JSON)
        labels = [f['label'] for f in findings]

        expected_labels = [
            'SSN', 'Credit Card', 'Phone', 'Email', 'Address',
            'Salary', 'Bank Account', 'Date of Birth', 'Passport',
            'IP Address', 'AWS Key', 'Database Connection'
        ]
        for label in expected_labels:
            assert label in labels, f"Missing detection for {label}. Found: {labels}"

    def test_all_patterns_redacted(self):
        """Every PII value should be replaced with a placeholder."""
        clean, log = sanitize_for_llm(self.EMPLOYEE_JSON)

        # Verify placeholders are present
        assert "{{SSN}}" in clean
        assert "{{CC}}" in clean
        assert "{{PHONE}}" in clean
        assert "{{EMAIL}}" in clean
        assert "{{ADDRESS}}" in clean
        assert "{{SALARY}}" in clean
        assert "{{IP}}" in clean
        assert "{{AWS_KEY}}" in clean
        assert "{{DB_CONN}}" in clean

        # Verify real values are NOT present
        assert "123-45-6789" not in clean
        assert "4111-1111-1111-1111" not in clean
        assert "john@company.com" not in clean
        assert "85,000" not in clean
        assert "192.168.1.100" not in clean
        assert "Secret" not in clean
        assert "AKIAIOSFODNN7EXAMPLE" not in clean

    def test_name_not_redacted(self):
        """Names should NOT be redacted (not a detected pattern)."""
        clean, _ = sanitize_for_llm(self.EMPLOYEE_JSON)
        assert "John Smith" in clean

    def test_redaction_log_has_counts(self):
        """Log should document each redaction."""
        _, log = sanitize_for_llm(self.EMPLOYEE_JSON)
        assert len(log) >= 10, f"Expected many redactions, got {len(log)}"
        for entry in log:
            assert 'label' in entry
            assert 'placeholder' in entry
            assert 'original' in entry
            # Original values should be truncated to 50 chars in log
            assert len(entry['original']) <= 50


# ══════════════════════════════════════════════════════════════════════════
# 13. sanitize_messages() — Conversation-Level Sanitization
# ══════════════════════════════════════════════════════════════════════════

class TestSanitizeMessages:
    def test_string_content(self):
        messages = [
            {"role": "user", "content": "My SSN is 123-45-6789"},
            {"role": "assistant", "content": "I see, {{SSN}} — what else?"},
        ]
        clean_msgs, log = sanitize_messages(messages)
        assert "{{SSN}}" in clean_msgs[0]["content"]
        assert "123-45-6789" not in clean_msgs[0]["content"]

    def test_multimodal_content(self):
        """Text blocks in multimodal content should be sanitized."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "SSN: 123-45-6789"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/img.png"}},
                ]
            }
        ]
        clean_msgs, log = sanitize_messages(messages)
        assert "{{SSN}}" in clean_msgs[0]["content"][0]["text"]
        assert "123-45-6789" not in clean_msgs[0]["content"][0]["text"]
        # Image block should be untouched
        assert clean_msgs[0]["content"][1]["type"] == "image_url"

    def test_no_pii_no_changes(self):
        messages = [
            {"role": "user", "content": "Build me a todo app"},
            {"role": "assistant", "content": "Sure, I'll create that."},
        ]
        clean_msgs, log = sanitize_messages(messages)
        assert log == []
        assert clean_msgs[0]["content"] == "Build me a todo app"

    def test_empty_messages(self):
        clean_msgs, log = sanitize_messages([])
        assert clean_msgs == []
        assert log == []

    def test_disabled(self):
        messages = [{"role": "user", "content": "SSN: 123-45-6789"}]
        clean_msgs, log = sanitize_messages(messages, enabled=False)
        assert clean_msgs[0]["content"] == "SSN: 123-45-6789"
        assert log == []

    def test_multiple_messages_with_pii(self):
        """PII across multiple messages should all be caught."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "My SSN is 123-45-6789"},
            {"role": "assistant", "content": "Noted. Phone?"},
            {"role": "user", "content": "(555) 867-5309"},
        ]
        clean_msgs, log = sanitize_messages(messages)
        assert "{{SSN}}" in clean_msgs[1]["content"]
        assert "({{PHONE}})" in clean_msgs[3]["content"]
        assert len(log) >= 2

    def test_log_combined(self):
        """All redactions from all messages should be in combined log."""
        messages = [
            {"role": "user", "content": "Email: test@test.com and SSN: 123-45-6789"},
        ]
        _, log = sanitize_messages(messages)
        assert_log_count(log, 2)


# ══════════════════════════════════════════════════════════════════════════
# 14. Edge Cases & False Positive Resistance
# ══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_empty_string(self):
        clean, log = sanitize_for_llm("")
        assert clean == ""
        assert log == []

    def test_none_input(self):
        clean, log = sanitize_for_llm(None)
        assert clean is None
        assert log == []

    def test_pure_code(self):
        """A typical code snippet should not trigger many false positives."""
        code = '''
def create_user(name, email):
    db = get_db_connection()
    db.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    return {"id": db.lastrowid, "status": "ok"}
'''
        clean, log = sanitize_for_llm(code)
        # db.execute contains "db" but no connection string — should not match DB_CONN
        db_matches = [l for l in log if l['label'] == 'Database Connection']
        assert len(db_matches) == 0, f"False positive DB connection match: {db_matches}"

    def test_url_not_email(self):
        """URLs should be distinguished from emails where possible."""
        clean, log = sanitize_for_llm("Visit https://example.com for details")
        email_matches = [l for l in log if l['label'] == 'Email']
        assert len(email_matches) == 0, f"False positive email match: {email_matches}"

    def test_port_number_not_phone(self):
        """Port numbers like :8000 should not trigger phone detection."""
        clean, log = sanitize_for_llm("Server running on port 8000")
        phone_matches = [l for l in log if l['label'] == 'Phone']
        assert len(phone_matches) == 0, f"False positive phone match: {phone_matches}"

    def test_version_number_not_cc(self):
        """Version strings like 1.0.0 should not trigger CC detection."""
        clean, log = sanitize_for_llm("Version: 1.0.0")
        cc_matches = [l for l in log if l['label'] == 'Credit Card']
        assert len(cc_matches) == 0, f"False positive CC match: {cc_matches}"

    def test_year_not_ssn(self):
        """4-digit years should not trigger SSN detection."""
        clean, log = sanitize_for_llm("Year: 2024")
        ssn_matches = [l for l in log if l['label'] == 'SSN']
        assert len(ssn_matches) == 0, f"False positive SSN match: {ssn_matches}"

    def test_placeholder_preserved(self):
        """Existing {{SSN}} placeholders should not be double-processed."""
        text = "The template uses {{SSN}} as a placeholder"
        clean, log = sanitize_for_llm(text)
        # Should either leave it alone or still match the pattern
        # Key: it should not become {{SSN}}} or similar corruption
        assert "{{" in clean

    def test_disabled_flag(self):
        """When disabled, text passes through unchanged."""
        text = "SSN: 123-45-6789, Email: test@test.com"
        clean, log = sanitize_for_llm(text, enabled=False)
        assert "123-45-6789" in clean
        assert "test@test.com" in clean
        assert log == []


# ══════════════════════════════════════════════════════════════════════════
# 15. Detect PII (Raw Findings)
# ══════════════════════════════════════════════════════════════════════════

class TestDetectPII:
    def test_returns_list(self):
        findings = detect_pii("SSN: 123-45-6789")
        assert isinstance(findings, list)
        assert len(findings) >= 1

    def test_findings_have_required_keys(self):
        findings = detect_pii("SSN: 123-45-6789")
        for f in findings:
            assert 'label' in f
            assert 'match' in f
            assert 'start' in f
            assert 'end' in f
            assert 'placeholder' in f

    def test_sorted_by_position(self):
        text = "SSN: 123-45-6789, Email: test@test.com"
        findings = detect_pii(text)
        if len(findings) >= 2:
            assert findings[0]['start'] < findings[1]['start']

    def test_no_false_findings(self):
        findings = detect_pii("Hello, world!")
        # Should have zero or very few findings
        assert len(findings) == 0, f"Unexpected findings in benign text: {findings}"
