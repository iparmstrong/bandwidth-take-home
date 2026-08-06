# Combined Documentation Submission

## Problem 1: Parse, Validate, and Route

For payload validation and routing, I implemented a dynamic intelligence approach. If the incoming payload has an unrecognized or missing severity, instead of defaulting it to 'info' or dropping it, the validator actively flags it as unknown. This allows the downstream Windmill flow to easily identify unclassified alerts and route them to the AI enrichment flow for classification. As for the mechanics of validation I implemented a Pydantic validator as it is a robust validation tool that I am familiar with.

For the remaining fields (alert_id, service, message, etc.), I enforce strict validation. An alert missing its ID or message is fundamentally unactionable. However, instead of raising an exception and crashing the pipeline on these malformed payloads, the script catches the validation error and returns a structured object with {"valid": False}. This allows the downstream Windmill Branch node to use an example dead letter queue so engineers can inspect the malformed output without losing data.

## Problem 2: Stub a Notification Delivery

For the notification delivery stub, I had to resolve an ambiguity in the requirements regarding dry_run behavior. The prompt requested that dry_run mode log the constructed request and return without attempting a live call, but also required exercising the retry logic against the stub. I chose to have the dry_run mode log the request but still execute the stubbed function. This ensures no actual live network call is ever made (fulfilling the safety requirement of dry_run), while still allowing the exponential backoff loop (time.sleep(2 ** (attempts - 1))) to execute so the retry mechanism can be validated in the CI test.

As a note on validating the retry logic: rather than passing an artificial should_fail flag through the Windmill flow variables, I implemented a local Python unit test (test_slack_call.py). This test uses unittest.mock.patch to directly intercept the stub and simulate sequential 503 HTTP errors via a side_effect sequence, verifying that the backoff loop functions correctly without polluting the core code.

## Problem 3: Write a CI Test

For the CI testing script, I focused on validating both the happy path and intentional edge cases to ensure the parsing logic is robust.

**Testing Strategy & Tradeoffs:**
1. **Happy Path Validation:** The script passes a valid payload with `dry_run=True` to confirm that all required fields are preserved, the `triggered_at` epoch timestamp is correctly converted to a UTC ISO-8601 string, and the `dry_run` flag is successfully returned in the output without triggering any live side-effects.
2. **Malformed Input:** I designed the `parse_alert` script to gracefully return `{"valid": False, "error": "validation_failed"}` when critical fields like `alert_id` or `service` are missing or empty. The CI tests explicitly exercise these failure modes to ensure bad payloads are caught early and safely trigger a graceful early return in the Windmill flow, rather than crashing the script.
3. **Handling Ambiguity (Unrecognized Severity):** When testing an unrecognized severity value, I made the deliberate design choice to mark the severity as `"unknown"`. Rather than rejecting the event entirely or degrading it to `"info"`, this design guarantees that ambiguous events can be properly routed to the AI flow for dynamic classification, ensuring critical production alerts are never inadvertently suppressed due to a typo.

## Problem 4: AI-Powered Incident Intelligence

For this problem, I designed the AI flow using a Validate-First Subflow Architecture. The flow validates the raw incoming payload before invoking the AI enrichment step, then passes the AI-enriched result into the original pvr_flow (from Problems 1 & 2) as a discrete subflow.

**Architectural Tradeoffs:**
By running the validator (parse_alert) as the first step and branching on its output, completely malformed payloads safely trigger an early return before an OpenAI API call is made. This is highly cost-conscious (no wasted tokens on garbage) and operationally sound. If a message fails validation and cannot be processed it will flow into the same dead letter queue as other failed messages, streamlining review. Once validation passes, the AI enrichment step processes the unclassified payload. The enriched result is then fed into pvr_flow as a subflow, achieving 100% reuse of the existing routing, classification, and notification logic. This guarantees that we don't have to duplicate Slack delivery code while seamlessly integrating the AI output. A negative of this approach is that the validation is ran twice incurring a second python import cost, but compared to calling the AI with bogus data, it is an acceptable tradeoff. While the prompt suggested making the AI script the first processing step, I made the deliberate architectural choice to run the validator first. In a production environment, spending LLM tokens on completely malformed or empty payloads is an unnecessary cost and failure risk. By validating first, we safely drop garbage data before it ever reaches the AI, which I felt was a critical operational improvement. Additionally, I opted to reuse the existing `parse_alert` script as the first step rather than duplicating its Pydantic validation logic inside the AI script. This strictly adheres to DRY (Don't Repeat Yourself) principles, ensuring that if the payload schema changes in the future, the validation logic only needs to be updated in one central location.

**Model Selection:**
I elected to use gpt-5-mini (passed in via static flow input) because it represents the perfect sweet spot for this task. While testing, I found that gpt-5-nano was too small to reliably understand the context and extract the correct information, whereas gpt-5.2 was overkill in terms of cost and latency. gpt-5-mini provides highly reliable JSON structured output enforcement at a fraction of the cost of larger flagship models, making it the ideal choice for high-volume, automated incident classification. Note for gpt-5-mini reasoning was set to minimal to keep speed reasonable. Response times were 8-10s for gpt-5-mini with default reasoning and 4-5s with minimal reasoning.

**Handling Ambiguity:**
The prompt presented a slight contradiction: Problem 4's expected output shows the full enriched payload, while Problem 2 established the contract that the notification stub returns a delivery receipt (`{"ok": true, "attempts": 1...}`). I chose to prioritize the established Problem 2 contract. Returning the delivery receipt at the end of the flow is more valuable for pipeline observability than parroting back the payload, so the flow prioritizes the delivery status while logging the enriched payload internally.
