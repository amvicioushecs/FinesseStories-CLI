import os
import json
from typing import Optional
from manuscriptfinesse.core.models import ProjectMetadata
from manuscriptfinesse.core.config import ProjectConfig

class ProjectManager:
    """Manages project workspace layout, initialization, and metadata persistence."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)
        self.meta_dir = os.path.join(self.root_dir, ".manuscriptfinesse")
        self.meta_file = os.path.join(self.meta_dir, "project.json")
        self.config_file = os.path.join(self.meta_dir, "config.yaml")

    def init_project(
        self,
        title: str = "Untitled Masterpiece",
        genre: str = "Unspecified",
        target_word_count: int = 80000,
    ) -> ProjectMetadata:
        """Initializes folder structure and saves default metadata and config."""
        os.makedirs(self.meta_dir, exist_ok=True)
        os.makedirs(os.path.join(self.root_dir, "bible", "characters"), exist_ok=True)
        os.makedirs(os.path.join(self.root_dir, "bible", "locations"), exist_ok=True)
        os.makedirs(os.path.join(self.root_dir, "bible", "factions"), exist_ok=True)
        os.makedirs(os.path.join(self.root_dir, "chapters"), exist_ok=True)

        metadata = ProjectMetadata(
            title=title,
            genre=genre,
            target_word_count=target_word_count,
        )
        self.save_metadata(metadata)

        config = ProjectConfig()
        config.save(self.config_file)

        return metadata

    def load_metadata(self) -> ProjectMetadata:
        """Loads ProjectMetadata from .manuscriptfinesse/project.json."""
        if not os.path.exists(self.meta_file):
            return ProjectMetadata()
        with open(self.meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProjectMetadata(**data)

    def save_metadata(self, metadata: ProjectMetadata) -> None:
        """Saves ProjectMetadata to .manuscriptfinesse/project.json."""
        os.makedirs(self.meta_dir, exist_ok=True)
        with open(self.meta_file, "w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=2))

    def load_config(self) -> ProjectConfig:
        """Loads ProjectConfig from .manuscriptfinesse/config.yaml."""
        return ProjectConfig.load(self.config_file)
