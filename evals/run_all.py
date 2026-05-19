#!/usr/bin/env python3
"""Lightweight repo-specific checks for the Bolna skills package."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_validator() -> list[str]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_skills.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return [result.stdout.strip(), result.stderr.strip()]
    return []


def check_trigger_cases() -> list[str]:
    failures: list[str] = []
    cases = json.loads((ROOT / "evals" / "trigger_cases.json").read_text())
    for case in cases:
        skill = case["skill"]
        path = ROOT / skill / "SKILL.md"
        if not path.exists():
            failures.append(f"missing skill from trigger cases: {skill}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        description_match = re.search(r"description:\s*[\"']?(.*)", text)
        description = description_match.group(1) if description_match else ""
        for query in case["queries"]:
            tokens = [
                token
                for token in re.findall(r"[a-z0-9]+", query.lower())
                if len(token) > 3 and token not in {"this", "with", "using", "from"}
            ]
            if tokens and not any(token in description or token in text for token in tokens):
                failures.append(f"{skill}: query has no matching trigger terms: {query}")
    return failures


def check_invariants() -> list[str]:
    failures: list[str] = []
    checked_roots = [
        ROOT / "README.md",
        ROOT / ".env.example",
        *sorted(ROOT.glob("*/SKILL.md")),
        *sorted(ROOT.glob("*/references/*.md")),
        *sorted(ROOT.glob("*/assets/*")),
    ]
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in checked_roots
        if path.is_file()
    )
    if "https://api.bolna.ai/agent " in all_text:
        failures.append("deprecated /agent endpoint appears with production host")
    if "phone_number,customer_name" in all_text:
        failures.append("batch CSV should use contact_number, not phone_number")
    if "api.bolna.dev" in all_text:
        failures.append("api.bolna.dev should not be used in production examples")
    if "scheduled_at\\\"" in all_text:
        failures.append("Bolna docs typo scheduled_at\\\" leaked into examples")
    return failures


def main() -> int:
    failures = run_validator() + check_trigger_cases() + check_invariants()
    if failures:
        for failure in failures:
            if failure:
                print(f"FAIL {failure}")
        return 1
    print("OK evals passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
