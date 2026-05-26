"""Core parsing logic for .fdx (XML) and Fountain (plain text) formats."""
from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from typing import List


SCENE_HEADING_RE = re.compile(
    r"^\s*(INT\.?|EXT\.?|INT/EXT\.?|EXT/INT\.?|I/E\.?)[\s/]",
    re.IGNORECASE
)


@dataclass
class Scene:
    """One scene from a screenplay."""
    id: int
    heading: str = ""
    location_type: str = ""    # "INT" or "EXT"
    location: str = ""
    time_of_day: str = ""
    action: str = ""
    characters: List[str] = field(default_factory=list)
    dialogue_count: int = 0
    shot_estimate: int = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class Script:
    """A parsed screenplay."""
    scenes: List[Scene]
    total_scenes: int = 0
    total_pages_estimated: int = 0
    main_characters: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "scenes": [s.to_dict() for s in self.scenes],
            "total_scenes": self.total_scenes,
            "total_pages_estimated": self.total_pages_estimated,
            "main_characters": self.main_characters,
        }


def _parse_heading(heading: str) -> tuple[str, str, str]:
    """Extract (location_type, location, time_of_day) from a scene heading."""
    h = heading.strip().upper()
    m = re.match(r"^(INT\.?|EXT\.?|INT/EXT\.?|EXT/INT\.?|I/E\.?)\s+(.*)", h)
    if not m:
        return "", heading, ""
    loc_type = m.group(1).rstrip(".").rstrip("/")
    rest = m.group(2)
    # Last dash-separated chunk is time of day
    if " - " in rest:
        loc, tod = rest.rsplit(" - ", 1)
        return loc_type, loc.strip(), tod.strip()
    return loc_type, rest.strip(), ""


def _shot_estimate(action_words: int, dialogue_count: int) -> int:
    """Rough heuristic for number of shots in a scene."""
    base = max(action_words // 40, 1)
    return base + dialogue_count // 2


def parse_fdx(content: str) -> Script:
    """Parse Final Draft .fdx (XML) content."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid .fdx XML: {e}")

    scenes: List[Scene] = []
    current: Scene | None = None
    pending_char: str | None = None
    all_characters: dict[str, int] = {}

    def commit_current():
        if current is None:
            return
        # Compute shot estimate
        action_words = len(current.action.split())
        current.shot_estimate = _shot_estimate(action_words, current.dialogue_count)
        # Decompose heading
        lt, loc, tod = _parse_heading(current.heading)
        current.location_type = lt
        current.location = loc
        current.time_of_day = tod
        # Dedup characters
        current.characters = sorted(set(current.characters))
        scenes.append(current)

    for para in root.iter("Paragraph"):
        ptype = (para.get("Type") or "").strip()
        text_parts = [t.text for t in para.iter("Text") if t.text]
        text = "".join(text_parts).strip()
        if not text:
            continue

        if ptype == "Scene Heading":
            commit_current()
            current = Scene(id=len(scenes) + 1, heading=text)
            pending_char = None
        elif ptype == "Action" and current is not None:
            current.action = (current.action + "\n" + text).strip()
        elif ptype == "Character" and current is not None:
            # Strip parenthetical extensions like "(V.O.)"
            name = re.sub(r"\s*\([^)]*\)\s*$", "", text).strip().upper()
            pending_char = name
            current.characters.append(name)
            all_characters[name] = all_characters.get(name, 0) + 1
        elif ptype == "Dialogue" and current is not None:
            current.dialogue_count += 1
            pending_char = None

    commit_current()

    # Top 8 most-frequent characters as "main"
    main = [c for c, _ in sorted(all_characters.items(),
                                  key=lambda kv: -kv[1])][:8]

    return Script(
        scenes=scenes,
        total_scenes=len(scenes),
        total_pages_estimated=max(1, sum(len(s.action.split()) for s in scenes) // 200),
        main_characters=main,
    )


def parse_fountain(content: str) -> Script:
    """Parse Fountain format screenplay."""
    lines = content.splitlines()
    scenes: List[Scene] = []
    current: Scene | None = None
    in_dialogue_block = False
    last_character: str | None = None
    all_characters: dict[str, int] = {}

    def commit_current():
        if current is None:
            return
        action_words = len(current.action.split())
        current.shot_estimate = _shot_estimate(action_words, current.dialogue_count)
        lt, loc, tod = _parse_heading(current.heading)
        current.location_type = lt
        current.location = loc
        current.time_of_day = tod
        current.characters = sorted(set(current.characters))
        scenes.append(current)

    for raw in lines:
        line = raw.rstrip()
        # Scene heading
        if SCENE_HEADING_RE.match(line) or line.startswith("."):
            commit_current()
            heading = line.lstrip(".").strip()
            current = Scene(id=len(scenes) + 1, heading=heading)
            in_dialogue_block = False
            last_character = None
            continue
        if current is None:
            continue
        # Character cue: uppercase line, no period
        stripped = line.strip()
        if (
            stripped and stripped == stripped.upper()
            and not stripped.startswith("(")
            and not stripped.endswith(".")
            and len(stripped) < 50
            and not SCENE_HEADING_RE.match(stripped)
        ):
            name = re.sub(r"\s*\([^)]*\)\s*$", "", stripped).strip().upper()
            current.characters.append(name)
            all_characters[name] = all_characters.get(name, 0) + 1
            in_dialogue_block = True
            last_character = name
            continue
        # Dialogue line
        if in_dialogue_block and stripped:
            if stripped.startswith("("):
                # parenthetical, skip dialogue count
                continue
            current.dialogue_count += 1
            continue
        # Empty line ends dialogue block
        if not stripped:
            in_dialogue_block = False
            continue
        # Action
        current.action = (current.action + "\n" + stripped).strip()

    commit_current()

    main = [c for c, _ in sorted(all_characters.items(),
                                  key=lambda kv: -kv[1])][:8]
    return Script(
        scenes=scenes,
        total_scenes=len(scenes),
        total_pages_estimated=max(1, sum(len(s.action.split()) for s in scenes) // 200),
        main_characters=main,
    )


def parse(content: str, format: str = "auto") -> Script:
    """Main entry point. format = 'fdx', 'fountain', or 'auto'."""
    if format == "auto":
        if content.lstrip().startswith("<"):
            format = "fdx"
        else:
            format = "fountain"
    if format == "fdx":
        return parse_fdx(content)
    if format == "fountain":
        return parse_fountain(content)
    raise ValueError(f"Unknown format: {format}")
