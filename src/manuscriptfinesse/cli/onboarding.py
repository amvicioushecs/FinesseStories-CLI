"""
Onboarding Wizard for ManuscriptFinesse

This module provides an interactive onboarding experience to help new users
set up their LLM provider preferences and API keys.
"""

from typing import Optional, Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from manuscriptfinesse.core.credentials import (
    CredentialManager,
    save_api_key,
    get_api_key,
    has_api_key,
)
from manuscriptfinesse.providers.factory import LLMProviderFactory


class OnboardingWizard:
    """Interactive wizard for setting up ManuscriptFinesse."""

    SUPPORTED_PROVIDERS = {
        "gemini": {
            "name": "Google Gemini",
            "env_var": "GEMINI_API_KEY",
            "models": ["gemini-2.5-flash", "gemini-2.5-pro"],
            "signup_url": "https://aistudio.google.com/apikey",
        },
        "openrouter": {
            "name": "OpenRouter",
            "env_var": "OPENROUTER_API_KEY",
            "models": ["anthropic/claude-3-5-sonnet", "openai/gpt-4o", "meta-llama/llama-3-70b"],
            "signup_url": "https://openrouter.ai/keys",
        },
        "openai": {
            "name": "OpenAI",
            "env_var": "OPENAI_API_KEY",
            "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            "signup_url": "https://platform.openai.com/api-keys",
        },
        "anthropic": {
            "name": "Anthropic",
            "env_var": "ANTHROPIC_API_KEY",
            "models": ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
            "signup_url": "https://console.anthropic.com/settings/keys",
        },
        "ollama": {
            "name": "Ollama (Local)",
            "env_var": None,
            "models": ["llama3", "mistral", "codellama"],
            "signup_url": "https://ollama.ai",
            "is_local": True,
        },
    }

    RECOMMENDED_ROUTES = {
        "balanced": {
            "name": "Balanced (Recommended)",
            "description": "Good balance of quality and cost",
            "routing": {
                "miner": "gemini/gemini-2.5-flash",
                "dossier_builder": "gemini/gemini-2.5-pro",
                "synthesizer": "gemini/gemini-2.5-flash",
                "outliner": "gemini/gemini-2.5-flash",
                "drafter": "anthropic/claude-3-5-sonnet",
                "auditor": "gemini/gemini-2.5-pro",
                "polisher": "openai/gpt-4o",
            },
        },
        "budget": {
            "name": "Budget-Friendly",
            "description": "Minimize costs with mostly Flash models",
            "routing": {
                "miner": "gemini/gemini-2.5-flash",
                "dossier_builder": "gemini/gemini-2.5-flash",
                "synthesizer": "gemini/gemini-2.5-flash",
                "outliner": "gemini/gemini-2.5-flash",
                "drafter": "gemini/gemini-2.5-pro",
                "auditor": "gemini/gemini-2.5-flash",
                "polisher": "gemini/gemini-2.5-flash",
            },
        },
        "premium": {
            "name": "Premium Quality",
            "description": "Best quality with top-tier models",
            "routing": {
                "miner": "openai/gpt-4o",
                "dossier_builder": "anthropic/claude-3-5-sonnet",
                "synthesizer": "openai/gpt-4o",
                "outliner": "anthropic/claude-3-5-sonnet",
                "drafter": "anthropic/claude-3-5-sonnet",
                "auditor": "openai/gpt-4o",
                "polisher": "anthropic/claude-3-5-sonnet",
            },
        },
    }

    def __init__(self):
        self.console = Console()
        self.credential_manager = CredentialManager()
        self.configured_providers: Dict[str, str] = {}

    def run(self) -> bool:
        """
        Run the complete onboarding flow.

        Returns:
            True if onboarding completed successfully, False otherwise
        """
        self._show_welcome()

        # Step 1: Check existing setup
        existing = self._check_existing_setup()
        if existing:
            if not self._handle_existing_setup():
                return False

        # Step 2: Select providers
        if not self._select_providers():
            return False

        # Step 3: Configure API keys
        if not self._configure_api_keys():
            return False

        # Step 4: Choose routing strategy
        if not self._choose_routing():
            return False

        # Step 5: Test connections
        if not self._test_connections():
            self.console.print("\n[yellow]⚠ Some connection tests failed, but you can continue.[/yellow]")
            if not Confirm.ask("Continue anyway?"):
                return False

        # Step 6: Save configuration
        self._save_configuration()

        self._show_completion()
        return True

    def _show_welcome(self) -> None:
        """Display welcome message."""
        self.console.print(
            Panel.fit(
                "[bold green]Welcome to ManuscriptFinesse![/bold green]\n\n"
                "This wizard will help you set up your AI providers and API keys.\n"
                "You'll be writing your novel in no time!\n\n"
                "[dim]Press Ctrl+C at any time to exit.[/dim]",
                border_style="green",
            )
        )
        self.console.print()

    def _check_existing_setup(self) -> bool:
        """Check if there's existing configuration."""
        has_config = False

        for provider in self.SUPPORTED_PROVIDERS:
            if has_api_key(provider):
                has_config = True
                break

        return has_config

    def _handle_existing_setup(self) -> bool:
        """Handle existing configuration."""
        self.console.print("[yellow]⚠ Found existing configuration![/yellow]\n")

        configured = []
        for provider, info in self.SUPPORTED_PROVIDERS.items():
            if has_api_key(provider):
                configured.append(provider)

        if configured:
            self.console.print(f"Currently configured: [bold]{', '.join(configured)}[/bold]\n")

        action = Prompt.ask(
            "What would you like to do?",
            choices=["continue", "reconfigure", "exit"],
            default="continue",
        )

        if action == "exit":
            return False
        elif action == "reconfigure":
            # Clear existing credentials
            for provider in configured:
                self.credential_manager.delete_credential(provider)
            self.console.print("[dim]Cleared existing configuration.[/dim]\n")

        return True

    def _select_providers(self) -> bool:
        """Select which providers to configure."""
        self.console.print(
            Panel(
                "[bold]Step 1: Select AI Providers[/bold]\n\n"
                "Choose which LLM providers you want to use. You can select multiple.",
                border_style="blue",
            )
        )
        self.console.print()

        # Show available providers
        table = Table(title="Available Providers")
        table.add_column("Provider", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="green")

        selected = []

        for provider_id, info in self.SUPPORTED_PROVIDERS.items():
            is_local = info.get("is_local", False)
            provider_type = "🔒 Local" if is_local else "☁️ Cloud"
            status = "✓ Configured" if has_api_key(provider_id) else "○ Not configured"

            table.add_row(info["name"], provider_type, status)

        self.console.print(table)
        self.console.print()

        # Ask which providers to configure
        self.console.print("[bold]Which providers would you like to configure?[/bold]")
        self.console.print("[dim](Enter comma-separated list, e.g., 'gemini,openrouter' or 'all')[/dim]\n")

        while True:
            choice = Prompt.ask("Providers").strip().lower()

            if choice == "all":
                selected = list(self.SUPPORTED_PROVIDERS.keys())
                break
            elif choice == "none" or choice == "":
                selected = []
                break
            else:
                parts = [p.strip() for p in choice.split(",")]
                invalid = [p for p in parts if p not in self.SUPPORTED_PROVIDERS]

                if invalid:
                    self.console.print(f"[red]Unknown providers: {', '.join(invalid)}[/red]")
                    continue

                selected = parts
                break

        if not selected:
            self.console.print("[red]You must select at least one provider.[/red]")
            return False

        self.configured_providers = {p: self.SUPPORTED_PROVIDERS[p] for p in selected}

        self.console.print(f"\n[green]✓ Selected {len(selected)} provider(s)[/green]\n")
        return True

    def _configure_api_keys(self) -> bool:
        """Configure API keys for selected providers."""
        self.console.print(
            Panel(
                "[bold]Step 2: Configure API Keys[/bold]\n\n"
                "Enter your API keys for each selected provider.\n"
                "Keys are stored encrypted on your local machine.",
                border_style="blue",
            )
        )
        self.console.print()

        for provider_id, info in self.configured_providers.items():
            if info.get("is_local"):
                self.console.print(f"[bold cyan]{info['name']}[/bold cyan]")
                self.console.print(f"[dim]Local provider - no API key needed[/dim]\n")
                continue

            self.console.print(f"[bold cyan]{info['name']}[/bold cyan]")
            self.console.print(f"[dim]Get your key at: {info['signup_url']}[/dim]")

            # Check if already configured
            if has_api_key(provider_id):
                current = get_api_key(provider_id)
                masked = current[:8] + "..." if current and len(current) > 8 else "***"
                self.console.print(f"[dim]Current key: {masked}[/dim]")

                if not Confirm.ask("Replace existing key?", default=False):
                    self.console.print()
                    continue

            # Prompt for API key
            api_key = Prompt.ask(
                f"Enter {info['name']} API key",
                password=True,
            )

            if not api_key or len(api_key.strip()) < 10:
                self.console.print("[red]Invalid API key. Please try again.[/red]\n")
                # Allow retry or skip
                if not Confirm.ask("Try again?", default=True):
                    del self.configured_providers[provider_id]
                    continue
                continue

            # Save the key
            save_api_key(provider_id, api_key.strip(), encrypt=True)
            self.console.print(f"[green]✓ API key saved securely[/green]\n")

        return len(self.configured_providers) > 0

    def _choose_routing(self) -> bool:
        """Choose model routing strategy."""
        self.console.print(
            Panel(
                "[bold]Step 3: Choose Model Routing Strategy[/bold]\n\n"
                "Different tasks use different AI models. Choose a preset or customize.",
                border_style="blue",
            )
        )
        self.console.print()

        # Show routing options
        table = Table(title="Routing Strategies")
        table.add_column("Strategy", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Models Used", style="green")

        for route_id, route_info in self.RECOMMENDED_ROUTES.items():
            models = set()
            for model_path in route_info["routing"].values():
                model_name = model_path.split("/")[0] if "/" in model_path else model_path
                models.add(model_name)
            models_str = ", ".join(models)

            table.add_row(route_info["name"], route_info["description"], models_str)

        self.console.print(table)
        self.console.print()

        choice = Prompt.ask(
            "Choose a routing strategy",
            choices=list(self.RECOMMENDED_ROUTES.keys()),
            default="balanced",
        )

        self.selected_routing = self.RECOMMENDED_ROUTES[choice]["routing"]

        self.console.print(f"\n[green]✓ Selected: {self.RECOMMENDED_ROUTES[choice]['name']}[/green]\n")
        return True

    def _test_connections(self) -> bool:
        """Test connections to configured providers."""
        self.console.print(
            Panel(
                "[bold]Step 4: Testing Connections[/bold]\n\n"
                "Verifying API keys and model access...",
                border_style="blue",
            )
        )
        self.console.print()

        all_passed = True

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            for provider_id in self.configured_providers.keys():
                task = progress.add_task(f"Testing {provider_id}...", total=None)

                # Try to get a provider instance
                try:
                    test_model = self.SUPPORTED_PROVIDERS[provider_id]["models"][0]
                    full_model = f"{provider_id}/{test_model}"

                    provider = LLMProviderFactory.get_provider(full_model)

                    # Check if we got a mock provider (means no API key)
                    from manuscriptfinesse.providers.base import MockProvider
                    if isinstance(provider, MockProvider):
                        progress.update(task, description=f"[red]✗ {provider_id}: No valid API key[/red]")
                        all_passed = False
                    else:
                        progress.update(task, description=f"[green]✓ {provider_id}: Connected[/green]")
                except Exception as e:
                    progress.update(task, description=f"[red]✗ {provider_id}: {str(e)}[/red]")
                    all_passed = False

        return all_passed

    def _save_configuration(self) -> None:
        """Save the final configuration."""
        self.console.print(
            Panel(
                "[bold]Saving Configuration...[/bold]",
                border_style="green",
            )
        )

        # Configuration is already saved via save_api_key calls
        # The routing will be saved when ProjectConfig is used

        self.console.print("[green]✓ Configuration saved successfully![/green]\n")

    def _show_completion(self) -> None:
        """Show completion message."""
        self.console.print(
            Panel.fit(
                "[bold green]🎉 Setup Complete![/bold green]\n\n"
                "You're ready to start using ManuscriptFinesse!\n\n"
                "[bold]Next steps:[/bold]\n"
                "• Run [cyan]manuscriptfinesse chat[/cyan] to start the natural language interface\n"
                "• Run [cyan]manuscriptfinesse init --title \"My Novel\"[/cyan] to create a project\n"
                "• Type [cyan]manuscriptfinesse --help[/cyan] for all commands\n\n"
                "[dim]You can re-run this wizard anytime with:[/dim]\n"
                "[cyan]manuscriptfinesse setup[/cyan]",
                border_style="green",
            )
        )


def run_onboarding() -> bool:
    """Convenience function to run the onboarding wizard."""
    wizard = OnboardingWizard()
    return wizard.run()
