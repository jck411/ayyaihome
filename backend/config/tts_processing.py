# config/tts_processing.py
from dataclasses import dataclass, field
from typing import List, Dict
import re

@dataclass
class TTSProcessingConfig:
    minimum_phrase_length: int = 50
    delimiters: List[str] = field(default_factory=lambda: [".", "?", "!"])
    delimiter_regex: str = field(init=False)
    delimiter_pattern: re.Pattern = field(init=False)

    def __post_init__(self):
        escaped_delimiters = ''.join(re.escape(d) for d in self.delimiters)
        self.delimiter_regex = f"[{escaped_delimiters}]"
        self.delimiter_pattern = re.compile(self.delimiter_regex)
