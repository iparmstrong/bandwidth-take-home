# import wmill
import time
import logging
import sys
from typing import Any
import httpx
from httpx import Response

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def call_slack_stub(body: dict[str, Any], should_fail: bool = False) -> Response:
    """Stub representing the POST request to Slack."""
    req = httpx.Request("POST", "https://slack.com/api/chat.postMessage", json=body)
    if should_fail:
        return Response(503, request=req)
    else:
        return Response(200, request=req)

def call_slack(body: dict[str, Any], should_fail: bool = False) -> Response:
    """Stub representing the POST request to Slack."""
    req = httpx.Request("POST", "https://slack.com/api/chat.postMessage", json=body)
    if should_fail:
        return Response(503, request=req)
    else:
        return Response(200, request=req)

def main(
    in_data: dict[str, Any],
    dry_run: bool = False,
    should_fail: bool = False,
    in_CI: bool = False,
):
    alert_id = in_data.get("alert_id")
    service = in_data.get("service")
    severity = in_data.get("severity", "info")
    summary = in_data.get("summary")
    probable_cause = in_data.get("probable_cause")
    message = in_data.get("message")
    host = in_data.get("host")
    triggered_at = in_data.get("triggered_at")
    should_page = in_data.get("should_page")
    channel = in_data.get("channel")

    fields = [
        {"type": "mrkdwn", "text": f"*Service:*\n{service}"},
        {"type": "mrkdwn", "text": f"*Severity:*\n{severity}"},
        {"type": "mrkdwn", "text": f"*Host:*\n{host}"},
        {"type": "mrkdwn", "text": f"*Triggered At:*\n{triggered_at}"},
    ]

    if should_page is not None:
        fields.append({"type": "mrkdwn", "text": f"*Page On-Call:*\n{should_page}"})

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Alert: {alert_id}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{message}*",
            },
        },
    ]

    if summary:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary:*\n{summary}",
            },
        })

    if probable_cause:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Probable Cause:*\n{probable_cause}",
            },
        })

    blocks.append({
        "type": "section",
        "fields": fields,
    })

    req_body = {
        "channel": channel,
        "text": f"[{str(severity).upper()}] Alert {alert_id} on {service}: {message}",
        "blocks": blocks,
    }

    if dry_run:
        logger.info(f"DRY RUN: Constructed request for channel {channel}: {req_body}")
        # Note: The prompt states "This step only needs to run in dry_run mode... log 
        # and return without attempting a live call." We still call the stub to exercise 
        # the retry logic as requested in requirement #3, because the stub IS the 
        # "non-live" call.

    slack_func = call_slack_stub if dry_run or in_CI else call_slack

    response = None
    is_ok = False
    attempts = 0
    max_attempts = 3

    for i in range(max_attempts):
        attempts = i + 1
        try:
            # Dynamically call the appropriate function
            response = slack_func(req_body, should_fail=should_fail)
            response.raise_for_status()
            is_ok = True
            break
        except httpx.HTTPStatusError as e:
            logger.warning(f"Attempt {attempts} failed with error: {e}. Retrying...")
            if attempts < max_attempts:
                # Wait 2^(n-1) seconds: attempts=1 -> 1s, attempts=2 -> 2s
                time.sleep(2 ** (attempts - 1))
            else:
                logger.error(f"Failed to deliver Slack message after {max_attempts} attempts.")

    return {
        "alert_id": alert_id,
        "channel": channel,
        "ok": is_ok,
        "attempts": attempts,
        "dry_run": dry_run
    }
