"""Service for managing project data and learning from summaries."""
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from models.project import Project
from services.base_service import BaseService
from config.settings import OUTPUT_DIR


class ProjectManager(BaseService):
    def __init__(self):
        super().__init__()
        self.db_path = Path(OUTPUT_DIR) / 'projects.db'
        self.initialize()

    def initialize(self) -> None:
        """Initialize project manager and database."""
        try:
            # Ensure output directory exists
            Path(OUTPUT_DIR).mkdir(exist_ok=True)
            # Set up database
            Project.setup_database(self.db_path)
        except Exception as e:
            self.handle_error(e, {"context": "Project manager initialization"})
            raise

    def learn_from_summary(self, summary: str) -> None:
        """Learn from a generated summary to update project information."""
        try:
            # Check if we've already processed this summary
            summary_hash = hashlib.sha256(summary.encode()).hexdigest()
            if Project.is_summary_processed(self.db_path, summary_hash):
                self.logger.info("Summary already processed, skipping")
                return

            # Extract project information from summary using multiple patterns
            patterns = [
                # Project name in bold with description
                r'\*\*([^*]+?)\*\*(?:[:\s]+([^[]+))?(?:\[([^\]]+)\]\(([^)]+)\))?',
                # Project name in section headers
                r'##\s*([^#\n]+?)\s*(?:Development|Updates?|Integration)',
                # Project name in development updates
                r'(?:developing|working on|updates? (?:to|for)|progress on)\s+(?:the\s+)?([A-Z][a-zA-Z0-9_-]+)',
                # Project name with version
                r'([A-Z][a-zA-Z0-9_-]+)\s+v?[\d\.]+',
            ]
            
            projects_updated = 0
            for pattern in patterns:
                matches = re.finditer(pattern, summary)
                for match in matches:
                    # Get project name from the first capturing group
                    project_name = match.group(1).strip()
                    
                    # Skip common false positives
                    if project_name.lower() in ['the', 'a', 'an', 'this', 'that', 'these', 'those']:
                        continue
                    
                    # Get or create project
                    project = Project.from_db(self.db_path, project_name)
                    if not project:
                        project = Project(
                            name=project_name,
                            description="",
                            category="Unknown",
                            people_involved=[],
                            discord_channels=[],
                            tags=[]
                        )
                    
                    # Try to extract description if available (from first pattern)
                    if len(match.groups()) > 1 and match.group(2):
                        description = match.group(2).strip()
                        if description:
                            project.description = description
                    
                    # Try to extract Discord channel if available (from first pattern)
                    if len(match.groups()) > 3 and match.group(4):
                        channel_id = match.group(4).split('/')[-2]
                        if channel_id not in (project.discord_channels or []):
                            if not project.discord_channels:
                                project.discord_channels = []
                            project.discord_channels.append(channel_id)
                    
                    # Extract context around the match
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(summary), match.end() + 100)
                    context = summary[context_start:context_end]
                    
                    # Extract people involved from context
                    people = re.findall(r'(?:by|from|@)\s*([A-Z][a-zA-Z0-9_-]+)', context)
                    for person in people:
                        if person not in project.people_involved:
                            project.people_involved.append(person)
                    
                    # Extract category from context
                    categories = {
                        'Core': r'(?:core|node|protocol|blockchain)',
                        'dApp': r'(?:dapp|defi|dao|dex|platform)',
                        'Tool': r'(?:tool|wallet|extension|library|sdk)',
                        'Infrastructure': r'(?:infrastructure|bridge|oracle|api)'
                    }
                    for category, pattern in categories.items():
                        if re.search(pattern, context, re.I):
                            project.category = category
                            break
                    
                    # Extract technical tags
                    tech_patterns = [
                        r'(?:using|with|in)\s+([A-Za-z]+)',
                        r'(?:implemented|developed|updated|fixed|enhanced|integrated)\s+([A-Za-z]+)',
                        r'#([A-Za-z]+)',
                        r'([A-Za-z]+)(?:\s+integration|\s+implementation|\s+development)'
                    ]
                    for pattern in tech_patterns:
                        tags = re.findall(pattern, context)
                        for tag in tags:
                            tag = tag.lower()
                            if len(tag) > 2 and tag not in (project.tags or []):  # Skip short tags
                                if not project.tags:
                                    project.tags = []
                                project.tags.append(tag)
                    
                    # Update last updated and summary
                    project.last_updated = datetime.now()
                    project.last_summary = context.strip()
                    
                    # Save project to database
                    project.save_to_db(self.db_path)
                    projects_updated += 1
            
            # Mark summary as processed
            Project.mark_summary_processed(self.db_path, summary_hash)
            if projects_updated > 0:
                self.logger.info(f"Updated {projects_updated} projects")
            
        except Exception as e:
            self.handle_error(e, {"context": "Learning from summary"})
            raise

    def get_project_context(self, project_name: str) -> Optional[str]:
        """Get context about a project for summary generation."""
        project = Project.from_db(self.db_path, project_name)
        if project:
            context = f"""Project: {project.name}
Category: {project.category}
People Involved: {', '.join(project.people_involved)}
Last Summary: {project.last_summary}
Technical Focus: {', '.join(project.tags or [])}"""
            return context
        return None

    def get_all_project_contexts(self) -> str:
        """Get context about all projects for summary generation."""
        contexts = []
        for project in Project.get_all_projects(self.db_path):
            if project.last_summary:  # Only include projects with previous summaries
                context = f"""Project: {project.name}
Category: {project.category}
People: {', '.join(project.people_involved)}
Focus: {', '.join(project.tags or [])}
Last Update: {project.last_summary}
---"""
                contexts.append(context)
        return "\n".join(contexts)
