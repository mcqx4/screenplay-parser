"""Command-line interface for screenplay-parser."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import parse


def render_shotlist_markdown(script) -> str:
    """Render a markdown shot list grouped by scene."""
    lines = ["# Shot List\n"]
    for s in script.scenes:
        lines.append(f"## Scene {s.id}: {s.heading}\n")
        lines.append(f"- **Location:** {s.location or '?'}")
        lines.append(f"- **Time:** {s.time_of_day or '?'}")
        lines.append(f"- **Characters:** {', '.join(s.characters) or '—'}")
        lines.append(f"- **Estimated shots:** {s.shot_estimate}")
        if s.dialogue_count > 0:
            lines.append(f"- **Dialogue exchanges:** {s.dialogue_count}")
        # Suggested shots
        lines.append("\n**Suggested shots:**\n")
        n = max(s.shot_estimate, 1)
        for i in range(n):
            if i == 0:
                lines.append(f"- {s.id}.{chr(65+i)} — WS, establishing")
            elif i == n - 1 and s.dialogue_count > 0:
                lines.append(f"- {s.id}.{chr(65+i)} — CU, emotional beat")
            elif s.dialogue_count > 0 and i % 2 == 1:
                lines.append(f"- {s.id}.{chr(65+i)} — OTS, dialogue")
            else:
                lines.append(f"- {s.id}.{chr(65+i)} — MS, action")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Parse Final Draft (.fdx) and Fountain screenplays into JSON or shot lists.",
    )
    parser.add_argument("file", help="Path to .fdx or .fountain file")
    parser.add_argument("--format", choices=["auto", "fdx", "fountain"],
                        default="auto", help="Input format (default: auto-detect)")
    parser.add_argument("--output", choices=["json", "shotlist", "stats"],
                        default="json", help="Output mode (default: json)")
    parser.add_argument("--pretty", action="store_true",
                        help="Pretty-print JSON output")
    args = parser.parse_args()

    content = Path(args.file).read_text(encoding="utf-8")
    script = parse(content, format=args.format)

    if args.output == "json":
        if args.pretty:
            print(json.dumps(script.to_dict(), indent=2))
        else:
            print(json.dumps(script.to_dict()))
    elif args.output == "shotlist":
        print(render_shotlist_markdown(script))
    elif args.output == "stats":
        print(f"Scenes: {script.total_scenes}")
        print(f"Estimated pages: {script.total_pages_estimated}")
        print(f"Main characters: {', '.join(script.main_characters)}")
        print(f"Total shots estimated: {sum(s.shot_estimate for s in script.scenes)}")


if __name__ == "__main__":
    main()
