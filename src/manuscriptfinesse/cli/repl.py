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
                         users can type requests in plain English or use slash commands.
                         If False, uses traditional command mode.
    """
    console = Console()
    
    if natural_language:
        console.print(
            Panel.fit(
                "[bold green]ManuscriptFinesse Natural Language Interface[/bold green]\n"
                "[dim]Type your requests in plain English or use slash commands.\n\n"
                "Examples:\n"
                "  • \"Create a new fantasy novel called The Dragon's Quest\"\n"
                "  • /init --title \"My Novel\" --genre fantasy\n"
                "  • /draft 5\n"
                "  • /export --format epub\n\n"
                "Type [bold]/help[/bold] for all slash commands, or [bold]exit[/bold] to leave.[/dim]",
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
            # Handle natural language mode (including slash commands)
            if line.lower() == "/help" or line.lower() == "help":
                _show_slash_command_help(console)
                continue
            
            response = nl_agent.process_request(line)
            
            # Handle special return values from slash commands
            if response == "__EXIT__":
                console.print("Exiting interactive shell.")
                break
            elif response == "__MODE__":
                natural_language = False
                console.print("[bold cyan]Switched to Traditional Command mode[/bold cyan]")
                console.print("[dim]Now using standard CLI command syntax.[/dim]")
                continue
            elif response == "__HELP__":
                _show_slash_command_help(console)
                continue
            else:
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
    console.print("[dim]Or use slash commands like /init, /draft, /export. Type /help for list.[/dim]")


def _show_slash_command_help(console: Console) -> None:
    """Display help for slash commands."""
    console.print("[bold cyan]Available Slash Commands:[/bold cyan]")
    commands = [
        ("/init", "Initialize a new project", "[--title <title>] [--genre <genre>] [--target-words <n>]"),
        ("/ingest", "Ingest raw notes/source material", "<file_path_or_text>"),
        ("/dossiers", "Build character/location/faction dossiers", "[--character <name>] [--location <name>] [--faction <name>]"),
        ("/bible", "Synthesize master story bible", ""),
        ("/outline", "Generate chapter outline", "[--words <n>] [--chapters <n>]"),
        ("/draft", "Draft manuscript chapters", "[--chapter <n>]"),
        ("/polish", "Polish and enhance chapters", "[--chapter <n>]"),
        ("/export", "Export to publishing formats", "[--format epub|docx|markdown|all]"),
        ("/frontmatter", "Generate professional front matter", "[--chapter-titles]"),
        ("/backmatter", "Generate professional back matter", "[--next-book <title>]"),
        ("/mode", "Switch to traditional command mode", ""),
        ("/exit", "Exit the interface", ""),
    ]
    
    for cmd, desc, params in commands:
        console.print(f"  [green]{cmd}[/green] {params}")
        console.print(f"    [dim]{desc}[/dim]")
    
    console.print("\n[dim]Example usage:[/dim]")
    console.print("  [green]/init[/green] --title \"My Novel\" --genre fantasy")
    console.print("  [green]/draft[/green] 5")
    console.print("  [green]/export[/green] --format epub")
    console.print("  [green]/frontmatter[/green]")
    console.print("  [green]/backmatter[/green] --next-book \"Book Two\"")


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
