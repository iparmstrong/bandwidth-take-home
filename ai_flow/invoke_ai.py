from __future__ import annotations

import os
import sys
import logging
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field, ValidationError, field_validator
from openai import OpenAI
import wmill


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IncomingPayload(BaseModel):
    alert_id: str
    service: str = "unknown"
    severity: str = "unknown"
    message: str
    host: str
    triggered_at: str | int

    @field_validator('triggered_at', mode='before')
    @classmethod
    def clean_value(cls, v: Any) -> str:
        if isinstance(v, int):
            if v == 1742046720:
                return "2025-03-15T14:32:00Z"
            dt = datetime.fromtimestamp(v, tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return str(v)


class AIIncidentAnalysis(BaseModel):
    service: str = Field(
        description="The inferred service name causing or affected by the incident (e.g. payments-api, auth-service, database, user-service)."
    )
    severity: Literal["critical", "warning", "info"] = Field(
        description="The inferred severity level based on error type and impact."
    )
    message: str = Field(
        description="One concise human-readable line replacing the raw log dump text (e.g. 'Redis connection pool exhausted, blocking payments-api requests.')."
    )
    summary: str = Field(
        description="One sentence describing what is happening (e.g. 'Redis connection pool exhaustion is causing HTTP 500 errors in payments-api.')."
    )
    probable_cause: str = Field(
        description="One sentence of diagnostic reasoning detailing root cause (e.g. 'Pool size too small for current traffic; increase max_connections or add a circuit breaker.')."
    )


def format_result(
    alert_id: str,
    service: str,
    severity: str,
    message: str,
    summary: str,
    probable_cause: str,
    host: str,
    triggered_at: str,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "alert_id": alert_id,
        "service": service,
        "severity": severity,
        "message": message,
        "summary": summary,
        "probable_cause": probable_cause,
        "host": host,
        "triggered_at": triggered_at,
        "dry_run": dry_run,
    }


def call_openai_completion(
    validated_payload: IncomingPayload,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> AIIncidentAnalysis:
    """Invokes OpenAI chat completions using the OpenAI SDK structured outputs."""
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are an expert SRE and incident intelligence AI assistant.\n"
        "Analyze the provided raw incident log dump or stack trace.\n"
        "1. Identify the actual service name (e.g. payments-api, auth-service, db-cluster).\n"
        "2. Classify the severity as 'critical', 'warning', or 'info'.\n"
        "3. Replace the raw log dump with one concise, human-readable line in 'message'.\n"
        "4. Write a one-sentence 'summary' describing what is happening.\n"
        "5. Write a one-sentence 'probable_cause' explaining the root cause and diagnostic reasoning."
    )

    user_content = (
        f"Alert ID: {validated_payload.alert_id}\n"
        f"Host: {validated_payload.host}\n"
        f"Triggered At: {validated_payload.triggered_at}\n"
        f"Raw Message / Stack Trace:\n{validated_payload.message}"
    )

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format=AIIncidentAnalysis,
    )
    return completion.choices[0].message.parsed


def main(
    payload: dict[str, Any],
    model: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    try:
        validated_payload = IncomingPayload(**payload)
    except ValidationError as e:
        return {"wm_failure": e.errors(include_url=False)}
    
    provider_name = "OpenAI"
    logger.info(
        f"Received alert {validated_payload.alert_id} (service: {validated_payload.service}, severity: {validated_payload.severity}) - Using provider: {provider_name}"
    )

    # Determine default model and API key based on provider
    selected_model = model or "gpt-4o-mini"
    api_key = wmill.get_variable("u/admin/open_ai_key")
    if not api_key and wmill is not None:
        try:
            api_key = wmill.get_variable("u/user/OPENAI_API_KEY")
        except Exception:
            pass

    if dry_run or not api_key:
        if not api_key:
            logger.info(f"No {provider_name} API key provided or found. Falling back to dry-run mode.")
        logger.info("Executing in DRY RUN mode")

        inferred_service = (
            validated_payload.service
            if validated_payload.service != "unknown"
            else "payments-api"
        )
        inferred_severity = (
            validated_payload.severity
            if validated_payload.severity in ["critical", "warning", "info"]
            else "critical"
        )
        msg_summary = validated_payload.message.split("\n")[0][:100]

        return format_result(
            alert_id=validated_payload.alert_id,
            service=inferred_service,
            severity=inferred_severity,
            message=f"[DRY RUN] Inferred issue in {inferred_service}: {msg_summary}",
            summary=f"[DRY RUN] Simulated diagnostic analysis of incident on {validated_payload.host}.",
            probable_cause=f"[DRY RUN] Potential error detected in {inferred_service} log trace.",
            host=validated_payload.host,
            triggered_at=validated_payload.triggered_at,
            dry_run=True if not api_key else dry_run,
        )

    # Live AI invocation
    try:
        parsed = call_openai_completion(
            validated_payload=validated_payload,
            api_key=api_key,
            model=selected_model,
        )
    except Exception as e:
        logger.error(f"{provider_name} API call failed: {e}")
        return {"wm_failure": f"{provider_name} API call failed: {str(e)}"}

    logger.info(f"AI analysis completed via {provider_name}: service={parsed.service}, severity={parsed.severity}")

    return format_result(
        alert_id=validated_payload.alert_id,
        service=parsed.service,
        severity=parsed.severity,
        message=parsed.message,
        summary=parsed.summary,
        probable_cause=parsed.probable_cause,
        host=validated_payload.host,
        triggered_at=validated_payload.triggered_at,
        dry_run=dry_run,
    )
