import json
import re
from typing import Optional

import httpx
from anthropic import Anthropic

from app.config import get_settings

settings = get_settings()

# Shared system prompt for Claude and Ollama
SYSTEM_PROMPT = """You are an intelligent email parser for a job application tracking system.
Your task is to analyze job-related emails and extract structured information.

Analyze the email carefully and extract:
1. Whether this is a job application-related email
2. The source platform (LinkedIn, Naukri, Indeed, or Unknown)
3. Company name
4. Job position/title
5. Current application status
6. Interview details if mentioned
7. A brief summary of key information
8. Confidence score (0-1)

Respond ONLY in valid JSON format with no additional text."""

USER_PROMPT_TEMPLATE = """
Analyze this job-related email and extract the following information:

Email Subject: {subject}
From: {from_address}
Date: {date}
Body:
{body}

Extract and return a JSON object with these fields:
{{
    "is_job_email": boolean,
    "source_platform": "linkedin" | "naukri" | "indeed" | "unknown",
    "company_name": string or null,
    "position_title": string or null,
    "application_status": "applied" | "screening" | "interview" | "offer" | "rejected" | "accepted" | "update" | null,
    "interview_details": {{
        "date": string or null,
        "time": string or null,
        "format": string or null,
        "location": string or null
    }},
    "key_info_summary": string,
    "confidence_score": number (0-1)
}}

Guidelines:
- is_job_email: true if this is related to job applications, interviews, or hiring
- source_platform: detect from sender domain or content patterns
- application_status: map to standard statuses based on email content
- interview_details: extract if interview is mentioned
- confidence_score: how certain you are about the extraction
"""


class ParsedEmailResult:
    def __init__(
        self,
        is_job_email: bool,
        source_platform: str,
        company_name: Optional[str],
        position_title: Optional[str],
        application_status: Optional[str],
        interview_details: Optional[dict],
        key_info_summary: str,
        confidence_score: float,
    ):
        self.is_job_email = is_job_email
        self.source_platform = source_platform
        self.company_name = company_name
        self.position_title = position_title
        self.application_status = application_status
        self.interview_details = interview_details or {}
        self.key_info_summary = key_info_summary
        self.confidence_score = confidence_score


class EmailParserService:
    def __init__(self):
        self._anthropic: Optional[Anthropic] = None
        if settings.ANTHROPIC_API_KEY:
            self._anthropic = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def _clean_body(self, body: str) -> str:
        """Clean email body for parsing."""
        if not body:
            return ""
        # Remove excessive whitespace
        body = re.sub(r'\s+', ' ', body)
        # Limit length for API
        return body[:8000]

    def _extract_from_patterns(self, subject: str, body: str, from_address: str) -> dict:
        """Extract basic info using regex patterns as fallback."""
        text = f"{subject} {body}".lower()

        # Detect source
        source = "unknown"
        if "linkedin" in from_address.lower() or "linkedin" in text:
            source = "linkedin"
        elif "naukri" in from_address.lower() or "naukri" in text:
            source = "naukri"
        elif "indeed" in from_address.lower() or "indeed" in text:
            source = "indeed"

        # Detect status keywords
        status = None
        status_keywords = {
            "applied": ["application received", "thank you for applying", "application submitted"],
            "screening": ["phone screen", "recruiter", "initial screening", "hr discussion"],
            "interview": ["interview", "schedule", "meeting", "discussion"],
            "offer": ["offer", "congratulations", "pleased to offer", "job offer"],
            "rejected": ["unfortunately", "not selected", "regret to inform", "other candidates"],
            "accepted": ["welcome to", "onboarding", "joined", "start date"],
        }

        for status_key, keywords in status_keywords.items():
            if any(kw in text for kw in keywords):
                status = status_key
                break

        return {
            "source_platform": source,
            "application_status": status,
        }

    def _json_dict_from_llm_text(self, content: str) -> dict:
        json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            raw = json_match.group(1)
        else:
            json_match = re.search(r"({.*})", content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object in model response")
            raw = json_match.group(1)
        return json.loads(raw)

    def _result_from_llm_dict(self, data: dict) -> ParsedEmailResult:
        return ParsedEmailResult(
            is_job_email=data.get("is_job_email", False),
            source_platform=data.get("source_platform", "unknown"),
            company_name=data.get("company_name"),
            position_title=data.get("position_title"),
            application_status=data.get("application_status"),
            interview_details=data.get("interview_details"),
            key_info_summary=data.get("key_info_summary", ""),
            confidence_score=float(data.get("confidence_score", 0.0)),
        )

    def _try_claude(self, prompt: str) -> Optional[ParsedEmailResult]:
        if not self._anthropic:
            return None
        try:
            response = self._anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text
            data = self._json_dict_from_llm_text(content)
            return self._result_from_llm_dict(data)
        except Exception as e:
            print(f"Error parsing email with Claude: {e}")
            return None

    async def _try_ollama(self, prompt: str) -> Optional[ParsedEmailResult]:
        base = (settings.OLLAMA_BASE_URL or "").strip()
        if not base:
            return None
        url = f"{base.rstrip('/')}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        try:
            timeout = httpx.Timeout(120.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                body = response.json()
            text = (body.get("message") or {}).get("content") or ""
            if not text.strip():
                return None
            data = self._json_dict_from_llm_text(text)
            return self._result_from_llm_dict(data)
        except Exception as e:
            print(f"Error parsing email with Ollama: {e}")
            return None

    def _pattern_fallback_result(
        self,
        subject: str,
        body: str,
        from_address: str,
        reason: str,
        confidence_score: float = 0.5,
    ) -> ParsedEmailResult:
        patterns = self._extract_from_patterns(subject, body, from_address)
        return ParsedEmailResult(
            is_job_email=patterns.get("application_status") is not None,
            source_platform=patterns.get("source_platform", "unknown"),
            company_name=None,
            position_title=None,
            application_status=patterns.get("application_status"),
            interview_details=None,
            key_info_summary=reason,
            confidence_score=confidence_score,
        )

    async def parse_email(
        self,
        subject: str,
        from_address: str,
        body: str,
        date: str,
    ) -> Optional[ParsedEmailResult]:
        """Parse email with Claude, then Ollama if configured, then heuristics."""
        cleaned_body = self._clean_body(body)
        prompt = USER_PROMPT_TEMPLATE.format(
            subject=subject,
            from_address=from_address,
            date=date,
            body=cleaned_body,
        )

        claude_result = self._try_claude(prompt)
        if claude_result is not None:
            return claude_result

        ollama_result = await self._try_ollama(prompt)
        if ollama_result is not None:
            return ollama_result

        if not settings.ANTHROPIC_API_KEY and not (settings.OLLAMA_BASE_URL or "").strip():
            return self._pattern_fallback_result(
                subject, body, from_address, "Parsed using pattern matching (no AI configured)"
            )
        return self._pattern_fallback_result(
            subject,
            body,
            from_address,
            "Parsed using pattern matching (AI unavailable or parse failed)",
            confidence_score=0.3,
        )


# Singleton instance
email_parser = EmailParserService()
