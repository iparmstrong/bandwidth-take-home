# import wmill
import time
from typing import Any
from httpx import Response
import httpx


def call_slack(body: dict[str, Any], should_fail: bool = False) -> Response:
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

    req_body = {
        "channel": channel,
        "text": f"[{str(severity).upper()}] Alert {alert_id} on {service}: {message}",
        "blocks": [
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
            {
                "type": "section",
                "fields": fields,
            },
        ],
    }

    response = None
    is_ok = False
    for i in range(3):
        try:
            response = call_slack(req_body, should_fail=should_fail)
            response.raise_for_status()
            is_ok = True
            break
        except httpx.HTTPStatusError:
            time.sleep(2**i)

    return {
            "alert_id": alert_id,
            "channel": channel,
            "ok": is_ok,
            "attempts": i + 1,
            "dry_run": dry_run
            }
