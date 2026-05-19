#!/usr/bin/env python3
"""Small local validator for this Agent Skills repo."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
DEPRECATED_AGENT_RE = re.compile(r"https://api\.bolna\.ai/agent(?!/v2|\{)")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening frontmatter marker")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing closing frontmatter marker")
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        data[key.strip()] = value
    return data


def main() -> int:
    failures: list[str] = []
    skill_files = sorted(
        path
        for path in ROOT.glob("*/SKILL.md")
        if path.parent.name not in {"scripts", "references"}
    )
    if not skill_files:
        failures.append("no skill folders found")

    for skill_md in skill_files:
        folder = skill_md.parent.name
        try:
            fm = parse_frontmatter(skill_md)
        except ValueError as exc:
            failures.append(f"{skill_md}: {exc}")
            continue

        name = fm.get("name", "")
        description = fm.get("description", "")

        if name != folder:
            failures.append(f"{skill_md}: name '{name}' must match folder '{folder}'")
        if not NAME_RE.fullmatch(name):
            failures.append(f"{skill_md}: invalid skill name '{name}'")
        if not description:
            failures.append(f"{skill_md}: missing description")
        if len(description) > 1024:
            failures.append(f"{skill_md}: description exceeds 1024 chars")
        if "<" in description or ">" in description:
            failures.append(f"{skill_md}: description should not contain angle brackets")

        text = skill_md.read_text(encoding="utf-8")
        if DEPRECATED_AGENT_RE.search(text):
            failures.append(f"{skill_md}: avoid deprecated https://api.bolna.ai/agent paths")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1

    print(f"OK {len(skill_files)} skills validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
