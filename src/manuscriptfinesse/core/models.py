from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ProjectMetadata(BaseModel):
    title: str = "Untitled Masterpiece"
    genre: str = "Unspecified"
    target_word_count: int = 80000
    current_word_count: int = 0
    current_chapter: int = 1
    role_providers: Dict[str, str] = Field(default_factory=lambda: {
        "miner": "gemini/gemini-2.5-flash",
        "dossier_builder": "gemini/gemini-2.5-pro",
        "synthesizer": "gemini/gemini-2.5-flash",
        "outliner": "gemini/gemini-2.5-flash",
        "drafter": "anthropic/claude-3-5-sonnet",
        "auditor": "gemini/gemini-2.5-pro",
        "polisher": "openai/gpt-4o"
    })

class CharacterDossier(BaseModel):
    id: str
    name: str
    role: str = "Supporting"
    voice_and_speech: str = ""
    backstory: str = ""
    personality: str = ""
    physical_appearance: str = ""
    motivations: str = ""
    secrets: List[str] = Field(default_factory=list)
    special_attributes: List[str] = Field(default_factory=list)

class LocationDossier(BaseModel):
    id: str
    name: str
    region: str = ""
    setting_type: str = "Outdoors"  # Indoors / Outdoors / Underground / Celestial
    overview: str = ""
    temperature: str = "Temperate"
    moisture: str = "Dry"
    weather_lighting: str = "Clear/Sunny"
    smells: List[str] = Field(default_factory=list)
    sounds: List[str] = Field(default_factory=list)
    visuals_and_textures: List[str] = Field(default_factory=list)
    factions_present: List[str] = Field(default_factory=list)
    points_of_interest: List[str] = Field(default_factory=list)

class FactionDossier(BaseModel):
    id: str
    name: str
    motto: str = ""
    ideology: str = ""

class StoryBibleSchema(BaseModel):
    story_bible_version: str = "3.0"
    project_title: str = "Untitled Project"
    canon_rules: List[str] = Field(default_factory=list)
    world: Dict[str, Any] = Field(default_factory=dict)
    characters: List[CharacterDossier] = Field(default_factory=list)
    locations: List[LocationDossier] = Field(default_factory=list)
    factions: List[FactionDossier] = Field(default_factory=list)
    chronology_and_canon_ledger: List[Dict[str, Any]] = Field(default_factory=list)

class ChapterBeat(BaseModel):
    chapter_id: str
    title: str
    pov: str
    target_word_count: int = 3500
    actual_word_count: int = 0
    status: str = "outlined"
    beats: List[str] = Field(default_factory=list)
    summary: str = ""
