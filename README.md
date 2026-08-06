# Bandwidth A-Team Take-Home Assessment

Welcome to my submission for the Windmill Take-Home Assessment! 

This repository contains the complete implementation for Problems 1–4, featuring robust payload validation, exponential backoff retries, CI testing, and an AI-powered intelligence layer.

## Repository Structure

* **`windmill_workspace/admin/`** 
  * This is the exact export of the Windmill workspace. It contains the `.flow.json` and `.script.json` metadata files alongside the Python scripts.
* **`docs/`**
  * Contains `final_submission.md`, which holds all the required written documentation explaining the architectural tradeoffs, design decisions, and ambiguity handling for each problem.
* **`pvr_flow/`** & **`ai_flow/`**
  * Contains neatly organized copies of the raw `.yaml` flow exports and `.py` scripts for quick reading outside of Windmill.


## Design Decisions & Tradeoffs

Please see [docs/final_submission.md](docs/final_submission.md) for the required paragraphs detailing the strategic *why* behind the architecture, including how I handled malformed payloads, stubbed the Slack delivery, and integrated the AI model cost-effectively.

Thank you for your time reviewing my submission!
