# Script Analysis & Sanity Check

## Overview
This document compares the local project scripts (located in `pvr_flow/`, `ai_flow/`, and the root directory) against the exported Windmill scripts located in the `admin/` directory.

Following the recent updates, the exported scripts are now properly synchronized with the local project files. Here is the current state:

## 1. Payload Validation (`pvr_flow/validator.py` vs `admin/parse_alert.py`)
- **Status: Synced & Verified**
- The exported `admin/parse_alert.py` has been updated and now perfectly matches the local `pvr_flow/validator.py`.
- The timestamp formatting bug has been resolved; it now correctly uses `strftime("%Y-%m-%dT%H:%M:%SZ")`.
- It now properly supports the `"unknown"` severity level.

## 2. Slack Integration (`pvr_flow/slack_call.py` vs `admin/slack_call.py`)
- **Status: Synced & Verified**
- The exported `admin/slack_call.py` has been updated and perfectly matches `pvr_flow/slack_call.py`.
- It now properly includes formatting for the AI-generated `summary` and `probable_cause` fields.
- The script now dynamically switches between the live API call and the stub function depending on the environment, fixing the issue where it was unconditionally stubbed.

## 3. Classification Script (`pvr_flow/classify.py` vs `admin/clasify_script.py`)
- **Status: Functionally Synced**
- **Typo in Exported File**: The exported Windmill script is still named `clasify_script.py` (missing an 's'), whereas the local project version is properly named `classify.py`. 
- **Content**: Both scripts are byte-for-byte identical, meaning there are no functional drift issues here.

## 4. AI Flow Script (`ai_flow/invoke_ai.py` vs `admin/ai_flow.flow.json`)
- **Status: Synced (Inline)**
- **Inline Execution**: The AI logic from `ai_flow/invoke_ai.py` is not exported as a standalone script in `admin/`. Instead, it is properly configured as an inline rawscript directly within the flow definition (`admin/ai_flow.flow.json` and `ai_flow/ai_flow.yaml`).
- **Content**: The inline script code in the exported flow perfectly matches the local `ai_flow/invoke_ai.py` file, so there are no drift issues here.
