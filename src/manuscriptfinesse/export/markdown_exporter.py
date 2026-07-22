import re
from typing import List, Dict, Any, Optional
from manuscriptfinesse.export.base_exporter import BaseExporter


def slugify(text: str) -> str:
    """Converts heading text to Markdown anchor slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_]+', '-', text).strip('-')


class MarkdownExporter(BaseExporter):
    """Stage 6 Markdown Exporter compiling a single merged manuscript MD file with TOC and metadata."""

    def compile(
        self,
        chapters: List[Dict[str, str]],
        output_path: str,
        front_matter: Optional[Dict[str, str]] = None
    ) -> str:
        self._ensure_output_dir(output_path)

        lines = []

        # Title & Metadata
        lines.append(f"# {self.title}\n")
        lines.append(f"**Author:** {self.author}\n")

        if front_matter:
            if "copyright" in front_matter:
                lines.append(f"*{front_matter['copyright']}*\n")
            if "dedication" in front_matter:
                lines.append(f"**Dedication:** {front_matter['dedication']}\n")
            if "foreword" in front_matter:
                lines.append("## Foreword\n")
                lines.append(f"{front_matter['foreword']}\n")

        # Table of Contents
        lines.append("## Table of Contents\n")
        for i, ch in enumerate(chapters, start=1):
            title = ch.get("title", f"Chapter {i}")
            slug = slugify(title)
            lines.append(f"- [{title}](#{slug})")
        lines.append("\n---\n")

        # Chapters
        for i, ch in enumerate(chapters, start=1):
            title = ch.get("title", f"Chapter {i}")
            content = ch.get("content", "")

            lines.append(f"# {title}\n")
            lines.append(f"{content}\n")
            lines.append("\n---\n")

        # Back Matter
        if front_matter:
            if "acknowledgments" in front_matter:
                lines.append("## Acknowledgments\n")
                lines.append(f"{front_matter['acknowledgments']}\n")
            if "about_author" in front_matter:
                lines.append("## About the Author\n")
                lines.append(f"{front_matter['about_author']}\n")

        full_md = "\n".join(lines)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_md)

        return output_path
