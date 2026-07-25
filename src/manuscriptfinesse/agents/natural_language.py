"""
Natural Language Interface Agent for ManuscriptFinesse

This module provides an AI-powered interface that allows users to interact
with the ManuscriptFinesse CLI using natural language instead of memorizing
terminal commands.
"""

import json
import re
from typing import Optional, Dict, Any, List, Tuple

from rich.console import Console

from manuscriptfinesse.providers.factory import LLMProviderFactory
from manuscriptfinesse.core.project import ProjectManager
from manuscriptfinesse.core.config import ProjectConfig


class NaturalLanguageAgent:
    """
    An agent that interprets natural language requests and maps them to
    ManuscriptFinesse CLI commands.
    """

    def __init__(self, config: Optional[ProjectConfig] = None):
        self.console = Console()
        self.pm = ProjectManager()
        self.config = config or self._load_config()
        self.provider = LLMProviderFactory.get_provider_for_role(
            "miner",  # Using miner as general-purpose LLM for now
            self.config.role_routing if self.config else {}
        )

        # Command patterns and their mappings
        self.command_patterns = {
            'init': {
                'keywords': ['start', 'create', 'initialize', 'init', 'new project', 'begin', 'setup'],
                'description': 'Initialize a new manuscript project',
                'required_params': [],
                'optional_params': ['title', 'genre', 'target_words']
            },
            'ingest': {
                'keywords': ['ingest', 'analyze', 'process', 'read', 'import', 'load notes', 'source material'],
                'description': 'Ingest raw notes or source material',
                'required_params': ['file_path_or_text'],
                'optional_params': []
            },
            'dossiers': {
                'keywords': ['dossier', 'character', 'location', 'faction', 'world building', 'bible'],
                'description': 'Build character, location, or faction dossiers',
                'required_params': [],
                'optional_params': ['character', 'location', 'faction']
            },
            'bible': {
                'keywords': ['story bible', 'bible.json', 'synthesize bible', 'master bible'],
                'description': 'Synthesize the master story bible',
                'required_params': [],
                'optional_params': []
            },
            'outline': {
                'keywords': ['outline', 'chapter matrix', 'plan', 'structure', 'plot'],
                'description': 'Generate chapter outline and beat allocations',
                'required_params': [],
                'optional_params': ['words', 'chapters']
            },
            'draft': {
                'keywords': ['draft', 'write', 'generate chapter', 'create chapter'],
                'description': 'Draft manuscript chapters',
                'required_params': [],
                'optional_params': ['chapter']
            },
            'polish': {
                'keywords': ['polish', 'edit', 'refine', 'enhance', 'line edit'],
                'description': 'Polish and enhance drafted chapters',
                'required_params': [],
                'optional_params': ['chapter']
            },
            'export': {
                'keywords': ['export', 'publish', 'epub', 'docx', 'markdown', 'download'],
                'description': 'Export manuscript to publishing formats',
                'required_params': [],
                'optional_params': ['format']
            }
        }

    def _load_config(self) -> Optional[ProjectConfig]:
        """Load project configuration if available."""
        try:
            return self.pm.load_config()
        except Exception:
            return None

    def interpret_request(self, user_input: str) -> Dict[str, Any]:
        """
        Interpret a natural language request and return the corresponding
        command and parameters.

        Args:
            user_input: The user's natural language input

        Returns:
            Dictionary containing 'command', 'params', and 'confidence'
        """
        user_input_lower = user_input.lower().strip()

        # Try to match against known command patterns
        best_match = None
        best_score = 0

        for cmd_name, pattern_info in self.command_patterns.items():
            score = 0
            matched_keywords = []

            for keyword in pattern_info['keywords']:
                if keyword in user_input_lower:
                    score += len(keyword)  # Longer keywords get higher weight
                    matched_keywords.append(keyword)

            if score > best_score:
                best_score = score
                best_match = {
                    'command': cmd_name,
                    'matched_keywords': matched_keywords,
                    'score': score
                }

        # If no pattern match, use LLM to interpret
        if best_score < 5 and self.provider:
            return self._llm_interpret(user_input)

        # Extract parameters from the input
        params = self._extract_parameters(user_input, best_match['command'] if best_match else '')

        return {
            'command': best_match['command'] if best_match else 'unknown',
            'params': params,
            'confidence': min(best_score / 20.0, 1.0) if best_match else 0.0,
            'matched_keywords': best_match.get('matched_keywords', []) if best_match else []
        }

    def _llm_interpret(self, user_input: str) -> Dict[str, Any]:
        """Use LLM to interpret ambiguous requests."""
        prompt = f"""You are a command interpreter for ManuscriptFinesse, a 6-stage AI novel generation tool.

Available commands:
- init: Initialize a new project (parameters: title, genre, target_words)
- ingest: Process raw notes/source material (parameters: file_path_or_text)
- dossiers: Create character/location/faction dossiers (parameters: character, location, faction)
- bible: Synthesize story bible from dossiers
- outline: Generate chapter outline (parameters: words, chapters)
- draft: Write manuscript chapters (parameters: chapter)
- polish: Edit and refine chapters (parameters: chapter)
- export: Export to publishing formats (parameters: format: epub/docx/markdown)

User request: "{user_input}"

Respond ONLY with a JSON object in this exact format:
{{
    "command": "<command_name>",
    "params": {{
        "param_name": "param_value"
    }},
    "explanation": "Brief explanation of what you understood"
}}

If the request is unclear or doesn't match any command, set command to "clarify" and ask for more information in the explanation."""

        try:
            response = self.provider.complete(prompt)
            # Parse the JSON response
            # Extract JSON from response (in case it has markdown formatting)
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'command': result.get('command', 'unknown'),
                    'params': result.get('params', {}),
                    'confidence': 0.8 if result.get('command') != 'clarify' else 0.3,
                    'explanation': result.get('explanation', '')
                }
        except Exception as e:
            self.console.print(f"[dim]LLM interpretation failed: {e}[/dim]")

        return {
            'command': 'clarify',
            'params': {},
            'confidence': 0.0,
            'explanation': "I'm not sure what you'd like to do. Could you be more specific?"
        }

    def _extract_parameters(self, user_input: str, command: str) -> Dict[str, Any]:
        """Extract parameters from user input based on command type."""
        params = {}
        user_input_lower = user_input.lower()

        # Extract numbers (for word count, chapter count, etc.)
        numbers = re.findall(r'\b(\d+)\b', user_input)

        if command == 'init':
            # Extract title (look for quoted text or after "called"/"named")
            title_match = re.search(r'["\']([^"\']+)["\']', user_input)
            if title_match:
                params['title'] = title_match.group(1)
            else:
                title_match = re.search(r'(?:called|named|titled)\s+([^\s,]+(?:\s+[^\s,]+)*)', user_input_lower)
                if title_match:
                    params['title'] = title_match.group(1).title()

            # Extract genre
            genre_keywords = ['fantasy', 'sci-fi', 'science fiction', 'romance', 'mystery',
                            'thriller', 'horror', 'historical', 'contemporary', 'young adult']
            for genre in genre_keywords:
                if genre in user_input_lower:
                    params['genre'] = genre.title()
                    break

            # Extract word count
            if numbers:
                # Look for numbers near "words" or "word count"
                if 'word' in user_input_lower:
                    params['target_words'] = int(numbers[0])

        elif command == 'ingest':
            # Extract file path or use the rest as text
            path_match = re.search(r'(/[^\s]+|\w+\.\w+)', user_input)
            if path_match:
                params['file_path_or_text'] = path_match.group(1)
            else:
                # Use everything after command keywords as text
                params['file_path_or_text'] = user_input

        elif command == 'dossiers':
            # Check for specific entity types
            if any(word in user_input_lower for word in ['character', 'protagonist', 'antagonist', 'person']):
                char_match = re.search(r'(?:character|named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', user_input)
                if char_match:
                    params['character'] = char_match.group(1)
            elif any(word in user_input_lower for word in ['location', 'place', 'setting', 'city', 'world']):
                loc_match = re.search(r'(?:location|place|named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', user_input)
                if loc_match:
                    params['location'] = loc_match.group(1)
            elif any(word in user_input_lower for word in ['faction', 'group', 'organization', 'guild']):
                fac_match = re.search(r'(?:faction|group|named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', user_input)
                if fac_match:
                    params['faction'] = fac_match.group(1)

        elif command == 'outline':
            # Extract word count and chapter count
            if len(numbers) >= 2:
                params['words'] = int(numbers[0])
                params['chapters'] = int(numbers[1])
            elif len(numbers) == 1:
                if 'chapter' in user_input_lower:
                    params['chapters'] = int(numbers[0])
                else:
                    params['words'] = int(numbers[0])

        elif command == 'draft' or command == 'polish':
            # Extract chapter number
            chapter_match = re.search(r'chapter\s*(\d+)', user_input_lower)
            if chapter_match:
                params['chapter'] = int(chapter_match.group(1))
            elif numbers:
                params['chapter'] = int(numbers[0])

        elif command == 'export':
            # Extract format
            if 'epub' in user_input_lower:
                params['format'] = 'epub'
            elif 'docx' in user_input_lower or 'word' in user_input_lower:
                params['format'] = 'docx'
            elif 'markdown' in user_input_lower or 'md' in user_input_lower:
                params['format'] = 'markdown'

        return params

    def execute_command(self, command: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Execute a CLI command with the given parameters.

        Args:
            command: The command name to execute
            params: Dictionary of command parameters

        Returns:
            Tuple of (success: bool, message: str)
        """
        from typer.testing import CliRunner
        from manuscriptfinesse.cli.main import app

        runner = CliRunner()

        # Build command arguments
        args = [command]
        for key, value in params.items():
            args.append(f"--{key.replace('_', '-')}")
            args.append(str(value))

        try:
            result = runner.invoke(app, args)
            if result.exit_code == 0:
                return True, result.output
            else:
                return False, f"Command failed: {result.output}"
        except Exception as e:
            return False, f"Error executing command: {str(e)}"

    def process_request(self, user_input: str) -> str:
        """
        Process a natural language request from start to finish.

        Args:
            user_input: The user's natural language input

        Returns:
            Response message to display to the user
        """
        # Interpret the request
        interpretation = self.interpret_request(user_input)

        command = interpretation['command']
        params = interpretation['params']
        confidence = interpretation['confidence']

        # Handle low confidence or clarification requests
        if confidence < 0.3 or command == 'clarify':
            return self._get_clarification_response(user_input, interpretation)

        # Confirm the action with the user
        self.console.print(f"\n[bold cyan]Understanding:[/bold cyan] You want to {command}", end="")
        if params:
            param_str = ", ".join(f"{k}={v}" for k, v in params.items())
            self.console.print(f" ({param_str})", end="")
        self.console.print("")

        # Execute the command
        success, message = self.execute_command(command, params)

        if success:
            return f"[bold green]✓ Success![/bold green]\n{message}"
        else:
            return f"[red]✗ Error:[/red] {message}"

    def _get_clarification_response(self, user_input: str, interpretation: Dict[str, Any]) -> str:
        """Generate a helpful clarification response."""
        responses = []

        if interpretation.get('explanation'):
            responses.append(interpretation['explanation'])

        responses.append("\n[bold cyan]Available commands:[/bold cyan]")
        for cmd_name, info in self.command_patterns.items():
            responses.append(f"  • {cmd_name}: {info['description']}")

        responses.append("\n[dim]Try being more specific, e.g.:[/dim]")
        examples = [
            '"Create a new fantasy novel called The Dragon\'s Quest"',
            '"Ingest my notes from story_ideas.txt"',
            '"Create a character dossier for John Smith"',
            '"Generate an outline with 20 chapters"',
            '"Draft chapter 5"',
            '"Export to EPUB format"'
        ]
        for ex in examples:
            responses.append(f"  {ex}")

        return "\n".join(responses)


def create_natural_language_interface():
    """Create and return a natural language interface instance."""
    return NaturalLanguageAgent()
