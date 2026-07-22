from typing import Optional
from manuscriptfinesse.providers.base import BaseLLMProvider
from manuscriptfinesse.agents.base_agent import BaseAgent, load_input

DEFAULT_MINER_SYSTEM_PROMPT = (
    "You are the Stage 1 KnowledgeMinerAgent for ManuscriptFinesse. "
    "Your objective is to analyze the provided source notes, transcript, or raw premise "
    "and extract a comprehensive, structured Project Brief in Markdown format.\n\n"
    "The output MUST contain the following explicit sections:\n"
    "- ## Premise\n"
    "- ## Themes & Tropes\n"
    "- ## Target Tone\n"
    "- ## Primary Entities\n"
    "- ## Non-Negotiables\n\n"
    "Ensure all key details from the input are preserved and organized clearly under these headers."
)


class KnowledgeMinerAgent(BaseAgent):
    """Stage 1 Context Intake Agent responsible for mining raw source material into a structured Project Brief."""

    def __init__(self, provider: BaseLLMProvider, system_prompt: Optional[str] = None):
        super().__init__(
            provider=provider,
            system_prompt=system_prompt or DEFAULT_MINER_SYSTEM_PROMPT
        )

    def run(self, raw_input: str) -> str:
        """Reads input file or raw text and generates project_brief.md content."""
        content = load_input(raw_input)
        user_prompt = f"Analyze the following raw context payload and extract a structured Project Brief:\n\n{content}"
        return self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )
