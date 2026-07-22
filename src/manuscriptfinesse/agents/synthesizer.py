import json
import os
import re
from typing import List, Dict, Any, Optional
from manuscriptfinesse.agents.base_agent import BaseAgent, load_input
from manuscriptfinesse.core.dossier_manager import DossierManager, slugify
from manuscriptfinesse.core.models import (
    StoryBibleSchema,
    CharacterDossier,
    LocationDossier,
    FactionDossier,
)
from manuscriptfinesse.providers.base import BaseLLMProvider

DEFAULT_SYNTHESIZER_SYSTEM_PROMPT = (
    "You are the Stage 3 Story Bible Synthesizer (BibleSynthesizerAgent) for ManuscriptFinesse. "
    "Your objective is to parse project briefs, character dossiers, sensory location dossiers, "
    "and faction dossiers, and synthesize a single, unified, machine-readable StoryBibleSchema "
    "JSON object with schema version '3.0'.\n\n"
    "Output MUST be valid JSON adhering strictly to the StoryBibleSchema structure."
)


def _extract_section(content: str, header: str) -> str:
    """Extracts text section under a markdown ## header."""
    pattern = rf"##\s+{re.escape(header)}[^\n]*\n(.*?)(?=\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _extract_list_items(content: str, header: str) -> List[str]:
    """Extracts bullet point list items under a markdown ## or ### header."""
    pattern = rf"###?\s+{re.escape(header)}[^\n]*\n(.*?)(?=\n###?|\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    block = match.group(1)
    items = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            item = line[2:].strip()
            if item and item.lower() not in ("none specified.", "none specified"):
                items.append(item)
    return items


def _extract_field(content: str, field_name: str) -> str:
    """Extracts key-value pair from markdown like **Key:** Value."""
    pattern = rf"\*\*{re.escape(field_name)}:\*\*\s*(.*)"
    match = re.search(pattern, content, re.IGNORECASE)
    if match:
        val = match.group(1).strip()
        return val
    return ""


def _parse_character_markdown(content: str, filename: str) -> CharacterDossier:
    """Parses character markdown dossier file into a CharacterDossier model."""
    name_match = re.search(r"# Character Dossier:\s*(.+)", content, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).strip()
    else:
        clean_name = filename[:-3] if filename.endswith(".md") else filename
        name = clean_name.replace("_", " ").title()

    char_id = slugify(name)
    role = _extract_field(content, "Role") or "Supporting"
    voice = _extract_field(content, "Voice & Speech Rules")
    appearance = _extract_section(content, "Physical Appearance")
    personality = _extract_section(content, "Personality & Speech")
    backstory = _extract_section(content, "Backstory & Origins")
    motivations = _extract_section(content, "Motivations & Internal Flaws")
    secrets = _extract_list_items(content, "Secrets")
    special_attributes = _extract_list_items(content, "Special Attributes & Unique Abilities")

    return CharacterDossier(
        id=char_id,
        name=name,
        role=role,
        voice_and_speech=voice,
        backstory=backstory,
        personality=personality,
        physical_appearance=appearance,
        motivations=motivations,
        secrets=secrets,
        special_attributes=special_attributes,
    )


def _parse_location_markdown(content: str, filename: str) -> LocationDossier:
    """Parses location markdown dossier file into a LocationDossier model."""
    name_match = re.search(r"# Location Dossier:\s*(.+)", content, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).strip()
    else:
        clean_name = filename[:-3] if filename.endswith(".md") else filename
        name = clean_name.replace("_", " ").title()

    loc_id = slugify(name)
    region = _extract_field(content, "Region")
    setting_raw = _extract_field(content, "Setting Type")
    setting_type = setting_raw.split("(")[0].strip() if setting_raw else "Outdoors"

    overview = _extract_section(content, "Scene & Setting Overview")

    temp_match = re.search(r"-\s*\*\*Temperature & Climate:\*\*\s*(.*)", content, re.IGNORECASE)
    temperature = temp_match.group(1).strip() if temp_match else "Temperate"

    moist_match = re.search(r"-\s*\*\*Moisture & Humidity:\*\*\s*(.*)", content, re.IGNORECASE)
    moisture = moist_match.group(1).strip() if moist_match else "Dry"

    weather_match = re.search(r"-\s*\*\*Weather & Illumination:\*\*\s*(.*)", content, re.IGNORECASE)
    weather_lighting = weather_match.group(1).strip() if weather_match else "Clear/Sunny"

    smells = _extract_list_items(content, "Olfactory")
    sounds = _extract_list_items(content, "Auditory")
    visuals = _extract_list_items(content, "Visuals & Textures underfoot")
    factions_present = _extract_list_items(content, "Factions Present")
    points_of_interest = _extract_list_items(content, "Key Points of Interest")

    return LocationDossier(
        id=loc_id,
        name=name,
        region=region,
        setting_type=setting_type,
        overview=overview,
        temperature=temperature,
        moisture=moisture,
        weather_lighting=weather_lighting,
        smells=smells,
        sounds=sounds,
        visuals_and_textures=visuals,
        factions_present=factions_present,
        points_of_interest=points_of_interest,
    )


def _parse_faction_markdown(content: str, filename: str) -> FactionDossier:
    """Parses faction markdown dossier file into a FactionDossier model."""
    name_match = re.search(r"# Faction Dossier:\s*(.+)", content, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).strip()
    else:
        clean_name = filename[:-3] if filename.endswith(".md") else filename
        name = clean_name.replace("_", " ").title()

    fac_id = slugify(name)
    motto = _extract_field(content, "Motto")
    ideology = _extract_field(content, "Ideology")

    return FactionDossier(
        id=fac_id,
        name=name,
        motto=motto,
        ideology=ideology,
    )


class BibleSynthesizerAgent(BaseAgent):
    """Stage 3 Story Bible Synthesizer Agent responsible for compiling dossiers into bible.json v3.0."""

    def __init__(self, provider: BaseLLMProvider, system_prompt: Optional[str] = None):
        super().__init__(
            provider=provider,
            system_prompt=system_prompt or DEFAULT_SYNTHESIZER_SYSTEM_PROMPT
        )

    def run(self, raw_input: str) -> str:
        """Executes synthesis using raw_input as base_dir or raw prompt and returns bible JSON string."""
        base_dir = raw_input if os.path.isdir(raw_input) else "."
        bible = self.synthesize(base_dir=base_dir)
        return bible.model_dump_json(indent=2)

    def synthesize(self, base_dir: str = ".") -> StoryBibleSchema:
        """Parses project brief & dossiers in base_dir, synthesizes StoryBibleSchema (v3.0), and writes bible.json."""
        d_mgr = DossierManager(base_dir=base_dir)

        # 1. Read Project Brief if it exists
        brief_path = os.path.join(base_dir, "project_brief.md")
        brief_content = ""
        project_title = "Untitled Project"
        canon_rules: List[str] = []

        if os.path.exists(brief_path):
            with open(brief_path, "r", encoding="utf-8") as f:
                brief_content = f.read()
            title_match = re.search(r"#\s*(?:Project Brief:\s*)?(.+)", brief_content, re.IGNORECASE)
            if title_match:
                project_title = title_match.group(1).strip()
            canon_rules = _extract_list_items(brief_content, "Non-Negotiables") or _extract_list_items(brief_content, "Canon Rules")

        # 2. Read character, location, faction dossier markdown files
        char_dossiers: List[CharacterDossier] = []
        for char_file in d_mgr.list_character_dossiers():
            content = d_mgr.read_character_dossier(char_file)
            char_dossiers.append(_parse_character_markdown(content, char_file))

        loc_dossiers: List[LocationDossier] = []
        for loc_file in d_mgr.list_location_dossiers():
            content = d_mgr.read_location_dossier(loc_file)
            loc_dossiers.append(_parse_location_markdown(content, loc_file))

        fac_dossiers: List[FactionDossier] = []
        for fac_file in d_mgr.list_faction_dossiers():
            content = d_mgr.read_faction_dossier(fac_file)
            fac_dossiers.append(_parse_faction_markdown(content, fac_file))

        # 3. Prompt LLM provider to synthesize/verify
        user_prompt = (
            f"=== PROJECT BRIEF ===\n{brief_content}\n\n"
            f"=== CHARACTERS ({len(char_dossiers)}) ===\n" + "\n---\n".join([c.model_dump_json() for c in char_dossiers]) + "\n\n"
            f"=== LOCATIONS ({len(loc_dossiers)}) ===\n" + "\n---\n".join([l.model_dump_json() for l in loc_dossiers]) + "\n\n"
            f"=== FACTIONS ({len(fac_dossiers)}) ===\n" + "\n---\n".join([f.model_dump_json() for f in fac_dossiers]) + "\n\n"
            "Synthesize all project information into a complete StoryBibleSchema v3.0 JSON object."
        )

        llm_response = self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        bible: Optional[StoryBibleSchema] = None

        # 4. Attempt to parse JSON response from LLM if provided
        cleaned = llm_response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            parsed_data = json.loads(cleaned)
            if isinstance(parsed_data, dict):
                parsed_data["story_bible_version"] = "3.0"
                bible = StoryBibleSchema.model_validate(parsed_data)
        except Exception:
            bible = None

        # 5. Fallback if LLM output was not structured JSON
        if bible is None:
            bible = StoryBibleSchema(
                story_bible_version="3.0",
                project_title=project_title,
                canon_rules=canon_rules,
                world={"summary": "Synthesized world setting from dossiers and brief."},
                characters=char_dossiers,
                locations=loc_dossiers,
                factions=fac_dossiers,
                chronology_and_canon_ledger=[]
            )

        # 6. Save bible.json to disk
        bible_path = os.path.join(base_dir, "bible.json")
        with open(bible_path, "w", encoding="utf-8") as f:
            f.write(bible.model_dump_json(indent=2))

        return bible
