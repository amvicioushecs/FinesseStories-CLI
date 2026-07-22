import json
from typing import Optional
from manuscriptfinesse.agents.base_agent import BaseAgent, load_input
from manuscriptfinesse.core.models import StoryBibleSchema
from manuscriptfinesse.providers.base import BaseLLMProvider

DEFAULT_POLISHER_SYSTEM_PROMPT = (
    "You are the Stage 6 Polish Agent (PolisherAgent) for ManuscriptFinesse. "
    "Your objective is line editing, prose refinement, pacing, and rhythm enhancement "
    "while maintaining canon and character voice."
)


class PolisherAgent(BaseAgent):
    """Stage 6 Polish Agent responsible for line editing and prose refinement."""

    def __init__(self, provider: BaseLLMProvider, system_prompt: Optional[str] = None):
        super().__init__(
            provider=provider,
            system_prompt=system_prompt or DEFAULT_POLISHER_SYSTEM_PROMPT
        )

    def run(self, raw_input: str) -> str:
        """Executes polishing from raw text or JSON input payload containing draft_text and bible."""
        content = load_input(raw_input)
        draft_text = content
        bible = StoryBibleSchema()

        if content and content.strip().startswith("{"):
            try:
                parsed = json.loads(content.strip())
                if isinstance(parsed, dict):
                    if "draft_text" in parsed:
                        draft_text = parsed["draft_text"]
                    elif "content" in parsed:
                        draft_text = parsed["content"]
                    elif "draft" in parsed:
                        draft_text = parsed["draft"]

                    if "bible" in parsed:
                        bible = StoryBibleSchema.model_validate(parsed["bible"])
            except Exception:
                pass

        return self.polish_chapter(draft_text=draft_text, bible=bible)

    def polish_chapter(self, draft_text: str, bible: StoryBibleSchema) -> str:
        """Polishes chapter prose given draft_text and StoryBibleSchema context."""
        canon_str = "\n".join([f"- {r}" for r in bible.canon_rules]) if bible.canon_rules else "None specified"

        char_str = ""
        if bible.characters:
            char_list = []
            for c in bible.characters:
                voice = c.voice_and_speech or "Standard"
                char_list.append(f"Character: {c.name} (Role: {c.role}, Voice: {voice})")
            char_str = "\n" + "\n".join(char_list)

        user_prompt = (
            f"=== CANON RULES ===\n{canon_str}\n"
            f"=== CHARACTER PROFILES ==={char_str}\n\n"
            f"=== DRAFT TEXT TO POLISH ===\n{draft_text}\n\n"
            f"Perform line editing and prose polishing. Refine sensory details, pacing, rhythm, "
            f"and sentence variety while strictly respecting canon and character voices."
        )

        response = self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        if not response or response.strip() == "":
            return draft_text

        return response
