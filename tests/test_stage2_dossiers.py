import os
import pytest
from manuscriptfinesse.agents.base_agent import BaseAgent
from manuscriptfinesse.providers.base import MockProvider
from manuscriptfinesse.core.dossier_manager import DossierManager
from manuscriptfinesse.agents.dossier_builder import CharacterWorldBuilderAgent


def test_dossier_manager_dir_creation(tmp_path):
    """Verify DossierManager creates character, location, and faction directories."""
    d_mgr = DossierManager(base_dir=str(tmp_path))
    assert os.path.isdir(d_mgr.char_dir)
    assert os.path.isdir(d_mgr.loc_dir)
    assert os.path.isdir(d_mgr.fac_dir)


def test_dossier_manager_save_and_read_character(tmp_path):
    """Verify DossierManager saves and reads character dossiers in Markdown."""
    d_mgr = DossierManager(base_dir=str(tmp_path))
    filepath = d_mgr.save_character_dossier(
        name="Lyra Vane",
        role="Protagonist",
        voice="Sharp, precise, speaks in short sentences",
        backstory="Former archivist turned mercenary after the Great Sacking.",
        personality="Cautious, observant, deeply loyal to few.",
        appearance="Tall, lean build, silver hair tied in a braid, scar over left brow.",
        motivations="Find the Lost Codex to clear her family name.",
        secrets=["Possesses forbidden glyph magic", "Sworn enemy of the High Council"],
        special_attributes=["Master Decipherer", "Acoustic Resonance Perception"]
    )
    assert os.path.exists(filepath)
    assert filepath.endswith("lyra_vane.md")

    content = d_mgr.read_character_dossier("Lyra Vane")
    assert "Lyra Vane" in content
    assert "Protagonist" in content
    assert "Sharp, precise" in content
    assert "Lost Codex" in content
    assert "forbidden glyph magic" in content
    assert "Master Decipherer" in content

    # Test list
    chars = d_mgr.list_character_dossiers()
    assert "lyra_vane.md" in chars or "Lyra Vane" in chars or "lyra_vane" in chars


def test_dossier_manager_save_and_read_location(tmp_path):
    """Verify DossierManager saves and reads detailed sensory location dossiers in Markdown."""
    d_mgr = DossierManager(base_dir=str(tmp_path))
    filepath = d_mgr.save_location_dossier(
        name="The Frost Fortress",
        region="Northern Wastes",
        setting_type="Subterranean",
        overview="A cavernous stronghold carved into ancient glacial ice.",
        temperature="Freezing / Sub-zero",
        moisture="Damp frost condensation",
        weather_lighting="Torchlight reflecting off blue ice pillars",
        smells=["Ozone", "Burning pine pitch", "Old leather"],
        sounds=["Howling arctic wind outside", "Dripping water", "Echoing whispers"],
        visuals_and_textures=["Slick frost floor", "Rough-hewn granite altars"],
        points_of_interest=["The Great Hearth", "The Vault of Mirrors"]
    )
    assert os.path.exists(filepath)
    assert filepath.endswith("the_frost_fortress.md")

    content = d_mgr.read_location_dossier("The Frost Fortress")
    assert "The Frost Fortress" in content
    assert "Northern Wastes" in content
    assert "Subterranean" in content
    assert "Freezing" in content
    assert "Burning pine pitch" in content
    assert "Howling arctic wind outside" in content
    assert "Vault of Mirrors" in content

    # Test list
    locs = d_mgr.list_location_dossiers()
    assert len(locs) == 1


def test_dossier_manager_save_and_read_faction(tmp_path):
    """Verify DossierManager saves and reads faction dossiers in Markdown."""
    d_mgr = DossierManager(base_dir=str(tmp_path))
    filepath = d_mgr.save_faction_dossier(
        name="The Silver Syndicate",
        motto="Knowledge is Currency",
        ideology="Monopolize ancient tech and knowledge to maintain political power.",
        overview="A secret guild of scholars, merchants, and shadow operatives.",
        members=["Lord Vaelen", "Kaelen Voss"],
        resources=["Archives of Oakhaven", "Fleet of Stealth Skiffs"]
    )
    assert os.path.exists(filepath)
    assert filepath.endswith("the_silver_syndicate.md")

    content = d_mgr.read_faction_dossier("The Silver Syndicate")
    assert "The Silver Syndicate" in content
    assert "Knowledge is Currency" in content
    assert "Lord Vaelen" in content

    facs = d_mgr.list_faction_dossiers()
    assert len(facs) == 1


def test_character_world_builder_agent_is_subclass():
    """Verify CharacterWorldBuilderAgent inherits from BaseAgent."""
    provider = MockProvider()
    agent = CharacterWorldBuilderAgent(provider=provider)
    assert isinstance(agent, BaseAgent)


def test_character_world_builder_agent_run_raw_input():
    """Verify CharacterWorldBuilderAgent run method processes raw brief input."""
    provider = MockProvider()
    agent = CharacterWorldBuilderAgent(provider=provider)
    brief = "# Project Brief\n## Premise\nHigh fantasy realm in sky islands."
    output = agent.run(brief)
    assert isinstance(output, str)
    assert len(output) > 0


def test_character_world_builder_agent_generate_character():
    """Verify agent generates character dossier prompt via LLM provider."""
    mock_response = (
        "# Character Dossier: Kaelen Voss\n\n"
        "**Role:** Protagonist\n"
        "**Voice:** Quiet and stoic\n"
        "**Backstory:** Raised in the lower mines.\n"
        "**Personality:** Pragmatic, loyal.\n"
        "**Appearance:** Tanned skin, dark hair, blue eyes.\n"
        "**Motivations:** Protect his village.\n"
        "**Secrets:** Possesses ancient mark.\n"
        "**Special Attributes:** Flame weaving."
    )
    provider = MockProvider(default_response=mock_response)
    agent = CharacterWorldBuilderAgent(provider=provider)
    result = agent.generate_character_dossier(
        brief_content="Project Brief info...",
        character_name="Kaelen Voss",
        role="Protagonist"
    )
    assert "Kaelen Voss" in result
    assert "Flame weaving" in result


def test_character_world_builder_agent_generate_location():
    """Verify agent generates sensory location dossier prompt via LLM provider."""
    mock_response = (
        "# Location Dossier: Sunken Citadel\n\n"
        "**Region:** Black Sea\n"
        "**Setting Type:** Subterranean\n\n"
        "## Scene & Setting Overview\nAncient underwater ruins.\n\n"
        "## Environmental & Micro-Climate Profile\n"
        "- **Temperature & Climate:** Frigid\n"
        "- **Moisture & Humidity:** Submerged\n"
        "- **Weather & Illumination:** Bioluminescent algae\n\n"
        "## Immersive 5-Sense Sensory Profile\n"
        "### Olfactory (What am I smelling?)\n- Brine\n- Salt\n\n"
        "### Auditory (What am I hearing?)\n- Water pressure hums\n\n"
        "### Visuals & Textures underfoot\n- Barnacle-encrusted stone\n\n"
        "## Key Points of Interest\n- The Sunken Throne"
    )
    provider = MockProvider(default_response=mock_response)
    agent = CharacterWorldBuilderAgent(provider=provider)
    result = agent.generate_location_dossier(
        brief_content="Project Brief info...",
        location_name="Sunken Citadel",
        setting_type="Subterranean"
    )
    assert "Sunken Citadel" in result
    assert "Subterranean" in result
    assert "Olfactory" in result
    assert "Auditory" in result


def test_character_world_builder_agent_build_and_save_dossiers(tmp_path):
    """Verify end-to-end building and saving dossiers via DossierManager."""
    d_mgr = DossierManager(base_dir=str(tmp_path))
    provider = MockProvider()
    agent = CharacterWorldBuilderAgent(provider=provider)

    brief_file = tmp_path / "project_brief.md"
    brief_file.write_text("# Project Brief\nPremise: Cyberpunk story.", encoding="utf-8")

    char_file = agent.build_and_save_character(
        dossier_manager=d_mgr,
        brief_input=str(brief_file),
        name="Rin Nova",
        role="Protagonist"
    )
    assert os.path.exists(char_file)

    loc_file = agent.build_and_save_location(
        dossier_manager=d_mgr,
        brief_input=str(brief_file),
        name="Sector 7 Slums",
        setting_type="Outdoors"
    )
    assert os.path.exists(loc_file)
