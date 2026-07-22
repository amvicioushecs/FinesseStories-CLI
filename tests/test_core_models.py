import os
import pytest
from manuscriptfinesse.core.models import (
    ProjectMetadata,
    StoryBibleSchema,
    ChapterBeat,
    LocationDossier,
    CharacterDossier,
    FactionDossier,
)
from manuscriptfinesse.core.config import ProjectConfig
from manuscriptfinesse.core.project import ProjectManager

def test_project_metadata_defaults():
    meta = ProjectMetadata(title="Test Book")
    assert meta.title == "Test Book"
    assert meta.target_word_count == 80000
    assert meta.current_chapter == 1
    assert "miner" in meta.role_providers

def test_story_bible_schema_v3():
    bible = StoryBibleSchema(project_title="Test Book")
    assert bible.story_bible_version == "3.0"
    assert isinstance(bible.canon_rules, list)
    assert isinstance(bible.characters, list)
    assert isinstance(bible.locations, list)

def test_location_dossier_sensory_details():
    loc = LocationDossier(
        id="loc_01",
        name="Sunken Citadel",
        setting_type="Underground",
        temperature="Freezing",
        moisture="Damp",
        weather_lighting="Bioluminescent moss",
        smells=["Damp ozone", "Ancient decay"],
        sounds=["Echoing water drops", "Distant howling wind"]
    )
    assert loc.setting_type == "Underground"
    assert "Damp ozone" in loc.smells
    assert "Echoing water drops" in loc.sounds

def test_character_and_faction_dossiers():
    char = CharacterDossier(id="char_01", name="Lyra Vane", role="Protagonist", secrets=["Shadow magic user"])
    assert char.name == "Lyra Vane"
    assert char.role == "Protagonist"
    assert "Shadow magic user" in char.secrets

    faction = FactionDossier(id="fac_01", name="Shadow Assembly", motto="In Darkness We Trust")
    assert faction.name == "Shadow Assembly"
    assert faction.motto == "In Darkness We Trust"

def test_chapter_beat():
    beat = ChapterBeat(chapter_id="ch_01", title="Beginning", pov="Lyra", beats=["Beat 1", "Beat 2"])
    assert beat.chapter_id == "ch_01"
    assert beat.target_word_count == 3500
    assert len(beat.beats) == 2

def test_project_config(tmp_path):
    config = ProjectConfig()
    assert "gemini" in config.providers
    assert config.role_routing["miner"] == "gemini/gemini-2.5-flash"
    
    cfg_file = str(tmp_path / "config.yaml")
    config.save(cfg_file)
    assert os.path.exists(cfg_file)
    
    loaded = ProjectConfig.load(cfg_file)
    assert loaded.role_routing["miner"] == "gemini/gemini-2.5-flash"

def test_project_manager(tmp_path):
    pm = ProjectManager(root_dir=str(tmp_path))
    meta = pm.init_project(title="Eldoria Chronicles", genre="Fantasy", target_word_count=100000)
    
    assert meta.title == "Eldoria Chronicles"
    assert os.path.exists(tmp_path / ".manuscriptfinesse" / "project.json")
    assert os.path.exists(tmp_path / ".manuscriptfinesse" / "config.yaml")
    assert os.path.exists(tmp_path / "bible" / "characters")
    assert os.path.exists(tmp_path / "bible" / "locations")
    assert os.path.exists(tmp_path / "bible" / "factions")
    assert os.path.exists(tmp_path / "chapters")

    loaded_meta = pm.load_metadata()
    assert loaded_meta.title == "Eldoria Chronicles"
    assert loaded_meta.target_word_count == 100000
