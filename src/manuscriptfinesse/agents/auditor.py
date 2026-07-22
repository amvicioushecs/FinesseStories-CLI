import hashlib
import json
import re
from typing import Dict, Any, List, Optional
from manuscriptfinesse.agents.base_agent import BaseAgent, load_input
from manuscriptfinesse.core.models import StoryBibleSchema
from manuscriptfinesse.providers.base import BaseLLMProvider

DEFAULT_AUDITOR_SYSTEM_PROMPT = (
    "You are the Stage 5 Continuity Auditor Agent (ContinuityAuditorAgent) for ManuscriptFinesse. "
    "Your objective is to audit chapter draft prose against locked Story Bible canon rules, character voice consistency, "
    "and detect phrase or sentence repetition loops."
)


def compute_hash_repetition_score(text: str, n: int = 4) -> float:
    """Computes a repetition score (0.0 to 1.0) based on n-gram hash duplicates in text."""
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < n:
        return 0.0

    ngrams = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]
    if not ngrams:
        return 0.0

    hashes = [hashlib.md5(" ".join(gram).encode('utf-8')).hexdigest() for gram in ngrams]
    unique_hashes = set(hashes)
    duplicate_count = len(hashes) - len(unique_hashes)
    score = duplicate_count / len(hashes)
    return round(score, 4)


class ContinuityAuditorAgent(BaseAgent):
    """Stage 5 Continuity Auditor Agent responsible for auditing drafts for canon violations, voice drift, and loops."""

    def __init__(self, provider: BaseLLMProvider, system_prompt: Optional[str] = None):
        super().__init__(
            provider=provider,
            system_prompt=system_prompt or DEFAULT_AUDITOR_SYSTEM_PROMPT
        )

    def run(self, raw_input: str) -> str:
        """Reads draft text or JSON payload and returns JSON string of audit results."""
        content = load_input(raw_input)
        draft_text = content
        bible = StoryBibleSchema()

        if content and content.strip().startswith("{"):
            try:
                parsed = json.loads(content.strip())
                if "draft_text" in parsed:
                    draft_text = parsed["draft_text"]
                if "bible" in parsed:
                    bible = StoryBibleSchema.model_validate(parsed["bible"])
            except Exception:
                pass

        audit_res = self.audit_chapter(draft_text=draft_text, bible=bible)
        return json.dumps(audit_res, indent=2)

    def audit_chapter(self, draft_text: str, bible: StoryBibleSchema) -> Dict[str, Any]:
        """Audits drafted prose against StoryBibleSchema canon rules and computes repetition score."""
        repetition_score = compute_hash_repetition_score(draft_text)
        canon_violations: List[str] = []
        voice_drift_alerts: List[str] = []

        # Prepare prompt for LLM provider audit pass
        canon_summary = "\n".join([f"- {r}" for r in bible.canon_rules]) if bible.canon_rules else "None"
        char_summary = "\n".join([
            f"- {c.name}: Voice={c.voice_and_speech}, Personality={c.personality}"
            for c in bible.characters
        ]) if bible.characters else "None"

        user_prompt = (
            f"=== STORY BIBLE CANON RULES ===\n{canon_summary}\n\n"
            f"=== CHARACTER VOICE PROFILES ===\n{char_summary}\n\n"
            f"=== CHAPTER DRAFT TEXT ===\n{draft_text[:4000]}\n\n"
            "Audit the draft text. Respond in valid JSON with keys:\n"
            "- 'canon_violations': list of strings detailing any canon rules violated\n"
            "- 'voice_drift_alerts': list of strings detailing any character voice drift\n"
            "- 'audit_notes': string summary\n"
        )

        llm_response = self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        # Attempt parsing LLM response
        if llm_response:
            cleaned = llm_response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r"\s*```$", "", cleaned)
                cleaned = cleaned.strip()
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    if "canon_violations" in parsed and isinstance(parsed["canon_violations"], list):
                        canon_violations.extend(parsed["canon_violations"])
                    if "voice_drift_alerts" in parsed and isinstance(parsed["voice_drift_alerts"], list):
                        voice_drift_alerts.extend(parsed["voice_drift_alerts"])
            except Exception:
                pass

        # Deterministic check for negative canon rules (No X, Cannot X, Never X)
        if bible.canon_rules:
            draft_lower = draft_text.lower()
            for rule in bible.canon_rules:
                rule_lower = rule.lower()
                for prefix in ["no ", "cannot ", "never ", "prohibit ", "prohibited: "]:
                    if prefix in rule_lower:
                        after_prefix = rule_lower.split(prefix, 1)[1].strip()
                        # Extract the target concept before prepositions
                        target_concept = re.split(r'\b(in|on|at|with|under|by|from|to|for|during|against)\b', after_prefix)[0].strip()
                        target_concept = target_concept.rstrip(".")
                        if target_concept and len(target_concept) > 2 and target_concept in draft_lower:
                            violation_msg = f"Potential violation of canon rule: '{rule}' (found forbidden term '{target_concept}')"
                            if violation_msg not in canon_violations:
                                canon_violations.append(violation_msg)
                        break

        # Determine status: "PASSED", "WARNING", "CRITICAL"
        if canon_violations or repetition_score >= 0.30:
            status = "CRITICAL"
        elif voice_drift_alerts or repetition_score >= 0.15:
            status = "WARNING"
        else:
            status = "PASSED"

        return {
            "status": status,
            "canon_violations": canon_violations,
            "voice_drift_alerts": voice_drift_alerts,
            "repetition_score": repetition_score
        }
