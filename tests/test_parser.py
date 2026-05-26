"""Basic tests for screenplay_parser."""
from screenplay_parser import parse


FOUNTAIN_SAMPLE = """INT. NIGHTSHIFT DINER - 3 AM

The diner is empty except for MARIA, late 30s, hunched over a coffee.

MARIA
Why am I still here?

EXT. STREET - CONTINUOUS

A black sedan rolls past, slows, stops.

DETECTIVE COLE (V.O.)
That was the last time she was seen alive.
"""


def test_fountain_basic():
    script = parse(FOUNTAIN_SAMPLE, format="fountain")
    assert script.total_scenes == 2
    assert script.scenes[0].location == "NIGHTSHIFT DINER"
    assert script.scenes[0].time_of_day == "3 AM"
    assert "MARIA" in script.scenes[0].characters
    assert script.scenes[1].location_type == "EXT"


def test_auto_detect():
    script = parse(FOUNTAIN_SAMPLE)
    assert script.total_scenes == 2


def test_main_characters():
    script = parse(FOUNTAIN_SAMPLE)
    assert "MARIA" in script.main_characters


if __name__ == "__main__":
    test_fountain_basic()
    test_auto_detect()
    test_main_characters()
    print("All tests passed")
