# ManuscriptFinesse Architecture & System Design Specification

**Document Version:** 1.1.0  
**Date:** July 22, 2026  
**Status:** Approved by Author  
**Target Package:** `manuscriptfinesse` (CLI & Agentic Engine)

---

## 1. Overview & Vision

**ManuscriptFinesse** is a high-continuity, 6-stage AI fiction generation engine and interactive CLI suite. It guides authors from an initial raw idea or context dump all the way to a published manuscript formatted for KDP, EPUB, PDF, and DOCX.

### Key Principles
1. **Stage-Gated Author Control:** The author remains in full control via approval gates between every major development stage (Brief → Character/World Dossiers → Story Bible SSOT → Outline Matrix → Recursive Drafts → Polish & Export).
2. **Deep Granular World & Character Dossiers:** Dedicated Markdown files (`.md`) are generated and maintained for every character, location, and faction in Stage 2, which are then compiled into the machine-readable Story Bible (`bible.json` v3.0) in Stage 3.
3. **Multi-Provider LLM & Specialized Role Routing:** Connects natively to Google Gemini, OpenRouter, OpenAI, Anthropic, and Ollama, allowing custom per-role model assignments (e.g. Gemini 2.5 Flash for outliner, Claude 3.5 Sonnet / Gemini Pro for drafter, local Ollama for auditor).
4. **Continuity Auditing & Loop Prevention:** Automatic sliding context windows combined with real-time audit passes to prevent character voice drift, canon rule violations, and text repetition loops.
5. **Complete Self-Publishing Suite:** Automated front/back matter generation (Title Page, Copyright, TOC, About Author) with KDP, EPUB, PDF, and DOCX styling.

---

## 2. End-to-End System Pipeline

```
 [ Input Stream (Notes / Context / Premise) ]
        │
        ▼
 [ STAGE 1: Intake & Knowledge Mining ]
        ├── Source Provenance Logging
        └── Project Brief Generation (`project_brief.md`)
        │
        ▼  ───► [ User Approval Gate 1 ]
 [ STAGE 2: World & Character Architecture (Dossiers) ]
        ├── Character Dossiers (`bible/characters/<name>.md`)
        ├── Location Dossiers (`bible/locations/<name>.md`)
        └── Faction Dossiers (`bible/factions/<name>.md`)
        │
        ▼  ───► [ User Approval Gate 2 ]
 [ STAGE 3: Story Bible Synthesis ]
        └── Master Single Source of Truth (`bible.json` v3.0)
        │
        ▼  ───► [ User Approval Gate 3 ]
 [ STAGE 4: Outline Engine ]
        ├── Granular Chapter Matrix
        ├── Scene Beat Breakdown
        └── Target Word Count Allocations
        │
        ▼  ───► [ User Approval Gate 4 ]
 [ STAGE 5: Recursive Draft Execution ]
        ├── Sliding Context Window Assembly
        ├── Drafter Agent Pass
        └── Continuity Auditor Pass (Canon & Loop Check)
        │
        ▼  ───► [ User Approval Gate 5 ]
 [ STAGE 6: Polish, Verification & Export ]
        ├── Line Editing & Prose Enhancement
        ├── Originality & Consistency Audit Report
        └── KDP-Compliant Export (EPUB, PDF, DOCX, MD)
```

---

## 3. Detailed Stage Specifications

### Stage 1: Context Intake & Knowledge Mining
- **Input:** Raw notes, world briefs, genre preferences, character sketches, or text transcripts.
- **Agent:** `KnowledgeMinerAgent`
- **Output:** `project_brief.md` containing core premise, themes, target tone, primary entities, and non-negotiables.

### Stage 2: World & Character Architecture (Markdown Dossiers)
- **Agent:** `CharacterWorldBuilderAgent`
- **Outputs:**
  - `bible/characters/<character_name>.md`:
    - Full Name & Aliases
    - Role, Archetype & Relationships
    - Backstory & Origins
    - Personality, Speech Patterns & Voice Rules
    - Physical Appearance & Distinctive Traits
    - Motivations, Internal Flaws & Secrets
    - Special Attributes, Inventory & Unique Abilities
  - `bible/locations/<location_name>.md`:
    - Location Name, Region & Setting Type (Indoors / Outdoors / Underground / Celestial)
    - Scene & Setting Overview (Where am I located, physical boundaries & spatial layout)
    - Environmental & Micro-Climate Profile:
      - Temperature & Climate (Hot, Cold, Freezing, Sweltering, Temperate)
      - Moisture & Humidity (Dry, Arid, Damp, Wet, Rain, Fog, Submerged)
      - Weather, Sky & Illumination (Sunny, Overcast, Cloudy, Moonlit, Bioluminescent, Pitch Black)
    - Immersive 5-Sense Profile:
      - Olfactory (What am I smelling: ozone, damp earth, pine, smoke, salt, sulfur, decay)
      - Auditory (What am I hearing: howling wind, echoing drops, muffled footsteps, oppressive silence)
      - Visual & Textural (Architecture, color palette, light sources, surface textures underfoot)
    - Key Sub-locations & Points of Interest
    - Factions & Notable Inhabitants Present
    - Lore, History & Local Magic/Physics Anomalies
  - `bible/factions/<faction_name>.md`:
    - Name, Emblem & Motto
    - Ideology, Goals & Internal Structure
    - Notable Members & Resources

### Stage 3: Story Bible Synthesis (JSON v3.0)
- **Agent:** `BibleSynthesizerAgent`
- **Output:** `bible.json` (version 3.0) compiled from the Markdown dossiers and project brief into a machine-readable Single Source of Truth (SSOT) containing locked canon rules, character attributes, location index, factions, and chronological ledger.

### Stage 4: Outline Engine & Chapter Matrix
- **Agent:** `OutlinerAgent`
- **Output:** `.manuscriptfinesse/project.json` updated with `chapter_matrix`:
  - Chapter ID, Title, POV Character
  - Act & Arc Assignment
  - Scene-by-Scene Beats
  - Target Word Count Allocation
  - Required Narrative Revelations / Conflict Escalations

### Stage 5: Recursive Draft Execution & Continuity Audit
- **Agents:** `DrafterAgent` and `ContinuityAuditorAgent`
- **Sliding Context Window:** Combines Story Bible v3.0 rules, active character voice profiles, summaries of chapters $N-1$ and $N-2$, and active chapter beats.
- **Audit Pass:** Checks drafted text against locked canon rules, character voice consistency, and hash-based repetition loops.

### Stage 6: Polish, Verification & Publishing Export
- **Agent:** `PolisherAgent` + Exporters
- **Line Editing:** Prose polisher enhances rhythm, sensory depth, pacing, and removes filler.
- **Auto Front/Back Matter:** Title Page, Copyright Notice, TOC, Author Bio, and Acknowledgments.
- **Export Formats:** EPUB, PDF, DOCX (Standard Manuscript format), and KDP-compliant upload bundle.

---

## 4. Multi-Provider LLM Configuration

The project configuration file `.manuscriptfinesse/config.yaml` maps agent roles to specific LLM models across providers:

```yaml
providers:
  gemini:
    api_key_env: GEMINI_API_KEY
  openrouter:
    api_key_env: OPENROUTER_API_KEY
  openai:
    api_key_env: OPENAI_API_KEY
  anthropic:
    api_key_env: ANTHROPIC_API_KEY
  ollama:
    base_url: http://localhost:11434

role_routing:
  miner: gemini/gemini-2.5-flash
  dossier_builder: gemini/gemini-2.5-pro
  synthesizer: gemini/gemini-2.5-flash
  outliner: gemini/gemini-2.5-flash
  drafter: anthropic/claude-3-5-sonnet
  auditor: gemini/gemini-2.5-pro
  polisher: openai/gpt-4o
```

---

## 5. CLI & REPL Commands (`manuscriptfinesse`)

```bash
# Initialize a new manuscript project
mf init --title "The Cipher of Eldoria"

# Stage 1: Ingest reference materials
mf ingest notes.txt context/

# Stage 2: Generate character, location, and faction Markdown dossiers
mf dossiers --build
mf dossier --character "Lyra Vane"

# Stage 3: Synthesize master bible.json (v3.0)
mf bible --synthesize

# Stage 4: Generate chapter matrix & outline
mf outline --generate --target-words 80000

# Stage 5: Draft chapter N or all chapters
mf draft --chapter 1
mf draft --all

# Stage 6: Polish & Export
mf polish --all
mf export --format epub --format pdf --format docx --format kdp

# Interactive REPL Shell
mf shell
```
