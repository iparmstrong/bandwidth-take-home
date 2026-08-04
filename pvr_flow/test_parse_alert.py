# test: script/u/admin/parse_alert
import wmill

VALID_PAYLOAD = {
    "alert_id": "ALT-4892",
    "service": "payments-api",
    "severity": "critical",
    "message": "HTTP 5xx error rate exceeded 5% over a 5-minute window",
    "host": "prod-payments-01",
    "triggered_at": 1742046720,
}


def main():
    # TODO: Call u/admin/parse_alert via wmill.run_script with VALID_PAYLOAD
    # and dry_run=True, and assert the output looks the way you expect.

    # TODO: Exercise at least one malformed-input case and assert your
    # Problem 1 script handles it the way you designed it to.
    wmill.run_script_by_path("u/admin/parse_alert", VALID_PAYLOAD)
    pass