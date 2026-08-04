# Windmill Assessment

### BAND Enterprise Systems

## **Introduction**

This is a practical exercise in building production-quality automation with Windmill. The four problems form a progressive pipeline where each one extends the last: parse and route a real-world event through conditional logic, deliver a notification reliably, write tests to validate your logic, then wire everything into an event-driven flow with an AI layer. We’re evaluating your design decisions for reliability, code clarity, and how you reason about failure and ambiguity. **We are not evaluating whether your submission runs perfectly.**

### **Allowed Resources**

Any online resources may be referenced. The _Windmill documentation_ is your friend — knowing how to read and digest new documentation is part of what we’re assessing. We ask that you refrain from using AI to generate your submissions wholesale. You’re welcome to use it as a thinking aid, but be prepared to explain the reasoning behind your design choices.

**A note on ambiguity:** some requirements below are intentionally open-ended, particularly around error handling. Where we haven’t specified exact behavior, use your judgment and be ready to explain the tradeoffs behind the approach you chose.

## **Background**

Your company runs an infrastructure monitoring system that fires a webhook whenever a service alert is triggered. The following JSON payload is the canonical event shape used across all problems.

```json
{
  "alert_id": "ALT-4892",
  "service": "payments-api",
  "severity": "critical",
  "message": "HTTP 5xx error rate exceeded 5% over a 5-minute window",
  "host": "prod-payments-01",
  "triggered_at": 1742046720
}
```

The three valid values for `severity` are `critical`, `warning`, and `info`. Each maps to a different Slack channel and escalation policy, as specified in Problem 1. This payload is the primary input for all four problems. In Problem 4, the monitoring system can’t yet classify the event on its own: `service` and `severity` arrive as `"unknown"`, and `message` holds a raw log dump or stack trace instead of a short human-readable line. The AI layer is responsible for deriving the real values from that raw text.

## **Problem 1: Parse, Validate, and Route**

**Objective:** Write a _Windmill Script_ (Python) that acts as the entry point for the pipeline: it _receives a raw webhook payload_, validates it, and returns a normalized event object. Then wire that script into a _Windmill Flow_ that uses a _Branch node_ to route the normalized event to the correct destination based on severity.

### **Requirements**

1. Accept a `payload` dict and a `dry_run` boolean (default `False`).

2. Make sure the payload is well-formed before it moves downstream. We’re intentionally not specifying how you should surface invalid input (missing fields, an unrecognized `severity`, etc.) — decide what’s appropriate for a production system and be ready to defend the choice.

3. Log a single `INFO` line that includes `alert_id`, `service`, and `severity`.

4. If `dry_run` is `True`, log a clearly labeled dry-run notice and return `{**payload, "dry_run": True}` immediately, without performing any downstream side-effects.

5. Convert `triggered_at` from a Unix epoch integer to a _UTC ISO-8601_ string (`YYYY-MM-DDTHH:MM:SSZ`).

6. In the Flow, add a Branch node that evaluates `severity` from the script’s output and routes to one of three paths:

| **Severity** | **channel** | **should_page** |
|---|---|---|
| `critical` | `#incidents` | `true` |
| `warning` | `#alerts` | `false` |
| `info` | `#monitoring` | `false` |

7. Each branch path logs an `INFO` line identifying which path was taken, appends `channel` and `should_page` to the event, and returns the enriched dict. The shape must be identical across all three paths.

**Tip:** Flow steps can run an _inline script_ written directly in the editor, or reference an existing _workspace script_ by path. Add your Problem 1 script as the flow’s first step, map flow inputs through the step’s _Input Transforms_ panel using `flow_input.field_name`, and reference its output in later steps with `results.stepN.field_name`. The Branch node evaluates a JavaScript predicate against the prior step’s output, e.g. `results.step1.severity === "critical"`.

### **Expected Output**

The following shows the enriched event for a `critical` alert. The only differences for `warning` and `info` alerts are the values of `channel` and `should_page`, per the table above.

```json
{
  "alert_id": "ALT-4892",
  "service": "payments-api",
  "severity": "critical",
  "message": "HTTP 5xx error rate exceeded 5% over a 5-minute window",
  "host": "prod-payments-01",
  "triggered_at": "2025-03-15T14:32:00Z",
  "channel": "#incidents",
  "should_page": true,
  "dry_run": false
}
```

### **Starter Script**

Create this script in Windmill at path `u/admin/parse_alert`. Implement all `TODO` blocks.

```python
# path: u/admin/parse_alert
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {"alert_id", "service", "severity", "message", "host", "triggered_at"}
VALID_SEVERITIES = {"critical", "warning", "info"}


def main(payload: dict, dry_run: bool = False) -> dict:
    """Validate and normalize an incoming alert webhook payload.

    Args:
        payload: Raw JSON body from the monitoring webhook.
        dry_run: When True, validate and log but skip all side-effects.

    Returns:
        Normalized alert dict with `triggered_at` converted to ISO-8601.
    """
    # TODO: Decide how to validate the payload against REQUIRED_FIELDS and
    # VALID_SEVERITIES, and how to surface a problem to the caller.
    # There's no single required approach here -- use your judgment.

    # TODO: Log INFO containing alert_id, service, and severity.

    # TODO: If dry_run, log a "DRY RUN" notice and return
    # {**payload, "dry_run": True} immediately.

    # TODO: Convert triggered_at (Unix epoch integer) to a UTC ISO-8601 string
    # ending in "Z", e.g. 1742046720 -> "2025-03-15T14:32:00Z".

    # TODO: Return the normalized dict.
    pass
```

## **Problem 2: Stub a Notification Delivery**

**Objective:** Extend the flow from Problem 1 with a step that builds the notification that would be sent to the routed channel, and models retry behavior for a flaky network call. This exercise doesn’t use a live Slack workspace, so the REST call itself is stubbed rather than actually made.

### **Requirements**

1. Add a script step to your Problem 1 flow. The step receives the enriched event from the prior branch and accepts `dry_run` as a flow-level input.

2. Construct the request body you would send to Slack’s _chat.postMessage_ endpoint, including at minimum `alert_id`, `service`, `severity`, `message`, and `host`.

3. Stub the REST call itself: write a small stand-in function representing the POST request (no live token or network call needed) whose success or failure you control, so you can exercise your retry logic against it.

4. Implement retry logic around that stub: up to **3 attempts**, waiting 2<sup>(_n_−1)</sup> seconds between attempts (1 s, 2 s), logging a `WARNING` on each retry with the attempt number and the error encountered.

5. This step only needs to run in `dry_run` mode for this exercise — log the constructed request (channel and body) and return without attempting a live call.

6. Return a receipt dict containing `ok`, `attempts`, `channel`, and `alert_id`.

### **Expected Output**

```json
{
  "alert_id": "ALT-4892",
  "channel": "#incidents",
  "ok": true,
  "attempts": 1,
  "dry_run": true
}
```

## **Problem 3: Write a CI Test**

**Objective:** Write a Windmill _CI test script_ that covers the core logic of your Problem 1 script. Use the `dry_run` flag to exercise code paths that would otherwise invoke a live service.

**Tip:** Windmill’s CI test pattern works by adding a `test:` annotation to the top of a script, which turns it into a test that runs automatically whenever the tested script or flow is deployed. See the CI test scripts docs for the annotation syntax, the `wmill.run_script` helper, and how results surface on the script’s detail page. _Instant Preview_ and _Test Flows_ are also useful for quick iteration before you formalize things into a CI test.

### **Requirements**

1. Write CI tests as per `TODO` blocks.

### **Starter Test Script**

Create this script in Windmill at path `u/admin/test_parse_alert`. Implement all `TODO` blocks.

```python
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
    pass
```

## **Problem 4: AI-Powered Incident Intelligence**

**Objective:** Build a complete, event-driven Windmill Flow using the same _webhook_ entry point pattern as Problems 1–3, with the same canonical payload shape from the Background section. Here, the upstream monitoring system hasn’t classified the event: `service` and `severity` arrive as `"unknown"`, and `message` holds a raw log dump or stack trace. A Windmill Script step calls an LLM directly through the **OpenAI Python SDK** to derive the real values and generate a diagnostic summary. The flow then routes by severity and delivers a notification enriched with the model’s output.

**Note:** Use the OpenAI Python SDK directly in a script step rather than Windmill’s builtin AI Agent node. This is meant to mirror how AI calls actually get wired into day-to-day automation: picking a model, shaping the request, and enforcing the response shape yourself.

### **Reference: Calling OpenAI from a Windmill Script**

The snippet below is a known-working sanity check for calling the OpenAI SDK from inside a Windmill script, with the API key loaded from a Windmill variable instead of an environment variable. It’s intentionally minimal — it just confirms the SDK, key, and model name all work together. Designing the actual structured extraction call for this problem (Requirement 4) is on you.

```python
import wmill
from openai import OpenAI

api_key = wmill.get_variable("u/admin/openai_key")
client = OpenAI(api_key=api_key)

resp = client.responses.create(
    model="gpt-4.1-mini",
    input="Say 'ok' and return the number 7.",
)

print(resp.output_text)
```

### **Requirements**

1. Configure the flow with a webhook trigger, following the same pattern as Problem 1. The payload uses the same shape as the Background section’s canonical event, with `service` and `severity` set to `"unknown"` and `message` holding the raw log dump or stack trace text.

2. Add a Windmill Python script as the first processing step. Inside it, call the OpenAI Python SDK directly.

3. Deliberately select the least expensive model you believe is still capable of this task, and be ready to explain that choice in your documentation paragraph.

4. Force the model to return a structured object rather than free text – using the SDK’s structured-output or schema-enforcement mechanism, not prompt instructions alone. The object must contain: `service`, `severity` (must be one of `critical`, `warning`, or `info`), `message` (one concise line replacing the raw log text), `summary` (one sentence describing what is happening), and `probable_cause` (one sentence of diagnostic reasoning). Parse and validate the response before using it downstream.

5. Carry `alert_id`, `host`, and `triggered_at` through from the original payload, and feed the model’s corrected fields into your Problem 1 routing logic to branch by severity and append `channel` and `should_page`.

6. Deliver the notification using the stubbed retry pattern from Problem 2, enriching the message with the model-generated `summary` and `probable_cause`.

7. The `dry_run` flag must propagate to every step. When set, no calls are made to the LLM provider or any other external service.

### **Flow Diagram**

`Webhook Trigger (raw payload) -> Script: SDK call (+structured alert) -> Route by Severity (+summary) -> Notify (stubbed)`

### **Mocked Interaction**

**Webhook payload:**

```json
{
  "alert_id": "ALT-7731",
  "service": "unknown",
  "severity": "unknown",
  "message": "ERROR 2025-03-15 14:31:58 payments-api [prod-payments-01] ConnectionPoolTimeoutError: All connections in pool exhausted after 30s. HTTPConnectionPool(host='redis-primary')",
  "host": "prod-payments-01",
  "triggered_at": 1742046720
}
```

### **Expected Output**

```json
{
  "alert_id": "ALT-7731",
  "service": "payments-api",
  "severity": "critical",
  "message": "Redis connection pool exhausted, blocking payments-api requests.",
  "summary": "Redis connection pool exhaustion is causing HTTP 500 errors in payments-api.",
  "probable_cause": "Pool size too small for current traffic; increase max_connections or add a circuit breaker.",
  "host": "prod-payments-01",
  "triggered_at": "2025-03-15T14:32:00Z",
  "channel": "#incidents",
  "should_page": true,
  "dry_run": true
}
```

**Note:** We’ll provide you with an API key before you begin this problem. Create a Windmill variable to store it — something like `u/admin/<variable-name>` — and load it in your script with `wmill.get_variable()`. Contact `ateaminterviewsubmissions@bandwidth.com` if you have any issues with the key.

### **Documentation**

For each problem you attempt, write a short paragraph explaining your thought process. Focus on the _strategic why_ that informed design decisions.

#### **Submitting Your Work**

For each problem, submit one Windmill artifact and one documentation paragraph.

- Flows export as _YAML_ (_Flow Editor → Export_).
- Scripts and test files are plain `.py` files you can copy out of the editor.

Send all artifacts as attachments to `ateaminterviewsubmissions@bandwidth.com` with your name in the subject line.

## **Rubric**

- **Correctness** (4 points): Does the solution address each problem’s requirements? Is the core logic sound?
- **Fault Tolerance** (4 points): Are retries implemented with proper backoff? Does `dry_run` propagate end-to-end? Does a failure in one step leave subsequent steps unaffected?
- **Handling Ambiguity** (3 points): Where requirements were left open-ended, did the candidate make a reasonable, defensible choice and articulate it clearly?
- **Test Quality** (2 points): Does the CI test cover meaningful paths, including at least one malformed-input case? Is `dry_run` used correctly to avoid live calls during testing?
- **Code Quality** (3 points): Are log messages descriptive? Do comments explain intent rather than mechanics? Is the code consistently styled and easy to follow?
- **AI Integration** (2 points): Is the model called directly through its SDK with the response shape enforced, not just prompted? Is the model choice cost-aware and justified?
- **Documentation** (2 points): Do the written paragraphs articulate design decisions and tradeoffs rather than simply describe what each step does?

**Total = 20 points**