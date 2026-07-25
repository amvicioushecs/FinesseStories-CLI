import sys
import shlex
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from typer.testing import CliRunner
from manuscriptfinesse.agents.natural_language import NaturalLanguageAgent


def launch_repl(natural_language: bool = True) -> None:
    """Launches an interactive REPL shell session for ManuscriptFinesse.
    
    Args:
        natural_language: If True, enables natural language processing mode where
                         users can type requests in plain English. If False, uses
                         traditional command mode.
    """
    console = Console()
    
    if natural_language:
        console.print(
            Panel.fit(
                "[bold green]ManuscriptFinesse Natural Language Interface[/bold green]\n"
                "[dim]Type your requests in plain English, or [bold]help[/bold] for examples.\n"
                "Type [bold]exit[/bold] / [bold]quit[/bold] to leave.[/dim]",
                border_style="cyan",
            )
        )
        nl_agent = NaturalLanguageAgent()
    else:
        console.print(
            Panel.fit(
                "[bold green]ManuscriptFinesse Interactive REPL Shell[/bold green]\n"
                "[dim]Type [bold]help[/bold] for available commands, or [bold]exit[/bold] / [bold]quit[/bold] to leave.[/dim]",
                border_style="cyan",
            )
        )
    
    runner = CliRunner()

    while True:
        try:
            line = input("mf> " if not natural_language else "You: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nExiting interactive shell.")
            break

        if not line:
            continue

        if line.lower() in ("exit", "quit", "q"):
            console.print("Exiting interactive shell.")
            break

        if natural_language:
            # Handle natural language mode
            if line.lower() == "help":
                _show_natural_language_help(console)
                continue
            
            response = nl_agent.process_request(line)
            console.print(response)
        else:
            # Handle traditional command mode
            if line.lower() == "help":
                _show_traditional_help(console)
                continue

            try:
                args = shlex.split(line)
            except Exception as e:
                console.print(f"[red]Error parsing command inputs: {e}[/red]")
                continue

            from manuscriptfinesse.cli.main import app

            res = runner.invoke(app, args)
            if res.output:
                console.print(res.output.rstrip())


def _show_natural_language_help(console: Console) -> None:
    """Display help for natural language mode."""
    console.print("[bold cyan]Natural Language Examples:[/bold cyan]")
    examples = [
        '"Create a new fantasy novel called The Dragon\'s Quest"',
        '"Ingest my notes from story_ideas.txt"',
        '"Create a character dossier for John Smith"',
        '"Generate an outline with 20 chapters"',
        '"Draft chapter 5"',
        '"Polish chapter 3"',
        '"Export to EPUB format"',
        '"Build the story bible from all dossiers"',
    ]
    for ex in examples:
        console.print(f"  {ex}")
    
    console.print("\n[dim]Tip: You can be conversational. The AI will understand your intent.[/dim]")


def _show_traditional_help(console: Console) -> None:
    """Display help for traditional command mode."""
    console.print("[bold cyan]Available Shell Commands:[/bold cyan]")
    console.print("  init [--title <title>]             Initialize project workspace")
    console.print("  ingest <file_path_or_text>        Stage 1: Context Intake & Brief")
    console.print("  dossiers                           Stage 2: Character/World Dossiers")
    console.print("  bible                              Stage 3: Story Bible Synthesis")
    console.print("  outline [--words W] [--chapters C] Stage 4: Granular Outlining")
    console.print("  draft [--chapter C]                Stage 5: Recursive Drafting & Audit")
    console.print("  polish [--chapter C]               Stage 6: Line Editing & Polish")
    console.print("  export [--format F]                Stage 6: Publishing Export")
    console.print("  exit / quit                        Exit interactive shell")
