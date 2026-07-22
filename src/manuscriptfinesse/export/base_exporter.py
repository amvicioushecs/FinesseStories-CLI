from abc import ABC, abstractmethod
import os
from typing import List, Dict, Any, Optional


class BaseExporter(ABC):
    """Abstract base class for all ManuscriptFinesse manuscript exporters."""

    def __init__(self, title: str = "Untitled Manuscript", author: str = "Anonymous"):
        self.title = title
        self.author = author

    def _ensure_output_dir(self, output_path: str) -> None:
        """Ensures destination directory exists before compiling."""
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

    @abstractmethod
    def compile(
        self,
        chapters: List[Dict[str, str]],
        output_path: str,
        front_matter: Optional[Dict[str, str]] = None
    ) -> str:
        """Compiles chapters and front matter into output file at output_path.

        Args:
            chapters: List of dicts, each with "title" and "content".
            output_path: Destination file path.
            front_matter: Optional dict with keys like "foreword", "dedication", "copyright", "about_author", etc.

        Returns:
            The output file path.
        """
        pass
