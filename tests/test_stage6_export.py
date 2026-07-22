import os
import json
import pytest
from manuscriptfinesse.agents.base_agent import BaseAgent
from manuscriptfinesse.agents.polisher import PolisherAgent
from manuscriptfinesse.core.models import StoryBibleSchema, CharacterDossier
from manuscriptfinesse.export.base_exporter import BaseExporter
from manuscriptfinesse.export.epub_exporter import EPUBExporter
from manuscriptfinesse.export.docx_exporter import DOCXExporter
from manuscriptfinesse.export.markdown_exporter import MarkdownExporter
from manuscriptfinesse.providers.base import BaseLLMProvider, MockProvider
import docx
from ebooklib import epub


class CapturingProvider(BaseLLMProvider):
    """Mock LLM provider that captures system and user prompts passed to generate()."""
    def __init__(self, response_text: str = "Polished prose content."):
        self.response_text = response_text
        self.last_system_prompt = ""
        self.last_user_prompt = ""

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.response_text


def test_polisher_agent_subclass():
    """Verify PolisherAgent inherits from BaseAgent."""
    provider = MockProvider()
    agent = PolisherAgent(provider=provider)
    assert isinstance(agent, BaseAgent)


def test_polisher_prose_refinement():
    """Verify polish_chapter includes draft text and canon rules in LLM prompt."""
    provider = CapturingProvider("Polished chapter prose with improved rhythm.")
    agent = PolisherAgent(provider=provider)

    bible = StoryBibleSchema(
        project_title="Caelum Chronicles",
        canon_rules=["No magic allowed in the outer rim"],
        characters=[CharacterDossier(id="char_1", name="Lyra", voice_and_speech="Laconic")]
    )
    draft_text = "Lyra walked into the room slowly. It was dark and cold."

    polished = agent.polish_chapter(draft_text=draft_text, bible=bible)
    assert polished == "Polished chapter prose with improved rhythm."
    assert "Lyra walked into the room slowly." in provider.last_user_prompt
    assert "No magic allowed in the outer rim" in provider.last_user_prompt


def test_polisher_run_method():
    """Verify PolisherAgent run() accepts string or JSON input."""
    provider = MockProvider()
    agent = PolisherAgent(provider=provider)

    # Direct text input
    res1 = agent.run("Draft prose to polish.")
    assert isinstance(res1, str)
    assert len(res1) > 0

    # JSON payload input
    payload = {
        "draft_text": "Draft prose in payload.",
        "bible": StoryBibleSchema(project_title="JSON Test").model_dump()
    }
    res2 = agent.run(json.dumps(payload))
    assert isinstance(res2, str)
    assert len(res2) > 0


def test_base_exporter_abstract():
    """Verify BaseExporter requires compile implementation."""
    with pytest.raises(TypeError):
        BaseExporter()


def test_epub_exporter_compilation(tmp_path):
    """Verify EPUBExporter compiles a valid EPUB file with chapters and front matter."""
    exporter = EPUBExporter(title="The Cipher of Eldoria", author="Jane Doe")

    assert isinstance(exporter, BaseExporter)

    chapters = [
        {"title": "Chapter 1: The Whispering Wind", "content": "The wind howled across the frozen tundra."},
        {"title": "Chapter 2: The Lost Temple", "content": "Ancient stone columns rose into the storm."}
    ]
    front_matter = {
        "foreword": "Welcome to the story.",
        "dedication": "Dedicated to all dreamers.",
        "copyright": "Copyright 2026 Jane Doe",
        "about_author": "Jane Doe is an author."
    }

    out_file = str(tmp_path / "manuscript.epub")
    result_path = exporter.compile(chapters=chapters, output_path=out_file, front_matter=front_matter)

    assert result_path == out_file
    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 0

    # Verify EPUB can be parsed by ebooklib
    book = epub.read_epub(out_file)
    assert book.get_metadata('DC', 'title')[0][0] == "The Cipher of Eldoria"
    assert book.get_metadata('DC', 'creator')[0][0] == "Jane Doe"


def test_docx_exporter_compilation(tmp_path):
    """Verify DOCXExporter compiles a valid DOCX file with 12pt manuscript formatting."""
    exporter = DOCXExporter(title="The Cipher of Eldoria", author="Jane Doe")
    assert isinstance(exporter, BaseExporter)

    chapters = [
        {"title": "Chapter 1: Arrival", "content": "Lyra arrived at the citadel gate.\n\nShe looked up at the ice towers."},
        {"title": "Chapter 2: Descent", "content": "The stairs spiraled into the darkness."}
    ]
    front_matter = {
        "dedication": "For my family.",
        "copyright": "All rights reserved 2026."
    }

    out_file = str(tmp_path / "manuscript.docx")
    result_path = exporter.compile(chapters=chapters, output_path=out_file, front_matter=front_matter)

    assert result_path == out_file
    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 0

    # Verify DOCX can be opened by python-docx and contains expected paragraphs
    doc = docx.Document(out_file)
    texts = [p.text for p in doc.paragraphs]
    full_text = "\n".join(texts)
    assert "The Cipher of Eldoria" in full_text
    assert "Jane Doe" in full_text
    assert "Chapter 1: Arrival" in full_text
    assert "Lyra arrived at the citadel gate." in full_text


def test_markdown_exporter_compilation(tmp_path):
    """Verify MarkdownExporter compiles a single merged manuscript MD file with TOC and metadata."""
    exporter = MarkdownExporter(title="The Cipher of Eldoria", author="Jane Doe")
    assert isinstance(exporter, BaseExporter)

    chapters = [
        {"title": "Chapter 1: First Light", "content": "Sunlight broke through the heavy clouds."},
        {"title": "Chapter 2: Shadows Fall", "content": "Night came swiftly upon the valley."}
    ]
    front_matter = {
        "foreword": "A note on the world.",
        "copyright": "Copyright (c) 2026 Jane Doe"
    }

    out_file = str(tmp_path / "manuscript.md")
    result_path = exporter.compile(chapters=chapters, output_path=out_file, front_matter=front_matter)

    assert result_path == out_file
    assert os.path.exists(out_file)

    with open(out_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "# The Cipher of Eldoria" in md_text
    assert "**Author:** Jane Doe" in md_text
    assert "Table of Contents" in md_text
    assert "Chapter 1: First Light" in md_text
    assert "Sunlight broke through the heavy clouds." in md_text
    assert "Chapter 2: Shadows Fall" in md_text
    assert "Copyright (c) 2026 Jane Doe" in md_text
