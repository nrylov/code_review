#!/usr/bin/env python3
"""
AI code review using the Claude API.

Usage:
    python3 ai_review.py < pr.diff > review.md

Environment variables:
    ANTHROPIC_API_KEY  Required. Your Anthropic API key.
    PR_TITLE           Optional. Title of the pull request.
    PR_BODY            Optional. Description of the pull request.
    MODEL              Optional. Claude model ID (default: claude-sonnet-4-6).

Uses only Python standard library — no pip installs required.
"""

import json
import os
import sys
import urllib.error
import urllib.request


def build_prompt(diff: str, pr_title: str, pr_body: str) -> str:
    context_parts = []
    if pr_title:
        context_parts.append(f"**PR Title:** {pr_title}")
    if pr_body:
        context_parts.append(f"**PR Description:**\n{pr_body}")
    context = "\n".join(context_parts) if context_parts else "(no description provided)"

    return f"""You are an expert software engineer performing a code review. \
Be specific, constructive, and concise.

{context}

**Diff:**
```diff
{diff}
```

Provide a structured review with the following sections. \
If a section has nothing notable, write "Nothing to flag." for that section.

## Summary
One or two sentences describing what this PR does.

## Issues
Bugs, logic errors, or correctness problems. Include file and line references where possible.

## Code Quality
Readability, maintainability, naming, duplication, or structural concerns.

## Security
Any security risks (injection, secret exposure, improper auth, etc.).

## Suggestions
Concrete, actionable improvements the author should consider.
"""


def call_claude(prompt: str, api_key: str, model: str) -> str:
    payload = json.dumps({
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"ERROR: Anthropic API returned {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    return result["content"][0]["text"]


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    model = os.environ.get("MODEL", "claude-sonnet-4-6")
    pr_title = os.environ.get("PR_TITLE", "")
    pr_body = os.environ.get("PR_BODY", "")

    diff = sys.stdin.read().strip()
    if not diff:
        print("ERROR: No diff received on stdin.", file=sys.stderr)
        sys.exit(1)

    prompt = build_prompt(diff, pr_title, pr_body)
    review = call_claude(prompt, api_key, model)
    print(review)


if __name__ == "__main__":
    main()
