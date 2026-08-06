import sys
import logging
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, Field


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Payload(BaseModel):
    alert_id: str = Field(..., min_length=1)
    service: str
    severity: Literal["critical", "warning", "info", "unknown"]
    message: str
    host: str
    triggered_at: str

    model_config = ConfigDict(extra="allow")

    @field_validator("severity", mode="before")
    @classmethod
    def fallback_severity(cls, v: Any) -> str:
        # If it's not one of the explicitly allowed good values, mark as unknown for AI
        if v not in {"critical", "warning", "info"}:
            logger.warning(
                f"Unrecognized severity '{v}', defaulting to 'unknown' for AI classification"
            )
            return "unknown"
        return v

    @field_validator("triggered_at", mode="before")
    @classmethod
    def clean_value(cls, v: Any) -> str:
        if isinstance(v, int):
            dt = datetime.fromtimestamp(v, tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return v


def main(payload: dict[str, Any], dry_run: bool = False):
    logger = logging.getLogger(__name__)

    try:
        validated_payload = Payload(**payload)
    except ValidationError as e:
        logger.error(
            f"Validation failed for payload: {payload}. Errors: {e.json(indent=2, include_url=False)}"
        )
        return {
            "valid": False,
            "error": "validation_failed",
            "details": e.errors(),
            "original_payload": payload,
        }

    logger.info(
        f"alert_id: {validated_payload.alert_id}, service: {validated_payload.service}, severity: {validated_payload.severity}"
    )

    if dry_run:
        logger.info(f"DRY RUN, Exiting")
        return {**validated_payload.model_dump(), "dry_run": True}

    return {**validated_payload.model_dump(), "dry_run": False}
