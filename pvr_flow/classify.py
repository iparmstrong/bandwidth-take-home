import sys
import logging
from typing import Any

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(validated_json: dict[str, Any]):
    severity = validated_json.get("severity")
    match severity:
        case "critical":
            logger.info("Routing alert through 'critical' branch -> channel: #incidents, should_page: True")
            return {**validated_json, "should_page": True, "channel": "#incidents"}
        case "warning":
            logger.info("Routing alert through 'warning' branch -> channel: #alerts, should_page: False")
            return {**validated_json, "should_page": False, "channel": "#alerts"}
        case _:
            logger.info("Routing alert through 'info' branch -> channel: #monitoring, should_page: False")
            return {**validated_json, "should_page": False, "channel": "#monitoring"}