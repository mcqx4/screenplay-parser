# screenplay-parser

> Parse Final Draft (`.fdx`) and Fountain screenplay files into structured JSON. Generate shot lists. Built for AI workflows and pre-production tools.

[![PyPI](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What it does

```bash
$ screenplay-parser nightshift.fdx --format json
{
  "scenes": [
    {
      "id": 1,
      "heading": "INT. NIGHTSHIFT DINER - 3 AM",
      "action": "The diner is empty except for MARIA, late 30s...",
      "characters": ["MARIA"],
      "dialogue_count": 4,
      "shot_estimate": 7
    },
    ...
  ],
  "total_scenes": 24,
  "total_pages_estimated": 12,
  "main_characters": ["MARIA", "DETECTIVE COLE", "JANITOR"]
}
```

```bash
$ screenplay-parser nightshift.fdx --shotlist > shots.md
# Generates a markdown shot list grouped by scene
```

## Installation

```bash
pip install screenplay-parser
```

Or from source:

```bash
git clone https://github.com/mcqx4/screenplay-parser
cd screenplay-parser
pip install -e .
```

## Why this exists

Pre-production tools, AI storyboard generators, and screenplay analysis tools all need to parse `.fdx` and Fountain files. The existing libraries are either:

- Tied to a specific framework (Celtx SDK)
- Abandoned (last commit 2019)
- Missing one of the two major formats
- Don't generate structured output usable for downstream tools

This library aims to be the smallest, fastest, dependency-light parser for both formats with sensible JSON output.

## Supported formats

- `.fdx` — Final Draft 8+ XML format
- Fountain — plain-text screenplay format (https://fountain.io/)

Coming soon: Celtx CSV export, raw screenplay text heuristic parser.

## Library use

```python
from screenplay_parser import parse

with open("nightshift.fdx") as f:
    script = parse(f.read(), format="fdx")

for scene in script.scenes:
    print(scene.heading, "—", len(scene.characters), "chars")
```

## Output JSON schema

Every scene returns:

```json
{
  "id": int,
  "heading": str,          // "INT. LOCATION - TIME"
  "location_type": str,    // "INT" or "EXT"
  "location": str,
  "time_of_day": str,      // "DAY", "NIGHT", "3 AM", ...
  "action": str,           // concatenated action lines
  "characters": [str],     // unique characters with dialogue
  "dialogue_count": int,
  "shot_estimate": int     // heuristic: max(action_words/40, dialogue_count)
}
```

## Shot list mode

The `--shotlist` flag outputs a markdown table with shot-type suggestions per scene, based on common conventions:

- Wide shot for scene heading
- Medium shots for action sequences
- OTS / close-up pairs for dialogue
- Insert shots for emphasized props

This is a rough estimate to seed a real shot-listing pass — not a substitute for it.

## Use in AI storyboarding pipelines

This parser is open-sourced by the team behind [**STORYLINER**](https://www.storyliner.online), an AI storyboard generator that turns screenplays into production-quality storyboards in under 2 minutes.

The parser is the same code we use to preprocess scripts before feeding them to our character-memory-conditioned image generation pipeline. We've open-sourced it because every AI pre-production tool needs this layer and there's no good public library.

If you're building an AI tool that touches screenplays, you might find this useful. If you just need storyboards generated from your scripts, try [STORYLINER](https://www.storyliner.online) directly (free tier, no credit card).

## Contributing

PRs welcome. Standard hygiene:

- One feature per PR
- Tests for new parsing paths
- Keep dependencies minimal (currently: zero runtime deps beyond stdlib)

## License

MIT — see [LICENSE](LICENSE).
