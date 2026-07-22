import json
import re
from typing import List, Dict, Any, Optional
from manuscriptfinesse.agents.base_agent import BaseAgent, load_input
from manuscriptfinesse.core.models import StoryBibleSchema, ChapterBeat
from manuscriptfinesse.providers.base import BaseLLMProvider

DEFAULT_OUTLINER_SYSTEM_PROMPT = (
    "You are the Stage 4 Granular Outlining Agent (OutlinerAgent) for ManuscriptFinesse. "
    "Your objective is to consume the Story Bible (v3.0) and synthesize a comprehensive, "
    "granular chapter matrix including chapter titles, POV assignments, scene beat breakdowns, "
    "and word count allocations.\n\n"
    "Output MUST be valid JSON adhering strictly to a list of ChapterBeat objects or a JSON object with a 'chapters' key."
)


class OutlinerAgent(BaseAgent):
    """Stage 4 Granular Outlining Agent responsible for generating chapter beat breakdown matrix."""

    def __init__(self, provider: BaseLLMProvider, system_prompt: Optional[str] = None):
        super().__init__(
            provider=provider,
            system_prompt=system_prompt or DEFAULT_OUTLINER_SYSTEM_PROMPT
        )

    def run(self, raw_input: str) -> str:
        """Reads Bible JSON (file path, raw JSON, or text) and generates ChapterBeat outline matrix JSON."""
        content = load_input(raw_input)
        bible: Optional[StoryBibleSchema] = None

        if content and (content.strip().startswith("{") or content.strip().startswith("[")):
            try:
                parsed = json.loads(content.strip())
                if isinstance(parsed, dict):
                    bible = StoryBibleSchema.model_validate(parsed)
            except Exception:
                bible = None

        if bible is None:
            bible = StoryBibleSchema(project_title=content.strip() if content else "Untitled Project")

        chapters = self.generate_outline(bible=bible)
        return json.dumps([c.model_dump() for c in chapters], indent=2)

    def generate_outline(
        self,
        bible: StoryBibleSchema,
        total_word_count: int = 80000,
        num_chapters: int = 20
    ) -> List[ChapterBeat]:
        """Generates granular chapter beat matrix for the story bible."""
        if num_chapters <= 0:
            num_chapters = 20
        if total_word_count <= 0:
            total_word_count = 80000

        base_words_per_chapter = total_word_count // num_chapters
        remainder = total_word_count % num_chapters

        # Determine primary POV character from bible if available
        primary_pov = "Protagonist"
        if bible.characters and len(bible.characters) > 0:
            primary_pov = bible.characters[0].name

        # Construct prompt for LLM provider
        char_summary = ", ".join([f"{c.name} ({c.role})" for c in bible.characters]) if bible.characters else "None specified"
        loc_summary = ", ".join([l.name for l in bible.locations]) if bible.locations else "None specified"
        canon_summary = "; ".join(bible.canon_rules) if bible.canon_rules else "None specified"

        user_prompt = (
            f"=== STORY BIBLE == \n"
            f"Title: {bible.project_title}\n"
            f"Canon Rules: {canon_summary}\n"
            f"Characters: {char_summary}\n"
            f"Locations: {loc_summary}\n"
            f"Target Total Word Count: {total_word_count}\n"
            f"Total Chapters: {num_chapters}\n"
            f"=====================\n"
            f"Generate a granular chapter matrix with {num_chapters} chapters. "
            "For each chapter provide chapter_id, title, pov, target_word_count, beats, and summary."
        )

        llm_response = self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        chapters: List[ChapterBeat] = []

        # Attempt parsing LLM JSON response
        cleaned = llm_response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            parsed_data = json.loads(cleaned)
            raw_list = []
            if isinstance(parsed_data, list):
                raw_list = parsed_data
            elif isinstance(parsed_data, dict):
                raw_list = parsed_data.get("chapters") or parsed_data.get("outline") or parsed_data.get("chapter_matrix") or []

            if isinstance(raw_list, list) and len(raw_list) > 0:
                for item in raw_list:
                    if isinstance(item, dict):
                        beat_obj = ChapterBeat.model_validate(item)
                        chapters.append(beat_obj)
        except Exception:
            chapters = []

        # Fallback generator if LLM output was not structured JSON matching chapters
        if not chapters:
            chapters = []
            for i in range(1, num_chapters + 1):
                target_words = base_words_per_chapter + (remainder if i == num_chapters else 0)
                ch_id = f"ch_{i:02d}"
                ch_title = f"Chapter {i}"
                beats = [
                    f"Beat {i}.1: Scene entry and situation setup",
                    f"Beat {i}.2: Conflict escalation and complication",
                    f"Beat {i}.3: Scene resolution and hook for next chapter"
                ]
                summary = f"Summary for Chapter {i} focusing on {primary_pov}."
                chapters.append(
                    ChapterBeat(
                        chapter_id=ch_id,
                        title=ch_title,
                        pov=primary_pov,
                        target_word_count=target_words,
                        actual_word_count=0,
                        status="outlined",
                        beats=beats,
                        summary=summary
                    )
                )

        return chapters
