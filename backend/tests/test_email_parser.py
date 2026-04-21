"""
Unit tests for EmailParserService — only the pattern-matching fallback path
is tested here (no API key required).
"""
import pytest
from app.services.email_parser import EmailParserService, ParsedEmailResult


@pytest.fixture
def parser():
    svc = EmailParserService()
    svc._anthropic = None          # disable Claude
    return svc


# ── _html_to_text ─────────────────────────────────────────────────────────────

def test_html_to_text_strips_tags(parser):
    html = "<p>Hello <b>world</b></p>"
    result = parser._html_to_text(html)
    assert "Hello" in result
    assert "world" in result
    assert "<" not in result


def test_html_to_text_skips_script(parser):
    html = "<p>Visible</p><script>alert('x')</script>"
    result = parser._html_to_text(html)
    assert "Visible" in result
    assert "alert" not in result


# ── _clean_body ───────────────────────────────────────────────────────────────

def test_clean_body_uses_html_when_text_empty(parser):
    result = parser._clean_body("", "<p>From HTML</p>")
    assert "From HTML" in result


def test_clean_body_prefers_plain_text(parser):
    result = parser._clean_body("plain text", "<p>html</p>")
    assert "plain text" in result


def test_clean_body_truncates_at_8000(parser):
    long_text = "x" * 10_000
    result = parser._clean_body(long_text)
    assert len(result) <= 8000


# ── _extract_from_patterns ───────────────────────────────────────────────────

def test_detects_linkedin_source(parser):
    result = parser._extract_from_patterns("", "", "jobs-noreply@linkedin.com")
    assert result["source_platform"] == "linkedin"


def test_detects_naukri_source(parser):
    result = parser._extract_from_patterns("", "Apply via naukri", "noreply@naukri.com")
    assert result["source_platform"] == "naukri"


def test_detects_indeed_source(parser):
    result = parser._extract_from_patterns("", "", "reply@indeed.com")
    assert result["source_platform"] == "indeed"


def test_detects_applied_status(parser):
    result = parser._extract_from_patterns(
        "Thank you for applying to Acme Corp", "", "hr@acme.com"
    )
    assert result["application_status"] == "applied"


def test_detects_interview_status(parser):
    result = parser._extract_from_patterns(
        "Interview invitation for the Software Engineer role", "", "hr@acme.com"
    )
    assert result["application_status"] == "interview"


def test_detects_rejected_status(parser):
    result = parser._extract_from_patterns(
        "Unfortunately we have decided not to move forward", "", "hr@acme.com"
    )
    assert result["application_status"] == "rejected"


def test_detects_offer_status(parser):
    result = parser._extract_from_patterns(
        "Congratulations! We are pleased to offer you the position", "", "hr@acme.com"
    )
    assert result["application_status"] == "offer"


def test_unknown_email_returns_none_status(parser):
    result = parser._extract_from_patterns("Random newsletter", "Buy now!", "news@shop.com")
    assert result["application_status"] is None


# ── pattern_fallback_result ───────────────────────────────────────────────────

def test_fallback_result_is_job_email_when_status_detected(parser):
    result = parser._pattern_fallback_result(
        "Thank you for applying", "", "hr@acme.com", "pattern match"
    )
    assert result.is_job_email is True


def test_fallback_result_not_job_email_when_no_status(parser):
    result = parser._pattern_fallback_result(
        "Weekly digest", "", "news@acme.com", "no match"
    )
    assert result.is_job_email is False


# ── parse_email (async, pattern-only path) ───────────────────────────────────

@pytest.mark.asyncio
async def test_parse_email_fallback_no_ai(parser):
    """When no AI is configured the service returns a pattern-based result."""
    result = await parser.parse_email(
        subject="Interview invitation at Acme",
        from_address="hr@acme.com",
        body="We'd like to schedule an interview with you.",
        date="2024-01-01",
    )
    assert isinstance(result, ParsedEmailResult)
    assert result.application_status == "interview"


@pytest.mark.asyncio
async def test_parse_email_returns_none_for_spam(parser):
    """Completely unrelated emails return a result with is_job_email=False."""
    result = await parser.parse_email(
        subject="50% off shoes today only!",
        from_address="shop@store.com",
        body="Great deals await.",
        date="2024-01-01",
    )
    # Pattern fallback is returned; it just marks is_job_email=False
    assert result is not None
    assert result.is_job_email is False
