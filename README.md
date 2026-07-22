# 📚 ManuscriptFinesse (FinesseStories-CLI)

**ManuscriptFinesse** is a command-line tool and interactive AI writing suite designed to take your book from a simple idea all the way to a finished, self-published manuscript.

Whether you're writing a fantasy novel, sci-fi epic, romance, or thriller, ManuscriptFinesse guides you through **6 structured stages**:

```
 [STAGE 1] Ingest Idea  ──►  Create Project Brief
      │
      ▼
 [STAGE 2] World Building  ──►  Characters, Factions & Sensory Location Dossiers
      │
      ▼
 [STAGE 3] Story Bible  ──►  Master bible.json (Single Source of Truth)
      │
      ▼
 [STAGE 4] Outlining  ──►  Granular Chapter Matrix & Word Count Targets
      │
      ▼
 [STAGE 5] Recursive Drafting  ──►  Prose Writing & Continuity Auditor
      │
      ▼
 [STAGE 6] Polish & Export  ──►  EPUB, DOCX (Standard Manuscript), & Markdown
```

---

## 🚀 Quick Start (5-Minute Tutorial)

### Step 1: Installation

Ensure you have Python 3.10+ installed. Install the package in editable mode:

```bash
git clone https://github.com/amvicioushecs/FinesseStories-CLI.git
cd FinesseStories-CLI
pip install -e .
```

Verify installation:
```bash
mf --help
```

---

### Step 2: Configure AI API Keys (Optional but Recommended)

ManuscriptFinesse supports Google Gemini, OpenRouter, OpenAI, and Anthropic models. Set your API key in your terminal environment:

**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-gemini-api-key-here"
# or for OpenRouter:
$env:OPENROUTER_API_KEY="your-openrouter-api-key-here"
```

*Note: If no API keys are provided, ManuscriptFinesse automatically runs in offline mock mode so you can test and explore immediately!*

---

### Step 3: Create a New Book Project

Create a new manuscript directory and project setup:

```bash
mf init --title "The Astral Citadel" --genre "Sci-Fi Fantasy" --target-words 80000
```

---

### Step 4: Run the Interactive Shell or Commands

You can run commands one by one, or launch the interactive shell:

```bash
mf shell
```

Inside the interactive shell:
```
mf> ingest "A space wizard and a starship captain must protect an ancient cosmic artifact from an empire."
mf> dossiers
mf> bible
mf> outline
mf> draft
mf> polish
mf> export --format all
```

Your completed book files (`.epub`, `.docx`, `.md`) will be generated inside the `exports/` folder! 🎉

---

## 📖 Command Reference & Detailed Guide

### 1. Initialize Project (`mf init`)
Sets up the workspace folder structure (`bible/`, `chapters/`, `exports/`, `.manuscriptfinesse/`).

```bash
mf init --title "My Epic Book" --genre "Fantasy" --target-words 75000
```

---

### 2. Context & Idea Ingestion (`mf ingest`)
Takes your raw notes, world idea, or synopsis and organizes it into a clean `project_brief.md` file.

- **From raw text in terminal:**
  ```bash
  mf ingest "In a world covered in perpetual ice, a young cartographer finds a map to an ancient warm valley."
  ```
- **From an existing text/markdown file:**
  ```bash
  mf ingest path/to/my_notes.txt
  ```

---

### 3. Character & Sensory Location Builder (`mf dossiers`)
Generates individual Markdown dossiers for every character, location, and faction in your story.

- **Generate default cast and locations:**
  ```bash
  mf dossiers
  ```
- **Create a specific detailed character:**
  ```bash
  mf dossiers --character "Aria Thorne"
  ```
- **Create an immersive 5-sense sensory location:**
  ```bash
  mf dossiers --location "The Frozen Outpost"
  ```
  *(Sensory location files record temperature, moisture, lighting, Olfactory smells, Auditory sounds, and visual textures underfoot so scenes feel alive!)*

---

### 4. Story Bible Synthesizer (`mf bible`)
Compiles all character files, sensory location files, faction files, and the project brief into a single master JSON file (`bible.json` v3.0). This becomes the Single Source of Truth for the AI during writing so characters never forget their backstories or break canon.

```bash
mf bible
```

---

### 5. Outlining Engine (`mf outline`)
Calculates chapter word count targets, assigns point-of-view (POV) characters, generates chapter titles, and writes detailed scene beats for the whole book.

```bash
mf outline --words 80000 --chapters 20
```

---

### 6. Recursive Drafting & Continuity Auditor (`mf draft`)
Writes your book chapter by chapter. Each chapter uses a **sliding context window** (reading the previous chapters' summaries) and passes through the **Continuity Auditor** to catch plot holes or repetitive language loop bugs.

- **Draft all chapters automatically:**
  ```bash
  mf draft
  ```
- **Draft a single specific chapter:**
  ```bash
  mf draft --chapter 1
  ```

---

### 7. Line Editing & Prose Polish (`mf polish`)
Enhances sentence rhythm, sensory imagery, and dialogue flow without changing story events.

- **Polish all chapters:**
  ```bash
  mf polish
  ```
- **Polish a specific chapter:**
  ```bash
  mf polish --chapter 1
  ```

---

### 8. Self-Publishing Exporters (`mf export`)
Compiles your individual chapters and metadata (Title, Author, Copyright, TOC, Author Bio) into publish-ready formats:

```bash
# Export all formats (EPUB, DOCX, Markdown)
mf export --format all

# Export specific format
mf export --format epub
mf export --format docx
mf export --format markdown
```

- **`.epub`**: Ready to upload to Amazon KDP, Apple Books, and Kobo.
- **`.docx`**: Formatted according to Standard Manuscript guidelines (12pt Times New Roman, 1.5 line spacing, 1-inch margins, first-line indents).
- **`.md`**: Single merged Markdown manuscript file.

---

## 📂 Project Directory Structure

When you work on a project with ManuscriptFinesse, your directory looks like this:

```
my-book-project/
├── .manuscriptfinesse/
│   └── project.json         # Project settings & metadata
├── project_brief.md          # Stage 1: Premise, themes & target tone
├── bible.json               # Stage 3: Master Story Bible (v3.0)
├── bible/
│   ├── characters/          # Stage 2: Individual character .md dossiers
│   │   ├── aria-thorne.md
│   │   └── captain-kael.md
│   ├── locations/           # Stage 2: Immersive 5-sense location .md dossiers
│   │   └── frozen-outpost.md
│   └── factions/            # Stage 2: Faction & alliance .md dossiers
│       └── the-iron-guild.md
├── chapters/                # Stage 5 & 6: Generated chapter drafts & audits
│   ├── ch01_draft.md
│   ├── ch01_audit.md
│   ├── ch01_polished.md
│   └── ...
└── exports/                 # Stage 6: Publishable book files
    ├── My_Book_Manuscript.epub
    ├── My_Book_Manuscript.docx
    └── My_Book_Manuscript.md
```

---

## 💡 Troubleshooting & FAQ

**Q: Do I need an expensive API key to use ManuscriptFinesse?**  
A: No! If no API key is provided, the tool automatically uses a built-in Mock Provider so you can test all features and workflows for free. When you are ready to write real prose, set your `GEMINI_API_KEY` or `OPENROUTER_API_KEY`.

**Q: Can I manually edit the character dossiers or chapter drafts?**  
A: Yes! All dossiers in `bible/` and chapters in `chapters/` are plain Markdown files. You can open and edit them in any text editor. Re-run `mf bible` anytime you edit dossiers to update the master Story Bible.

---

## 📄 License
MIT License. Created by [amvicioushecs](https://github.com/amvicioushecs).
