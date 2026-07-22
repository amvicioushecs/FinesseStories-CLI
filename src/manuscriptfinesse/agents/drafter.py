import json
import os
from typing import Optional, List, Dict, Any
from manuscriptfinesse.agents.base_agent import BaseAgent, load_input
from manuscriptfinesse.core.models import ChapterBeat, StoryBibleSchema, CharacterDossier, LocationDossier
from manuscriptfinesse.providers.base import BaseLLMProvider

DEFAULT_DRAFTER_SYSTEM_PROMPT = (
    "You are the Stage 5 Recursive Drafting Agent (DrafterAgent) for ManuscriptFinesse. "
    "Your objective is to craft rich, immersive fiction novel chapter prose incorporating the active POV "
    "character perspective, chapter beats, canon rules, sensory profiles, and sliding context from preceding chapters."
)


def assemble_sliding_context(preceding_chapters: List[ChapterBeat], window_size: int = 2) -> str:
    """Assembles a sliding context window string from the last `window_size` preceding chapters."""
    if not preceding_chapters or window_size <= 0:
        return ""
    recent = preceding_chapters[-window_size:]
    summaries = []
    for c in recent:
        s = c.summary or ("; ".join(c.beats) if c.beats else f"Chapter {c.chapter_id} drafted.")
        summaries.append(f"Chapter {c.chapter_id} ({c.title}) POV: {c.pov}\nSummary: {s}")
    return "\n\n".join(summaries)


class DrafterAgent(BaseAgent):
    """Stage 5 Recursive Drafting Agent responsible for drafting chapter prose."""

    def __init__(self, provider: BaseLLMProvider, system_prompt: Optional[str] = None):
        super().__init__(
            provider=provider,
            system_prompt=system_prompt or DEFAULT_DRAFTER_SYSTEM_PROMPT
        )

    def assemble_sliding_context(self, preceding_chapters: List[ChapterBeat], window_size: int = 2) -> str:
        """Helper method to assemble sliding context window string."""
        return assemble_sliding_context(preceding_chapters, window_size=window_size)

    def run(self, raw_input: str) -> str:
        """Executes drafting from raw JSON input (ChapterBeat or dict with beat/bible) or text."""
        content = load_input(raw_input)
        beat = ChapterBeat(chapter_id="ch_01", title="Chapter 1", pov="Protagonist")
        bible = StoryBibleSchema()
        sliding_summary = ""

        if content and content.strip().startswith("{"):
            try:
                parsed = json.loads(content.strip())
                if "beat" in parsed:
                    beat = ChapterBeat.model_validate(parsed["beat"])
                elif "chapter_id" in parsed:
                    beat = ChapterBeat.model_validate(parsed)

                if "bible" in parsed:
                    bible = StoryBibleSchema.model_validate(parsed["bible"])

                sliding_summary = parsed.get("sliding_summary", "")
            except Exception:
                pass

        return self.draft_chapter(beat=beat, bible=bible, sliding_summary=sliding_summary)

    def draft_chapter(self, beat: ChapterBeat, bible: StoryBibleSchema, sliding_summary: str = "") -> str:
        """Drafts chapter prose given a ChapterBeat, StoryBibleSchema, and sliding_summary context."""
        # Find POV character dossier if available
        pov_char: Optional[CharacterDossier] = None
        if bible.characters:
            for char in bible.characters:
                if char.name.lower() in beat.pov.lower() or beat.pov.lower() in char.name.lower():
                    pov_char = char
                    break

        pov_info = f"POV Character: {beat.pov}\n"
        if pov_char:
            pov_info += (
                f"Role: {pov_char.role}\n"
                f"Voice & Speech: {pov_char.voice_and_speech}\n"
                f"Physical Appearance: {pov_char.physical_appearance}\n"
                f"Personality: {pov_char.personality}\n"
                f"Motivations: {pov_char.motivations}\n"
            )

        # Canon rules
        canon_str = "\n".join([f"- {r}" for r in bible.canon_rules]) if bible.canon_rules else "None specified"

        # Beats & targets
        beats_str = "\n".join([f"- {b}" for b in beat.beats]) if beat.beats else "No beats defined."

        # Locations info if applicable
        locations_info = ""
        if bible.locations:
            loc_list = []
            for loc in bible.locations:
                sensory_smells = ", ".join(loc.smells) if loc.smells else "N/A"
                sensory_sounds = ", ".join(loc.sounds) if loc.sounds else "N/A"
                loc_list.append(
                    f"Location: {loc.name} ({loc.setting_type})\n"
                    f"  Temp: {loc.temperature}, Moisture: {loc.moisture}\n"
                    f"  Smells: {sensory_smells}\n"
                    f"  Sounds: {sensory_sounds}"
                )
            locations_info = "\n\n=== RELEVANT LOCATIONS ===\n" + "\n".join(loc_list)

        sliding_str = f"\n\n=== PRECEDING CHAPTER CONTEXT ===\n{sliding_summary}" if sliding_summary else ""

        user_prompt = (
            f"=== ACTIVE CHAPTER BEAT ===\n"
            f"Chapter ID: {beat.chapter_id}\n"
            f"Title: {beat.title}\n"
            f"Target Word Count: {beat.target_word_count}\n\n"
            f"=== POV CONTEXT ===\n{pov_info}\n"
            f"=== CANON RULES ===\n{canon_str}"
            f"{locations_info}"
            f"{sliding_str}\n\n"
            f"=== SCENE BEATS ===\n{beats_str}\n\n"
            f"Write the full prose for {beat.title}. Ensure deep sensory engagement, strict adherence to canon, "
            f"and authentic character voice."
        )

        response = self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        if not response or response.strip() == "":
            return f"# {beat.title}\n\nDraft prose for {beat.title} from the POV of {beat.pov}."

        return response
