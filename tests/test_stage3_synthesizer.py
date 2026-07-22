import json
import os
import pytest
from manuscriptfinesse.agents.base_agent import BaseAgent
from manuscriptfinesse.agents.synthesizer import BibleSynthesizerAgent
from manuscriptfinesse.core.dossier_manager import DossierManager
from manuscriptfinesse.core.models import StoryBibleSchema
from manuscriptfinesse.providers.base import MockProvider


def test_bible_synthesizer_is_subclass():
    """Verify BibleSynthesizerAgent inherits from BaseAgent."""
    provider = MockProvider()
    agent = BibleSynthesizerAgent(provider=provider)
    assert isinstance(agent, BaseAgent)


def test_bible_synthesizer_synthesis_empty_dir(tmp_path):
    """Verify synthesizer creates a default StoryBibleSchema (v3.0) and bible.json in an empty directory."""
    provider = MockProvider()
    agent = BibleSynthesizerAgent(provider=provider)

    bible = agent.synthesize(base_dir=str(tmp_path))

    assert isinstance(bible, StoryBibleSchema)
    assert bible.story_bible_version == "3.0"

    bible_path = tmp_path / "bible.json"
    assert os.path.exists(bible_path)

    with open(bible_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["story_bible_version"] == "3.0"


def test_bible_synthesizer_synthesis_with_saved_dossiers(tmp_path):
    """Verify synthesizer reads saved Markdown dossiers and compiles them into bible.json v3.0."""
    d_mgr = DossierManager(base_dir=str(tmp_path))

    # Write project brief
    brief_file = tmp_path / "project_brief.md"
    brief_file.write_text(
        "# Project Brief: Chronicles of Caelum\n\n"
        "## Premise\nHigh fantasy realm in floating sky islands.\n\n"
        "## Non-Negotiables\n- Sky ships require Aether crystals.\n",
        encoding="utf-8"
    )

    # Save character dossier
    d_mgr.save_character_dossier(
        name="Aria Vance",
        role="Protagonist",
        voice="Melodic and resolute",
        backstory="Sky-sailor from the Lower Cloud Belt.",
        personality="Brave, adventurous",
        appearance="Windblown blonde hair, leather flight suit",
        motivations="Find the Lost Citadel of Aether",
        secrets=["Carries forbidden map"],
        special_attributes=["Aether Navigation"]
    )

    # Save location dossier
    d_mgr.save_location_dossier(
        name="Aether Peak",
        region="Upper Atmosphere",
        setting_type="Outdoors",
        overview="Floating mountain spire shrouded in blue mist.",
        temperature="Freezing",
        moisture="Humid mist",
        weather_lighting="Constant auroral light",
        smells=["Ozone", "Fresh rain"],
        sounds=["Wind hums", "Crystal chime resonance"],
        visuals_and_textures=["Crystalline rock", "Slick ice shelves"],
        points_of_interest=["The Observatory", "Crystal Vault"]
    )

    # Save faction dossier
    d_mgr.save_faction_dossier(
        name="The Sky Guild",
        motto="Above the Storm",
        ideology="Protect the skyways and control crystal trade.",
        overview="Trade alliance of sky-captains.",
        members=["Captain Vane", "Aria Vance"],
        resources=["Fleet of 50 Sky-clippers"]
    )

    provider = MockProvider()
    agent = BibleSynthesizerAgent(provider=provider)

    bible = agent.synthesize(base_dir=str(tmp_path))

    assert bible.story_bible_version == "3.0"
    assert len(bible.characters) == 1
    assert bible.characters[0].name == "Aria Vance"
    assert bible.characters[0].role == "Protagonist"

    assert len(bible.locations) == 1
    assert bible.locations[0].name == "Aether Peak"
    assert "Ozone" in bible.locations[0].smells

    assert len(bible.factions) == 1
    assert bible.factions[0].name == "The Sky Guild"

    # Check generated bible.json file
    bible_path = tmp_path / "bible.json"
    assert os.path.exists(bible_path)

    with open(bible_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    assert json_data["story_bible_version"] == "3.0"
    assert json_data["project_title"] == "Chronicles of Caelum"
    assert len(json_data["characters"]) == 1
    assert json_data["characters"][0]["name"] == "Aria Vance"


def test_bible_synthesizer_custom_llm_json_response(tmp_path):
    """Verify synthesizer parses structured JSON from LLM response if valid."""
    custom_json = json.dumps({
        "story_bible_version": "3.0",
        "project_title": "Custom LLM Book",
        "canon_rules": ["No time travel"],
        "world": {"setting": "Sci-Fi"},
        "characters": [{
            "id": "char_01",
            "name": "Kaelen",
            "role": "Hero",
            "voice_and_speech": "Deep voice",
            "backstory": "Origin unknown",
            "personality": "Stoic",
            "physical_appearance": "Tall",
            "motivations": "Justice",
            "secrets": ["Is a cyborg"],
            "special_attributes": ["Cybernetics"]
        }],
        "locations": [],
        "factions": [],
        "chronology_and_canon_ledger": []
    })

    provider = MockProvider(default_response=custom_json)
    agent = BibleSynthesizerAgent(provider=provider)

    bible = agent.synthesize(base_dir=str(tmp_path))

    assert bible.story_bible_version == "3.0"
    assert bible.project_title == "Custom LLM Book"
    assert len(bible.characters) == 1
    assert bible.characters[0].name == "Kaelen"

    bible_path = tmp_path / "bible.json"
    assert os.path.exists(bible_path)


def test_bible_synthesizer_run_method(tmp_path):
    """Verify agent run() method calls synthesize and returns JSON string."""
    provider = MockProvider()
    agent = BibleSynthesizerAgent(provider=provider)

    result = agent.run(str(tmp_path))

    assert isinstance(result, str)
    assert '"story_bible_version": "3.0"' in result
