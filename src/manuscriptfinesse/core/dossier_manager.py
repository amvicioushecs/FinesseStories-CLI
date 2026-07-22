import os
import re
from typing import List, Optional


def slugify(name: str) -> str:
    """Converts a name string into a sanitized lowercase filename slug."""
    clean = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "_", clean)


class DossierManager:
    """Handles reading, creating, listing, and persisting Markdown dossiers for Stage 2."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.char_dir = os.path.join(base_dir, "bible", "characters")
        self.loc_dir = os.path.join(base_dir, "bible", "locations")
        self.fac_dir = os.path.join(base_dir, "bible", "factions")

        for d in [self.char_dir, self.loc_dir, self.fac_dir]:
            os.makedirs(d, exist_ok=True)

    def _resolve_filepath(self, target_dir: str, name_or_slug: str) -> str:
        """Resolves target directory and name/slug to absolute file path."""
        if name_or_slug.endswith(".md"):
            filename = name_or_slug
        else:
            filename = f"{slugify(name_or_slug)}.md"
        return os.path.join(target_dir, filename)

    # --- Character Dossiers ---

    def save_character_dossier(
        self,
        name: str,
        role: str = "Supporting",
        voice: str = "",
        backstory: str = "",
        personality: str = "",
        appearance: str = "",
        motivations: str = "",
        secrets: Optional[List[str]] = None,
        special_attributes: Optional[List[str]] = None,
        raw_content: Optional[str] = None
    ) -> str:
        """Saves character dossier Markdown file. Returns the created file path."""
        filepath = self._resolve_filepath(self.char_dir, name)

        if raw_content:
            content = raw_content
        else:
            secrets_list = secrets or []
            attributes_list = special_attributes or []

            secrets_fmt = "\n".join([f"- {s}" for s in secrets_list]) if secrets_list else "None specified."
            attributes_fmt = "\n".join([f"- {a}" for a in attributes_list]) if attributes_list else "None specified."

            content = (
                f"# Character Dossier: {name}\n\n"
                f"**Role:** {role}  \n"
                f"**Voice & Speech Rules:** {voice}\n\n"
                f"## Physical Appearance\n{appearance}\n\n"
                f"## Personality & Speech\n{personality}\n\n"
                f"## Backstory & Origins\n{backstory}\n\n"
                f"## Motivations & Internal Flaws\n{motivations}\n\n"
                f"## Secrets\n{secrets_fmt}\n\n"
                f"## Special Attributes & Unique Abilities\n{attributes_fmt}\n"
            )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def read_character_dossier(self, name_or_slug: str) -> str:
        """Reads character dossier Markdown file."""
        filepath = self._resolve_filepath(self.char_dir, name_or_slug)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Character dossier not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def list_character_dossiers(self) -> List[str]:
        """Lists all character dossier filenames."""
        if not os.path.exists(self.char_dir):
            return []
        return [f for f in os.listdir(self.char_dir) if f.endswith(".md")]

    # --- Location Dossiers ---

    def save_location_dossier(
        self,
        name: str,
        region: str = "",
        setting_type: str = "Outdoors",
        overview: str = "",
        temperature: str = "Temperate",
        moisture: str = "Dry",
        weather_lighting: str = "Clear/Sunny",
        smells: Optional[List[str]] = None,
        sounds: Optional[List[str]] = None,
        visuals_and_textures: Optional[List[str]] = None,
        points_of_interest: Optional[List[str]] = None,
        raw_content: Optional[str] = None
    ) -> str:
        """Saves sensory location dossier Markdown file. Returns the created file path."""
        filepath = self._resolve_filepath(self.loc_dir, name)

        if raw_content:
            content = raw_content
        else:
            smells_list = smells or []
            sounds_list = sounds or []
            visuals_list = visuals_and_textures or []
            poi_list = points_of_interest or []

            smells_fmt = "\n".join([f"- {s}" for s in smells_list]) if smells_list else "None specified."
            sounds_fmt = "\n".join([f"- {s}" for s in sounds_list]) if sounds_list else "None specified."
            visuals_fmt = "\n".join([f"- {v}" for v in visuals_list]) if visuals_list else "None specified."
            poi_fmt = "\n".join([f"- {p}" for p in poi_list]) if poi_list else "None specified."

            content = (
                f"# Location Dossier: {name}\n\n"
                f"**Region:** {region}  \n"
                f"**Setting Type:** {setting_type} (Indoors / Outdoors / Subterranean)\n\n"
                f"## Scene & Setting Overview\n{overview}\n\n"
                f"## Environmental & Micro-Climate Profile\n"
                f"- **Temperature & Climate:** {temperature}\n"
                f"- **Moisture & Humidity:** {moisture}\n"
                f"- **Weather & Illumination:** {weather_lighting}\n\n"
                f"## Immersive 5-Sense Sensory Profile\n"
                f"### Olfactory (What am I smelling?)\n{smells_fmt}\n\n"
                f"### Auditory (What am I hearing?)\n{sounds_fmt}\n\n"
                f"### Visuals & Textures underfoot\n{visuals_fmt}\n\n"
                f"## Key Points of Interest\n{poi_fmt}\n"
            )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def read_location_dossier(self, name_or_slug: str) -> str:
        """Reads location dossier Markdown file."""
        filepath = self._resolve_filepath(self.loc_dir, name_or_slug)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Location dossier not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def list_location_dossiers(self) -> List[str]:
        """Lists all location dossier filenames."""
        if not os.path.exists(self.loc_dir):
            return []
        return [f for f in os.listdir(self.loc_dir) if f.endswith(".md")]

    # --- Faction Dossiers ---

    def save_faction_dossier(
        self,
        name: str,
        motto: str = "",
        ideology: str = "",
        overview: str = "",
        members: Optional[List[str]] = None,
        resources: Optional[List[str]] = None,
        raw_content: Optional[str] = None
    ) -> str:
        """Saves faction dossier Markdown file. Returns the created file path."""
        filepath = self._resolve_filepath(self.fac_dir, name)

        if raw_content:
            content = raw_content
        else:
            members_list = members or []
            resources_list = resources or []

            members_fmt = "\n".join([f"- {m}" for m in members_list]) if members_list else "None specified."
            resources_fmt = "\n".join([f"- {r}" for r in resources_list]) if resources_list else "None specified."

            content = (
                f"# Faction Dossier: {name}\n\n"
                f"**Motto:** {motto}  \n"
                f"**Ideology:** {ideology}\n\n"
                f"## Overview & Goals\n{overview}\n\n"
                f"## Key Members & Figures\n{members_fmt}\n\n"
                f"## Resources & Assets\n{resources_fmt}\n"
            )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def read_faction_dossier(self, name_or_slug: str) -> str:
        """Reads faction dossier Markdown file."""
        filepath = self._resolve_filepath(self.fac_dir, name_or_slug)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Faction dossier not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def list_faction_dossiers(self) -> List[str]:
        """Lists all faction dossier filenames."""
        if not os.path.exists(self.fac_dir):
            return []
        return [f for f in os.listdir(self.fac_dir) if f.endswith(".md")]
