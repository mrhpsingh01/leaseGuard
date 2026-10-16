"""
Tests for Local Regex/NER PII Redactor
"""

from apps.api.services.pii_redactor import PIIRedactorService

def test_pii_redactor_masking_and_hydration():
    redactor = PIIRedactorService()
    sample_text = (
        "Tenant Alex M. Jordan (Phone: (706) 555-0192, Email: alex.jordan@uga.edu, SSN: 123-45-6789) "
        "agrees to lease the premises."
    )

    redacted, log = redactor.redact(sample_text)

    # Assert PII is removed
    assert "Alex M. Jordan" not in redacted
    assert "706" not in redacted
    assert "alex.jordan@uga.edu" not in redacted
    assert "123-45-6789" not in redacted

    # Assert placeholders present
    assert "[TENANT_NAME_1]" in redacted
    assert "[PHONE_1]" in redacted
    assert "[EMAIL_1]" in redacted
    assert "[SSN_1]" in redacted

    # Telemetry verification
    assert log.total_redacted >= 4
    assert log.entity_counts["SSN"] == 1
    assert log.entity_counts["EMAIL"] == 1
    assert log.entity_counts["PHONE"] == 1
    assert log.entity_counts["TENANT_NAME"] >= 1
    assert log.redaction_latency_ms >= 0

    # Hydration verification
    restored = redactor.rehydrate(redacted)
    assert "Alex M. Jordan" in restored
    assert "alex.jordan@uga.edu" in restored
    assert "(706) 555-0192" in restored
    assert "123-45-6789" in restored
