import json
import os
import pytest
from manuscriptfinesse.agents.base_agent import BaseAgent
from manuscriptfinesse.agents.outliner import OutlinerAgent
from manuscriptfinesse.core.models import StoryBibleSchema, ChapterBeat, CharacterDossier
from manuscriptfinesse.providers.base import MockProvider


def test_outliner_agent_is_subclass():
    """Verify OutlinerAgent inherits from BaseAgent."""
    provider = MockProvider()
    agent = OutlinerAgent(provider=provider)
    assert isinstance(agent, BaseAgent)


def test_outliner_matrix_generation_default_args():
    """Verify generate_outline creates 20 chapters totaling 80,000 words by default."""
    provider = MockProvider()
    agent = OutlinerAgent(provider=provider)
    bible = StoryBibleSchema(
        project_title="The Eldoria Code",
        characters=[CharacterDossier(id="char_1", name="Lyra Vane", role="Protagonist")]
    )

    chapters = agent.generate_outline(bible)

    assert len(chapters) == 20
    assert isinstance(chapters[0], ChapterBeat)
    
    # Target word count per chapter should sum up to total_word_count (80,000)
    total_allocated = sum(c.target_word_count for c in chapters)
    assert total_allocated == 80000
    assert chapters[0].target_word_count == 4000
    assert chapters[0].chapter_id == "ch_01"
    assert chapters[0].pov == "Lyra Vane"
    assert len(chapters[0].beats) > 0


def test_outliner_word_count_allocation_custom():
    """Verify word count allocation for custom total word count and num chapters."""
    provider = MockProvider()
    agent = OutlinerAgent(provider=provider)
    bible = StoryBibleSchema(project_title="Short Novel")

    chapters = agent.generate_outline(bible, total_word_count=50000, num_chapters=10)

    assert len(chapters) == 10
    total_allocated = sum(c.target_word_count for c in chapters)
    assert total_allocated == 50000
    assert chapters[0].target_word_count == 5000


def test_outliner_llm_json_output_parsing():
    """Verify OutlinerAgent correctly parses custom JSON array returned by LLM provider."""
    custom_outline_json = json.dumps([
        {
            "chapter_id": "ch_01",
            "title": "Chapter 1: The Arrival",
            "pov": "Kaelen",
            "target_word_count": 4000,
            "beats": ["Beat 1.1: Ship lands", "Beat 1.2: First contact"],
            "summary": "Kaelen arrives on the planet."
        },
        {
            "chapter_id": "ch_02",
            "title": "Chapter 2: The Discovery",
            "pov": "Lyra",
            "target_word_count": 4000,
            "beats": ["Beat 2.1: Ancient ruins found", "Beat 2.2: Trap triggered"],
            "summary": "Lyra discovers ancient technology."
        }
    ])

    provider = MockProvider(default_response=custom_outline_json)
    agent = OutlinerAgent(provider=provider)
    bible = StoryBibleSchema(project_title="Sci-Fi Epic")

    chapters = agent.generate_outline(bible, total_word_count=8000, num_chapters=2)

    assert len(chapters) == 2
    assert chapters[0].chapter_id == "ch_01"
    assert chapters[0].title == "Chapter 1: The Arrival"
    assert chapters[0].pov == "Kaelen"
    assert len(chapters[0].beats) == 2
    assert chapters[1].title == "Chapter 2: The Discovery"


def test_outliner_run_method(tmp_path):
    """Verify run() method accepts bible.json path or raw json string and returns JSON output."""
    provider = MockProvider()
    agent = OutlinerAgent(provider=provider)

    bible = StoryBibleSchema(project_title="Run Test Story")
    bible_file = tmp_path / "bible.json"
    bible_file.write_text(bible.model_dump_json(indent=2), encoding="utf-8")

    result = agent.run(str(bible_file))

    assert isinstance(result, str)
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == 20
    assert parsed[0]["chapter_id"] == "ch_01"
