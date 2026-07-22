import os
import json
import pytest
from typer.testing import CliRunner
from manuscriptfinesse.cli.main import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "ingest" in result.output
    assert "dossiers" in result.output
    assert "bible" in result.output
    assert "outline" in result.output
    assert "draft" in result.output
    assert "polish" in result.output
    assert "export" in result.output
    assert "shell" in result.output


def test_cli_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--title", "The Cipher of Eldoria"])
    assert result.exit_code == 0
    assert "The Cipher of Eldoria" in result.output
    assert os.path.exists(".manuscriptfinesse/project.json")
    with open(".manuscriptfinesse/project.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["title"] == "The Cipher of Eldoria"


def test_cli_ingest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    result = runner.invoke(app, ["ingest", "A fantasy epic set in floating sky islands."])
    assert result.exit_code == 0
    assert "Stage 1" in result.output or "Ingest" in result.output or "ingesting" in result.output.lower()
    assert os.path.exists("project_brief.md")


def test_cli_ingest_from_file(tmp_path, monkeypatch):
    notes_file = tmp_path / "notes.txt"
    notes_file.write_text("Detailed worldbuilding notes for sci-fi novel.", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    result = runner.invoke(app, ["ingest", str(notes_file)])
    assert result.exit_code == 0
    assert os.path.exists("project_brief.md")


def test_cli_dossiers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    runner.invoke(app, ["ingest", "A fantasy epic set in floating sky islands."])
    result = runner.invoke(app, ["dossiers"])
    assert result.exit_code == 0
    assert "Stage 2" in result.output or "dossier" in result.output.lower()


def test_cli_bible(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    runner.invoke(app, ["ingest", "A fantasy epic set in floating sky islands."])
    runner.invoke(app, ["dossiers"])
    result = runner.invoke(app, ["bible"])
    assert result.exit_code == 0
    assert "Stage 3" in result.output or "bible" in result.output.lower()
    assert os.path.exists("bible.json")


def test_cli_outline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    runner.invoke(app, ["ingest", "A fantasy epic set in floating sky islands."])
    runner.invoke(app, ["bible"])
    result = runner.invoke(app, ["outline", "--words", "60000", "--chapters", "15"])
    assert result.exit_code == 0
    assert "Stage 4" in result.output or "outline" in result.output.lower()


def test_cli_draft(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    runner.invoke(app, ["ingest", "A fantasy epic set in floating sky islands."])
    runner.invoke(app, ["bible"])
    runner.invoke(app, ["outline", "--words", "60000", "--chapters", "5"])
    result = runner.invoke(app, ["draft", "--chapter", "1"])
    assert result.exit_code == 0
    assert "Stage 5" in result.output or "draft" in result.output.lower()
    assert len(os.listdir("chapters")) > 0


def test_cli_draft_all(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    runner.invoke(app, ["ingest", "A fantasy epic set in floating sky islands."])
    runner.invoke(app, ["bible"])
    runner.invoke(app, ["outline", "--words", "10000", "--chapters", "2"])
    result = runner.invoke(app, ["draft", "--chapter", "0"])
    assert result.exit_code == 0


def test_cli_polish(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    runner.invoke(app, ["ingest", "A fantasy epic set in floating sky islands."])
    runner.invoke(app, ["bible"])
    runner.invoke(app, ["outline", "--words", "10000", "--chapters", "2"])
    runner.invoke(app, ["draft", "--chapter", "1"])
    result = runner.invoke(app, ["polish", "--chapter", "1"])
    assert result.exit_code == 0
    assert "Stage 6" in result.output or "polish" in result.output.lower()


def test_cli_export(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    runner.invoke(app, ["ingest", "A fantasy epic set in floating sky islands."])
    runner.invoke(app, ["bible"])
    runner.invoke(app, ["outline", "--words", "10000", "--chapters", "2"])
    runner.invoke(app, ["draft", "--chapter", "1"])
    result = runner.invoke(app, ["export", "--format", "epub"])
    assert result.exit_code == 0
    assert "Stage 6" in result.output or "export" in result.output.lower()


def test_cli_export_all(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--title", "Test Project"])
    runner.invoke(app, ["ingest", "A fantasy epic set in floating sky islands."])
    runner.invoke(app, ["bible"])
    runner.invoke(app, ["outline", "--words", "10000", "--chapters", "2"])
    runner.invoke(app, ["draft", "--chapter", "1"])
    result = runner.invoke(app, ["export", "--format", "all"])
    assert result.exit_code == 0


def test_cli_shell(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["shell"], input="help\nexit\n")
    assert result.exit_code == 0
    assert "REPL" in result.output or "ManuscriptFinesse" in result.output or "Interactive" in result.output
