"""Turning personas + a questionnaire into survey responses."""

from .heuristic import HeuristicAnswerer
from .runner import generate_responses

__all__ = ["HeuristicAnswerer", "generate_responses"]
