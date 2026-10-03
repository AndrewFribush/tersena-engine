"""Curated Tersena engine extraction with explicit synthetic fixtures."""

from .kb import KB, Record
from .matcher import Match, Matcher
from .parser import ParsedLabel, parse_label

__all__ = ["KB", "Record", "Match", "Matcher", "ParsedLabel", "parse_label"]
