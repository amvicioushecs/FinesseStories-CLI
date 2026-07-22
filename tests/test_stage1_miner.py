import os
import pytest
from manuscriptfinesse.providers.base import MockProvider
from manuscriptfinesse.agents.base_agent import BaseAgent, load_input
from manuscriptfinesse.agents.miner import KnowledgeMinerAgent


def test_base_agent_cannot_be_instantiated_directly():
    """Verify that BaseAgent is an abstract class and cannot be instantiated without subclassing."""
    provider = MockProvider()
    with pytest.raises(TypeError):
        BaseAgent(provider=provider)


def test_load_input_helper_raw_text():
    """Verify load_input helper returns raw text if input is not an existing file."""
    raw_text = "This is raw story premise text, not a file path."
    assert load_input(raw_text) == raw_text


def test_load_input_helper_multiline_raw_text():
    """Verify load_input helper handles multi-line raw text on Windows without OSError."""
    multiline_text = "Line 1: High fantasy realm\nLine 2: Dragon riders\nLine 3: Ancient glyphs"
    assert load_input(multiline_text) == multiline_text


def test_load_input_helper_file_path(tmp_path):
    """Verify load_input helper reads file contents when passed an existing file path."""
    input_file = tmp_path / "notes.txt"
    content = "Cyberpunk detective hunting AI rogues in Neo-Tokyo."
    input_file.write_text(content, encoding="utf-8")

    result = load_input(str(input_file))
    assert result == content


def test_knowledge_miner_agent_run_with_raw_text():
    """Verify KnowledgeMinerAgent runs with raw text input using MockProvider."""
    provider = MockProvider()
    agent = KnowledgeMinerAgent(provider=provider)

    raw_input = "A space captain searches for a lost homeworld amidst alien empires."
    result = agent.run(raw_input)

    assert isinstance(result, str)
    assert len(result) > 0
    assert "[MOCK GENERATION" in result


def test_knowledge_miner_agent_run_with_file_path(tmp_path):
    """Verify KnowledgeMinerAgent reads file input when given a file path."""
    input_file = tmp_path / "premise.txt"
    file_content = "Fantasy realm where magic is powered by musical harmonies."
    input_file.write_text(file_content, encoding="utf-8")

    provider = MockProvider()
    agent = KnowledgeMinerAgent(provider=provider)

    result = agent.run(str(input_file))
    assert isinstance(result, str)
    assert "[MOCK GENERATION" in result


def test_knowledge_miner_agent_structured_brief():
    """Verify KnowledgeMinerAgent generates structured project brief content with expected sections."""
    mock_brief = (
        "# Project Brief: Harmony of Spheres\n\n"
        "## Premise\n"
        "A rogue bard uses forbidden chords to awaken sleeping titans.\n\n"
        "## Themes & Tropes\n"
        "- Music as magic\n- Power corrupts\n\n"
        "## Target Tone\n"
        "Lyrical, tense, atmospheric.\n\n"
        "## Primary Entities\n"
        "- Lyra (Protagonist)\n- The Soundless Guild\n\n"
        "## Non-Negotiables\n"
        "- Magic requires physical acoustic resonance.\n"
    )

    provider = MockProvider(default_response=mock_brief)
    agent = KnowledgeMinerAgent(provider=provider)

    result = agent.run("Rogue bard awakens titans with music.")

    assert "## Premise" in result
    assert "## Themes & Tropes" in result
    assert "## Target Tone" in result
    assert "## Primary Entities" in result
    assert "## Non-Negotiables" in result
