import sys
import shlex
from rich.console import Console
from rich.panel import Panel
from typer.testing import CliRunner


def launch_repl() -> None:
    """Launches an interactive REPL shell session for ManuscriptFinesse."""
    console = Console()
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
            line = input("mf> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nExiting interactive shell.")
            break

        if not line:
            continue

        if line.lower() in ("exit", "quit", "q"):
            console.print("Exiting interactive shell.")
            break

        if line.lower() == "help":
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
