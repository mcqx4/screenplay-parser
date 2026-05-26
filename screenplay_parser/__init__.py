"""screenplay-parser — parse .fdx and Fountain screenplay files into structured JSON.

Open-sourced by STORYLINER (https://www.storyliner.online).
"""
from .parser import parse, Scene, Script

__version__ = "0.1.0"
__all__ = ["parse", "Scene", "Script"]
