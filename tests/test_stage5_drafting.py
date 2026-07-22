import json
import pytest
from manuscriptfinesse.agents.base_agent import BaseAgent
from manuscriptfinesse.agents.drafter import DrafterAgent, assemble_sliding_context
from manuscriptfinesse.agents.auditor import ContinuityAuditorAgent, compute_hash_repetition_score
from manuscriptfinesse.core.models import StoryBibleSchema, ChapterBeat, CharacterDossier, LocationDossier
from manuscriptfinesse.providers.base import BaseLLMProvider, MockProvider


class CapturingProvider(BaseLLMProvider):
    """Mock LLM provider that captures the last system and user prompts passed to generate()."""
    def __init__(self, response_text: str = "Default captured response prose."):
        self.response_text = response_text
        self.last_system_prompt = ""
        self.last_user_prompt = ""

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.response_text


def test_drafter_agent_subclass():
    """Verify DrafterAgent inherits from BaseAgent."""
    provider = MockProvider()
    agent = DrafterAgent(provider=provider)
    assert isinstance(agent, BaseAgent)


def test_auditor_agent_subclass():
    """Verify ContinuityAuditorAgent inherits from BaseAgent."""
    provider = MockProvider()
    agent = ContinuityAuditorAgent(provider=provider)
    assert isinstance(agent, BaseAgent)


def test_sliding_window_assembly():
    """Verify sliding context window assembly collects recent chapter summaries up to window_size."""
    ch1 = ChapterBeat(chapter_id="ch_01", title="Chapter 1: The Beginning", pov="Lyra", summary="Lyra discovers the map.")
    ch2 = ChapterBeat(chapter_id="ch_02", title="Chapter 2: The Journey", pov="Kaelen", summary="Kaelen joins Lyra.")
    ch3 = ChapterBeat(chapter_id="ch_03", title="Chapter 3: The Fortress", pov="Lyra", summary="They arrive at Frost Fortress.")

    # Window size 2 should pick ch2 and ch3
    context_2 = assemble_sliding_context([ch1, ch2, ch3], window_size=2)
    assert "ch_02" in context_2
    assert "ch_03" in context_2
    assert "ch_01" not in context_2

    # Window size 1 should pick ch3 only
    context_1 = assemble_sliding_context([ch1, ch2, ch3], window_size=1)
    assert "ch_03" in context_1
    assert "ch_02" not in context_1

    # Empty list
    assert assemble_sliding_context([], window_size=2) == ""


def test_drafter_chapter_drafting_with_pov_context():
    """Verify DrafterAgent incorporates POV character info, beats, canon, and sliding context into LLM prompt."""
    provider = CapturingProvider("Chapter 1 prose generated successfully.")
    agent = DrafterAgent(provider=provider)

    character = CharacterDossier(
        id="char_lyra",
        name="Lyra Vane",
        role="Protagonist",
        voice_and_speech="Sharp, concise, uses nautical metaphors",
        personality="Resourceful, cautious",
        physical_appearance="Tall with silver hair"
    )
    location = LocationDossier(
        id="loc_citadel",
        name="Sunken Citadel",
        setting_type="Subterranean",
        temperature="Freezing",
        moisture="Damp",
        smells=["Ozone", "Brine"],
        sounds=["Dripping water"]
    )
    bible = StoryBibleSchema(
        project_title="Caelum Chronicles",
        canon_rules=["No firearms in Caelum", "Magic requires mana crystals"],
        characters=[character],
        locations=[location]
    )

    beat = ChapterBeat(
        chapter_id="ch_01",
        title="Chapter 1: Into the Deep",
        pov="Lyra Vane",
        target_word_count=3500,
        beats=["Beat 1.1: Descend into citadel", "Beat 1.2: Encounter guardian"]
    )

    sliding_summary = "Chapter ch_00: Lyra departed the surface docks."

    draft_text = agent.draft_chapter(beat=beat, bible=bible, sliding_summary=sliding_summary)

    assert draft_text == "Chapter 1 prose generated successfully."
    # Verify user prompt received by provider contains crucial context
    user_prompt = provider.last_user_prompt
    assert "Lyra Vane" in user_prompt
    assert "Sharp, concise, uses nautical metaphors" in user_prompt
    assert "No firearms in Caelum" in user_prompt
    assert "Sunken Citadel" in user_prompt
    assert "Beat 1.1: Descend into citadel" in user_prompt
    assert "Chapter ch_00: Lyra departed the surface docks." in user_prompt


def test_auditor_hash_repetition_detector():
    """Verify hash repetition score calculation for repetitive vs unique prose."""
    # Unique text
    unique_text = "The quick brown fox jumps over the lazy dog. Shadows fell across the ancient stone archway quietly."
    unique_score = compute_hash_repetition_score(unique_text)
    assert unique_score == 0.0

    # Highly repetitive text
    repeated_sentence = "The darkness swallowed the chamber whole. " * 20
    repetitive_score = compute_hash_repetition_score(repeated_sentence)
    assert repetitive_score > 0.30

    provider = MockProvider()
    auditor = ContinuityAuditorAgent(provider=provider)
    bible = StoryBibleSchema()

    audit_result = auditor.audit_chapter(draft_text=repeated_sentence, bible=bible)
    assert audit_result["repetition_score"] > 0.30
    assert audit_result["status"] in ["WARNING", "CRITICAL"]


def test_auditor_canon_rule_check_and_passed():
    """Verify ContinuityAuditorAgent detects canon violations and passes clean drafts."""
    provider = MockProvider()
    auditor = ContinuityAuditorAgent(provider=provider)

    bible = StoryBibleSchema(
        project_title="Caelum Chronicles",
        canon_rules=["No firearms in Caelum"]
    )

    # Violating draft
    bad_draft = "Lyra drew her firearms and opened fire at the Caelum guards."
    bad_audit = auditor.audit_chapter(draft_text=bad_draft, bible=bible)
    assert bad_audit["status"] == "CRITICAL"
    assert len(bad_audit["canon_violations"]) > 0
    assert "No firearms in Caelum" in bad_audit["canon_violations"][0]

    # Clean draft
    clean_draft = "Lyra drew her silver rapier and stepped into the shadowy archway quietly."
    clean_audit = auditor.audit_chapter(draft_text=clean_draft, bible=bible)
    assert clean_audit["status"] == "PASSED"
    assert len(clean_audit["canon_violations"]) == 0
    assert len(clean_audit["voice_drift_alerts"]) == 0
    assert clean_audit["repetition_score"] < 0.15


def test_drafter_and_auditor_run_methods(tmp_path):
    """Verify run() methods on DrafterAgent and ContinuityAuditorAgent."""
    provider = MockProvider()
    drafter = DrafterAgent(provider=provider)
    auditor = ContinuityAuditorAgent(provider=provider)

    beat = ChapterBeat(chapter_id="ch_01", title="Beginning", pov="Protagonist")
    bible = StoryBibleSchema(project_title="Run Test")

    payload = {
        "beat": beat.model_dump(),
        "bible": bible.model_dump(),
        "sliding_summary": "Previous summary."
    }

    draft_result = drafter.run(json.dumps(payload))
    assert isinstance(draft_result, str)
    assert len(draft_result) > 0

    audit_payload = {
        "draft_text": draft_result,
        "bible": bible.model_dump()
    }
    audit_json = auditor.run(json.dumps(audit_payload))
    audit_data = json.loads(audit_json)
    assert "status" in audit_data
    assert "canon_violations" in audit_data
    assert "repetition_score" in audit_data
