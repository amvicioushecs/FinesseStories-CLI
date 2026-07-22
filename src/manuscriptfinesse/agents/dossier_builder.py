from typing import Optional
from manuscriptfinesse.providers.base import BaseLLMProvider
from manuscriptfinesse.agents.base_agent import BaseAgent, load_input
from manuscriptfinesse.core.dossier_manager import DossierManager

DEFAULT_DOSSIER_BUILDER_SYSTEM_PROMPT = (
    "You are the Stage 2 CharacterWorldBuilderAgent for ManuscriptFinesse. "
    "Your objective is to analyze the provided Project Brief and build comprehensive, "
    "highly detailed character dossiers, sensory location dossiers, and faction dossiers in Markdown format.\n\n"
    "Character Dossier Requirements:\n"
    "- Name & Aliases\n"
    "- Role & Relationships\n"
    "- Voice & Speech Rules\n"
    "- Physical Appearance & Distinctive Traits\n"
    "- Personality & Speech\n"
    "- Backstory & Origins\n"
    "- Motivations & Internal Flaws\n"
    "- Secrets\n"
    "- Special Attributes & Unique Abilities\n\n"
    "Sensory Location Dossier Requirements:\n"
    "- Name, Region & Setting Type (Indoors / Outdoors / Subterranean)\n"
    "- Scene & Setting Overview\n"
    "- Environmental Profile (Temperature, Moisture, Weather & Illumination)\n"
    "- Immersive 5-Sense Profile (Olfactory smells, Auditory sounds, Visuals & Textures underfoot)\n"
    "- Key Points of Interest\n"
)


class CharacterWorldBuilderAgent(BaseAgent):
    """Stage 2 Character & Detailed Sensory Location Dossier Builder Agent."""

    def __init__(self, provider: BaseLLMProvider, system_prompt: Optional[str] = None):
        super().__init__(
            provider=provider,
            system_prompt=system_prompt or DEFAULT_DOSSIER_BUILDER_SYSTEM_PROMPT
        )

    def run(self, raw_input: str) -> str:
        """Reads Project Brief (raw text or file path) and generates character/location dossiers."""
        brief_content = load_input(raw_input)
        user_prompt = (
            f"=== PROJECT BRIEF ===\n{brief_content}\n=====================\n"
            "Based on the Project Brief above, generate a set of comprehensive character and sensory location dossiers."
        )
        return self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

    def generate_character_dossier(self, brief_content: str, character_name: str, role: str = "Supporting") -> str:
        """Generates Markdown content for a specific character dossier based on Project Brief."""
        content = load_input(brief_content)
        user_prompt = (
            f"=== PROJECT BRIEF ===\n{content}\n=====================\n"
            f"Generate a detailed Character Dossier for '{character_name}' (Role: {role}).\n"
            "Include sections for Voice, Physical Appearance, Personality, Backstory, Motivations, Secrets, and Special Attributes."
        )
        return self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

    def generate_location_dossier(self, brief_content: str, location_name: str, setting_type: str = "Outdoors") -> str:
        """Generates Markdown content for a sensory location dossier based on Project Brief."""
        content = load_input(brief_content)
        user_prompt = (
            f"=== PROJECT BRIEF ===\n{content}\n=====================\n"
            f"Generate a detailed Sensory Location Dossier for '{location_name}' (Setting Type: {setting_type}).\n"
            "Include Environmental Profile (Temperature, Moisture, Weather/Lighting) and 5-Sense Sensory Profile (Olfactory, Auditory, Visuals & Textures underfoot, Points of Interest)."
        )
        return self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

    def generate_faction_dossier(self, brief_content: str, faction_name: str) -> str:
        """Generates Markdown content for a faction dossier based on Project Brief."""
        content = load_input(brief_content)
        user_prompt = (
            f"=== PROJECT BRIEF ===\n{content}\n=====================\n"
            f"Generate a detailed Faction Dossier for '{faction_name}'.\n"
            "Include Motto, Ideology, Overview, Members, and Resources."
        )
        return self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

    def build_and_save_character(
        self,
        dossier_manager: DossierManager,
        brief_input: str,
        name: str,
        role: str = "Supporting"
    ) -> str:
        """Generates character dossier from Project Brief and saves it using DossierManager."""
        dossier_md = self.generate_character_dossier(brief_content=brief_input, character_name=name, role=role)
        return dossier_manager.save_character_dossier(name=name, role=role, raw_content=dossier_md)

    def build_and_save_location(
        self,
        dossier_manager: DossierManager,
        brief_input: str,
        name: str,
        setting_type: str = "Outdoors"
    ) -> str:
        """Generates sensory location dossier from Project Brief and saves it using DossierManager."""
        dossier_md = self.generate_location_dossier(brief_content=brief_input, location_name=name, setting_type=setting_type)
        return dossier_manager.save_location_dossier(name=name, setting_type=setting_type, raw_content=dossier_md)

    def build_and_save_faction(
        self,
        dossier_manager: DossierManager,
        brief_input: str,
        name: str
    ) -> str:
        """Generates faction dossier from Project Brief and saves it using DossierManager."""
        dossier_md = self.generate_faction_dossier(brief_content=brief_input, faction_name=name)
        return dossier_manager.save_faction_dossier(name=name, raw_content=dossier_md)
