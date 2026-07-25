import os
import json
from typing import Optional, List
import typer
from rich.console import Console

from manuscriptfinesse.core.project import ProjectManager
from manuscriptfinesse.core.config import ProjectConfig
from manuscriptfinesse.core.dossier_manager import DossierManager
from manuscriptfinesse.core.models import StoryBibleSchema, ChapterBeat
from manuscriptfinesse.providers.factory import LLMProviderFactory
from manuscriptfinesse.agents.miner import KnowledgeMinerAgent
from manuscriptfinesse.agents.dossier_builder import CharacterWorldBuilderAgent
from manuscriptfinesse.agents.synthesizer import BibleSynthesizerAgent
from manuscriptfinesse.agents.outliner import OutlinerAgent
from manuscriptfinesse.agents.drafter import DrafterAgent, assemble_sliding_context
from manuscriptfinesse.agents.auditor import ContinuityAuditorAgent
from manuscriptfinesse.agents.polisher import PolisherAgent
from manuscriptfinesse.export.epub_exporter import EPUBExporter
from manuscriptfinesse.export.docx_exporter import DOCXExporter
from manuscriptfinesse.export.markdown_exporter import MarkdownExporter

app = typer.Typer(
    name="ManuscriptFinesse",
    help="6-Stage AI Novel Generator & Publishing Suite",
    no_args_is_help=True,
)
console = Console()


@app.command()
def init(
    title: str = typer.Option("Untitled Masterpiece", "--title", "-t", help="Title of your manuscript"),
    genre: str = typer.Option("Unspecified", "--genre", "-g", help="Genre of your manuscript"),
    target_words: int = typer.Option(80000, "--target-words", "-w", help="Target word count"),
):
    """Initialize a new ManuscriptFinesse project workspace."""
    pm = ProjectManager()
    meta = pm.init_project(title=title, genre=genre, target_word_count=target_words)
    console.print(f"[bold green]Initialized ManuscriptFinesse project:[/] [bold cyan]{meta.title}[/bold cyan]")
    console.print(f"Directory: [dim]{pm.root_dir}[/dim]")


@app.command()
def ingest(
    file_path_or_text: str = typer.Argument(..., help="Path to raw source notes file or raw text string"),
):
    """Stage 1: Ingest raw notes/context payload and synthesize Project Brief."""
    pm = ProjectManager()
    config = pm.load_config()
    provider = LLMProviderFactory.get_provider_for_role("miner", config.role_routing)
    agent = KnowledgeMinerAgent(provider=provider)

    console.print(f"[bold cyan][STAGE 1][/bold cyan] Ingesting source notes...")
    brief_markdown = agent.run(file_path_or_text)

    brief_path = os.path.join(pm.root_dir, "project_brief.md")
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(brief_markdown)

    console.print(f"[bold green]✓ Stage 1 Complete:[/] Saved Project Brief to [bold]{brief_path}[/bold]")


@app.command()
def dossiers(
    character: Optional[str] = typer.Option(None, "--character", help="Generate dossier for a specific character"),
    location: Optional[str] = typer.Option(None, "--location", help="Generate dossier for a specific location"),
    faction: Optional[str] = typer.Option(None, "--faction", help="Generate dossier for a specific faction"),
):
    """Stage 2: Build Markdown character, sensory location, and faction dossiers."""
    pm = ProjectManager()
    config = pm.load_config()
    provider = LLMProviderFactory.get_provider_for_role("dossier_builder", config.role_routing)
    agent = CharacterWorldBuilderAgent(provider=provider)
    d_mgr = DossierManager(base_dir=pm.root_dir)

    brief_path = os.path.join(pm.root_dir, "project_brief.md")
    brief_content = ""
    if os.path.exists(brief_path):
        with open(brief_path, "r", encoding="utf-8") as f:
            brief_content = f.read()
    else:
        brief_content = "Default project brief with Protagonist and main setting."

    console.print("[bold cyan][STAGE 2][/bold cyan] Building Markdown dossiers in bible/...")

    if character:
        path = agent.build_and_save_character(dossier_manager=d_mgr, brief_input=brief_content, name=character, role="Main Character")
        console.print(f"Created character dossier: [bold]{path}[/bold]")
    elif location:
        path = agent.build_and_save_location(dossier_manager=d_mgr, brief_input=brief_content, name=location, setting_type="Outdoors")
        console.print(f"Created location dossier: [bold]{path}[/bold]")
    elif faction:
        path = agent.build_and_save_faction(dossier_manager=d_mgr, brief_input=brief_content, name=faction)
        console.print(f"Created faction dossier: [bold]{path}[/bold]")
    else:
        c_path = agent.build_and_save_character(dossier_manager=d_mgr, brief_input=brief_content, name="Protagonist", role="Protagonist")
        l_path = agent.build_and_save_location(dossier_manager=d_mgr, brief_input=brief_content, name="Primary Realm", setting_type="Outdoors")
        f_path = agent.build_and_save_faction(dossier_manager=d_mgr, brief_input=brief_content, name="The Order")
        console.print(f"[bold green]✓ Stage 2 Complete:[/] Generated dossiers in [bold]{d_mgr.base_dir}/bible/[/bold]")


@app.command()
def bible():
    """Stage 3: Synthesize master bible.json (v3.0) Single Source of Truth."""
    pm = ProjectManager()
    config = pm.load_config()
    provider = LLMProviderFactory.get_provider_for_role("synthesizer", config.role_routing)
    agent = BibleSynthesizerAgent(provider=provider)

    console.print("[bold cyan][STAGE 3][/bold cyan] Synthesizing bible.json (v3.0)...")
    bible_schema = agent.synthesize(base_dir=pm.root_dir)

    console.print(f"[bold green]✓ Stage 3 Complete:[/] Synthesized Story Bible v{bible_schema.story_bible_version} to [bold]{os.path.join(pm.root_dir, 'bible.json')}[/bold]")


@app.command()
def outline(
    words: int = typer.Option(80000, "--words", "-w", help="Target word count for entire manuscript"),
    chapters: int = typer.Option(20, "--chapters", "-c", help="Total number of chapters to outline"),
):
    """Stage 4: Generate granular chapter matrix & beat allocations."""
    pm = ProjectManager()
    config = pm.load_config()
    provider = LLMProviderFactory.get_provider_for_role("outliner", config.role_routing)
    agent = OutlinerAgent(provider=provider)

    bible_path = os.path.join(pm.root_dir, "bible.json")
    if os.path.exists(bible_path):
        with open(bible_path, "r", encoding="utf-8") as f:
            bible_data = json.load(f)
        story_bible = StoryBibleSchema.model_validate(bible_data)
    else:
        story_bible = StoryBibleSchema(project_title="Untitled Masterpiece")

    console.print(f"[bold cyan][STAGE 4][/bold cyan] Generating chapter matrix ({chapters} chapters, target {words} words)...")
    chapter_beats = agent.generate_outline(bible=story_bible, total_word_count=words, num_chapters=chapters)

    meta = pm.load_metadata()
    meta.target_word_count = words
    pm.save_metadata(meta)

    outline_path = os.path.join(pm.meta_dir, "outline.json")
    with open(outline_path, "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in chapter_beats], f, indent=2)

    console.print(f"[bold green]✓ Stage 4 Complete:[/] Saved chapter matrix ({len(chapter_beats)} chapters) to [bold]{outline_path}[/bold]")


@app.command()
def draft(
    chapter: int = typer.Option(0, "--chapter", "-c", help="Draft specific chapter number (1-N), or 0 for all chapters"),
):
    """Stage 5: Recursive chapter drafting & continuity auditing."""
    pm = ProjectManager()
    config = pm.load_config()
    drafter_provider = LLMProviderFactory.get_provider_for_role("drafter", config.role_routing)
    auditor_provider = LLMProviderFactory.get_provider_for_role("auditor", config.role_routing)

    drafter = DrafterAgent(provider=drafter_provider)
    auditor = ContinuityAuditorAgent(provider=auditor_provider)

    bible_path = os.path.join(pm.root_dir, "bible.json")
    if os.path.exists(bible_path):
        with open(bible_path, "r", encoding="utf-8") as f:
            bible_data = json.load(f)
        story_bible = StoryBibleSchema.model_validate(bible_data)
    else:
        story_bible = StoryBibleSchema(project_title="Untitled Masterpiece")

    outline_path = os.path.join(pm.meta_dir, "outline.json")
    beats: List[ChapterBeat] = []
    if os.path.exists(outline_path):
        with open(outline_path, "r", encoding="utf-8") as f:
            raw_beats = json.load(f)
            beats = [ChapterBeat.model_validate(b) for b in raw_beats]

    if not beats:
        outliner = OutlinerAgent(provider=LLMProviderFactory.get_provider_for_role("outliner", config.role_routing))
        beats = outliner.generate_outline(bible=story_bible, total_word_count=80000, num_chapters=5)

    chapters_dir = os.path.join(pm.root_dir, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    target_beats = beats if chapter == 0 else [b for i, b in enumerate(beats, start=1) if i == chapter]
    if not target_beats and chapter > 0:
        target_beats = [ChapterBeat(chapter_id=f"ch_{chapter:02d}", title=f"Chapter {chapter}", pov="Protagonist")]

    console.print(f"[bold cyan][STAGE 5][/bold cyan] Recursive draft execution for {len(target_beats)} chapter(s)...")

    for idx, cb in enumerate(target_beats):
        beat_idx = beats.index(cb) if cb in beats else idx
        preceding_beats = beats[:beat_idx]
        sliding_context = assemble_sliding_context(preceding_beats, window_size=2)
        prose = drafter.draft_chapter(beat=cb, bible=story_bible, sliding_summary=sliding_context)
        audit_res = auditor.audit_chapter(draft_text=prose, bible=story_bible)

        ch_num = chapter
        if "ch_" in cb.chapter_id or "ch" in cb.chapter_id:
            try:
                ch_num = int(cb.chapter_id.replace("ch_", "").replace("ch", ""))
            except ValueError:
                pass
        if ch_num <= 0:
            ch_num = 1

        draft_file = os.path.join(chapters_dir, f"ch{ch_num:02d}_draft.md")
        with open(draft_file, "w", encoding="utf-8") as f:
            f.write(prose)

        audit_file = os.path.join(chapters_dir, f"ch{ch_num:02d}_audit.json")
        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump(audit_res, f, indent=2)

        status = audit_res.get("status", "PASSED")
        status_color = "green" if status == "PASSED" else "yellow"
        console.print(f"Drafted [bold]{cb.title}[/bold] -> Saved to [bold]{draft_file}[/bold] (Audit: [{status_color}]{status}[/{status_color}])")

    console.print(f"[bold green]✓ Stage 5 Complete:[/] Drafted and audited chapters in [bold]{chapters_dir}[/bold]")


@app.command()
def polish(
    chapter: int = typer.Option(0, "--chapter", "-c", help="Polish specific chapter number (1-N), or 0 for all drafted chapters"),
):
    """Stage 6: Line editing & prose enhancement."""
    pm = ProjectManager()
    config = pm.load_config()
    provider = LLMProviderFactory.get_provider_for_role("polisher", config.role_routing)
    polisher = PolisherAgent(provider=provider)

    bible_path = os.path.join(pm.root_dir, "bible.json")
    if os.path.exists(bible_path):
        with open(bible_path, "r", encoding="utf-8") as f:
            bible_data = json.load(f)
        story_bible = StoryBibleSchema.model_validate(bible_data)
    else:
        story_bible = StoryBibleSchema(project_title="Untitled Masterpiece")

    chapters_dir = os.path.join(pm.root_dir, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    existing_files = sorted(os.listdir(chapters_dir)) if os.path.exists(chapters_dir) else []
    draft_files = [f for f in existing_files if f.endswith("_draft.md") or (f.endswith(".md") and not f.endswith("_polished.md"))]

    if chapter > 0:
        ch_str = f"ch{chapter:02d}"
        ch_alt = f"ch_{chapter:02d}"
        matched = [f for f in draft_files if ch_str in f or ch_alt in f]
        if not matched:
            fallback_file = f"ch{chapter:02d}_draft.md"
            with open(os.path.join(chapters_dir, fallback_file), "w", encoding="utf-8") as f:
                f.write(f"# Chapter {chapter}\n\nDraft content to be polished.")
            draft_files = [fallback_file]
        else:
            draft_files = matched

    console.print(f"[bold cyan][STAGE 6][/bold cyan] Polishing {len(draft_files)} chapter draft(s)...")

    for df in draft_files:
        src_path = os.path.join(chapters_dir, df)
        if os.path.exists(src_path):
            with open(src_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = f"Draft content for {df}."

        polished_text = polisher.polish_chapter(draft_text=content, bible=story_bible)

        out_name = df.replace("_draft.md", "_polished.md") if "_draft.md" in df else f"polished_{df}"
        out_path = os.path.join(chapters_dir, out_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(polished_text)

        console.print(f"Polished [bold]{df}[/bold] -> Saved to [bold]{out_path}[/bold]")

    console.print(f"[bold green]✓ Stage 6 Polish Complete:[/] Polished chapters in [bold]{chapters_dir}[/bold]")


@app.command()
def export(
    format: str = typer.Option("epub", "--format", "-f", help="Export format: epub, docx, markdown, all"),
):
    """Stage 6: Build publishing export bundles (EPUB, DOCX, Markdown, etc.)."""
    pm = ProjectManager()
    meta = pm.load_metadata()

    chapters_dir = os.path.join(pm.root_dir, "chapters")
    export_dir = os.path.join(pm.root_dir, "export")
    os.makedirs(export_dir, exist_ok=True)

    chapter_list = []
    if os.path.exists(chapters_dir):
        files = sorted(os.listdir(chapters_dir))
        polished_files = [f for f in files if f.endswith("_polished.md")]
        draft_files = [f for f in files if f.endswith("_draft.md")]
        target_files = polished_files if polished_files else (draft_files if draft_files else [f for f in files if f.endswith(".md")])

        for idx, f_name in enumerate(target_files, start=1):
            with open(os.path.join(chapters_dir, f_name), "r", encoding="utf-8") as f:
                content = f.read()
            title = f"Chapter {idx}"
            if content.startswith("# "):
                first_line = content.split("\n")[0]
                title = first_line.replace("# ", "").strip()
            chapter_list.append({"title": title, "content": content})

    if not chapter_list:
        chapter_list = [{"title": "Chapter 1", "content": "Sample manuscript chapter content."}]

    fmt_lower = format.lower()
    console.print(f"[bold cyan][STAGE 6 EXPORT][/bold cyan] Exporting manuscript to [bold]{fmt_lower}[/bold]...")

    formats_to_run = ["epub", "docx", "markdown"] if fmt_lower == "all" else [fmt_lower]

    for fmt in formats_to_run:
        if fmt == "epub":
            out_file = os.path.join(export_dir, f"{meta.title.lower().replace(' ', '_')}.epub")
            exporter = EPUBExporter(title=meta.title, author="ManuscriptFinesse Author")
            exporter.compile(chapters=chapter_list, output_path=out_file)
            console.print(f"Exported EPUB: [bold]{out_file}[/bold]")
        elif fmt == "docx":
            out_file = os.path.join(export_dir, f"{meta.title.lower().replace(' ', '_')}.docx")
            exporter = DOCXExporter(title=meta.title, author="ManuscriptFinesse Author")
            exporter.compile(chapters=chapter_list, output_path=out_file)
            console.print(f"Exported DOCX: [bold]{out_file}[/bold]")
        elif fmt in ["markdown", "md"]:
            out_file = os.path.join(export_dir, f"{meta.title.lower().replace(' ', '_')}.md")
            exporter = MarkdownExporter(title=meta.title, author="ManuscriptFinesse Author")
            exporter.compile(chapters=chapter_list, output_path=out_file)
            console.print(f"Exported Markdown: [bold]{out_file}[/bold]")
        else:
            console.print(f"[yellow]Unknown export format '{fmt}', skipping.[/yellow]")

    console.print(f"[bold green]✓ Stage 6 Export Complete:[/] Publishing bundle written to [bold]{export_dir}[/bold]")


@app.command()
def shell(natural_language: bool = typer.Option(True, "--natural-language", "-nl", help="Enable natural language mode (default: True)")):
    """Launch interactive REPL shell session for ManuscriptFinesse.

    By default, starts in natural language mode where you can type requests
    in plain English. Use --no-natural-language for traditional command mode.
    """
    from manuscriptfinesse.cli.repl import launch_repl

    launch_repl(natural_language=natural_language)


@app.command()
def chat():
    """Launch the Natural Language Interface for ManuscriptFinesse.

    This provides an AI-powered conversational interface where you can
    interact with ManuscriptFinesse using plain English instead of
    memorizing terminal commands.

    Examples:
        - "Create a new fantasy novel called The Dragon's Quest"
        - "Ingest my notes from story_ideas.txt"
        - "Create a character dossier for John Smith"
        - "Generate an outline with 20 chapters"
        - "Draft chapter 5"
        - "Export to EPUB format"
    """
    from manuscriptfinesse.cli.repl import launch_repl

    launch_repl(natural_language=True)


if __name__ == "__main__":
    app()
