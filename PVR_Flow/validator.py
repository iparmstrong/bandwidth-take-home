import sys
import logging
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, ValidationError, field_validator
from typing import Literal
from datetime import datetime
import logging
# You can import any PyPi package. 
# See here for more info: https://www.windmill.dev/docs/advanced/dependencies_in_python

# you can use typed resources by doing a type alias to dict
#postgresql = dict


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Payload(BaseModel):
    alert_id: str
    service: str
    severity: Literal["critical", "warning", "info"]
    message: str
    host: str
    triggered_at: str

    @field_validator('triggered_at', mode='before')
    @classmethod
    def clean_value(cls, v: Any) -> str:
        if isinstance(v, int):
            date_str = datetime.fromtimestamp(v).replace(microsecond=0).isoformat()
            return f"{date_str}Z"
        return v

def main(
    payload: dict[str, Any],
    dry_run: bool = False
):
    logger = logging.getLogger(__name__)
    if dry_run:
        logger.info(f"alert_id: {payload.get('alert_id')}, service: {payload.get('service')}, severity: {payload.get('severity')}")
        logger.info(f"DRY RUN, Exiting")
        return {**payload, "dry_run": True}
    try:
        validated_payload = Payload(**payload)
    except ValidationError as e:
        raise ValueError(e.json(indent=2,include_url=False))

    logger.info(f"alert_id: {validated_payload.alert_id}, service: {validated_payload.service}, severity: {validated_payload.severity}")

    return {**validated_payload.model_dump()}
