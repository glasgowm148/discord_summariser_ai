"""Project model for tracking Ergo ecosystem projects."""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import sqlite3
from pathlib import Path

@dataclass
class Project:
    name: str
    description: str
    category: str  # Core, dApp, Tool, Infrastructure, Community
    people_involved: List[str]
    twitter_handle: Optional[str] = None
    github_repo: Optional[str] = None
    discord_channels: List[str] = None  # List of channel IDs where project is discussed
    website: Optional[str] = None
    last_updated: datetime = None
    last_summary: Optional[str] = None  # Last summary generated for this project
    tags: List[str] = None  # Technical tags/keywords associated with the project

    @staticmethod
    def setup_database(db_path: Path) -> None:
        """Set up SQLite database for projects."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    category TEXT,
                    twitter_handle TEXT,
                    github_repo TEXT,
                    website TEXT,
                    last_updated TIMESTAMP,
                    last_summary TEXT
                )
            """)
            
            # Create people table (many-to-many relationship)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS people (
                    project_name TEXT,
                    person TEXT,
                    PRIMARY KEY (project_name, person),
                    FOREIGN KEY (project_name) REFERENCES projects(name)
                )
            """)
            
            # Create channels table (many-to-many relationship)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    project_name TEXT,
                    channel_id TEXT,
                    PRIMARY KEY (project_name, channel_id),
                    FOREIGN KEY (project_name) REFERENCES projects(name)
                )
            """)
            
            # Create tags table (many-to-many relationship)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    project_name TEXT,
                    tag TEXT,
                    PRIMARY KEY (project_name, tag),
                    FOREIGN KEY (project_name) REFERENCES projects(name)
                )
            """)
            
            # Create processed_summaries table to track what we've processed
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_summaries (
                    summary_hash TEXT PRIMARY KEY,
                    processed_at TIMESTAMP
                )
            """)
            
            conn.commit()

    @staticmethod
    def from_db(db_path: Path, name: str) -> Optional['Project']:
        """Load project from database."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get project details
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            if not row:
                return None
                
            # Get people involved
            cursor.execute("SELECT person FROM people WHERE project_name = ?", (name,))
            people = [r[0] for r in cursor.fetchall()]
            
            # Get discord channels
            cursor.execute("SELECT channel_id FROM channels WHERE project_name = ?", (name,))
            channels = [r[0] for r in cursor.fetchall()]
            
            # Get tags
            cursor.execute("SELECT tag FROM tags WHERE project_name = ?", (name,))
            tags = [r[0] for r in cursor.fetchall()]
            
            return Project(
                name=row[0],
                description=row[1],
                category=row[2],
                twitter_handle=row[3],
                github_repo=row[4],
                website=row[5],
                last_updated=datetime.fromisoformat(row[6]) if row[6] else None,
                last_summary=row[7],
                people_involved=people,
                discord_channels=channels,
                tags=tags
            )

    def save_to_db(self, db_path: Path) -> None:
        """Save project to database."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Update or insert project details
            cursor.execute("""
                INSERT OR REPLACE INTO projects 
                (name, description, category, twitter_handle, github_repo, website, last_updated, last_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.name,
                self.description,
                self.category,
                self.twitter_handle,
                self.github_repo,
                self.website,
                self.last_updated.isoformat() if self.last_updated else None,
                self.last_summary
            ))
            
            # Update people involved
            cursor.execute("DELETE FROM people WHERE project_name = ?", (self.name,))
            cursor.executemany(
                "INSERT INTO people (project_name, person) VALUES (?, ?)",
                [(self.name, person) for person in self.people_involved]
            )
            
            # Update discord channels
            cursor.execute("DELETE FROM channels WHERE project_name = ?", (self.name,))
            cursor.executemany(
                "INSERT INTO channels (project_name, channel_id) VALUES (?, ?)",
                [(self.name, channel) for channel in (self.discord_channels or [])]
            )
            
            # Update tags
            cursor.execute("DELETE FROM tags WHERE project_name = ?", (self.name,))
            cursor.executemany(
                "INSERT INTO tags (project_name, tag) VALUES (?, ?)",
                [(self.name, tag) for tag in (self.tags or [])]
            )
            
            conn.commit()

    @staticmethod
    def get_all_projects(db_path: Path) -> List['Project']:
        """Get all projects from database."""
        projects = []
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM projects")
            for (name,) in cursor.fetchall():
                project = Project.from_db(db_path, name)
                if project:
                    projects.append(project)
        return projects

    @staticmethod
    def is_summary_processed(db_path: Path, summary_hash: str) -> bool:
        """Check if a summary has already been processed."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM processed_summaries WHERE summary_hash = ?",
                (summary_hash,)
            )
            return cursor.fetchone() is not None

    @staticmethod
    def mark_summary_processed(db_path: Path, summary_hash: str) -> None:
        """Mark a summary as processed."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO processed_summaries (summary_hash, processed_at) VALUES (?, ?)",
                (summary_hash, datetime.now().isoformat())
            )
            conn.commit()
