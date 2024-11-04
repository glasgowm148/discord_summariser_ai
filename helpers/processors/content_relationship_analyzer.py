"""Analyze relationships between content pieces."""
import re
from typing import Dict, List, Set

class ContentRelationshipAnalyzer:
    """Analyzes relationships and similarities between content pieces."""
    
    @staticmethod
    def find_related_content(items: List[str], similarity_threshold: float = 0.3) -> Dict[str, List[str]]:
        """Find groups of related content based on similarity."""
        related_groups: Dict[str, List[str]] = {}
        processed_indices: Set[int] = set()

        for i, item in enumerate(items):
            if i in processed_indices:
                continue

            # Extract main content without formatting
            main_content = ContentRelationshipAnalyzer._extract_plain_content(item)
            
            # Find related items
            related = []
            for j, other_item in enumerate(items):
                if j != i and j not in processed_indices:
                    other_content = ContentRelationshipAnalyzer._extract_plain_content(other_item)
                    
                    if ContentRelationshipAnalyzer._calculate_content_similarity(main_content, other_content) > similarity_threshold:
                        related.append(other_item)
                        processed_indices.add(j)

            if related:
                processed_indices.add(i)
                key_topic = ContentRelationshipAnalyzer._extract_key_topic(item)
                if key_topic in related_groups:
                    related_groups[key_topic].extend([item] + related)
                else:
                    related_groups[key_topic] = [item] + related

        return related_groups

    @staticmethod
    def _extract_plain_content(text: str) -> str:
        """Extract plain content without formatting."""
        # Remove project name formatting
        text = re.sub(r'\*\*[^*]+\*\*:', '', text.lower())
        # Remove markdown links
        text = re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', text)
        return text.strip()

    @staticmethod
    def _calculate_content_similarity(content1: str, content2: str) -> float:
        """Calculate similarity ratio between two content pieces."""
        # Remove common words and punctuation
        words1 = set(re.findall(r'\b\w+\b', content1.lower()))
        words2 = set(re.findall(r'\b\w+\b', content2.lower()))
        
        # Calculate similarity based on shared significant words
        common_words = words1.intersection(words2)
        total_words = len(words1.union(words2))
        
        if total_words == 0:
            return 0.0
            
        return len(common_words) / total_words

    @staticmethod
    def _extract_key_topic(text: str) -> str:
        """Extract the key topic from content."""
        # Try to get the project name first
        project_match = re.search(r'\*\*([^*]+)\*\*', text)
        if project_match:
            return project_match.group(1)
        
        # Otherwise, extract key words from the content
        content = re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', text.lower())
        words = re.findall(r'\b\w+\b', content)
        return words[1] if len(words) > 1 else words[0] if words else "general"

    @staticmethod
    def combine_related_content(items: List[str], link_separator: str = ", ") -> str:
        """Combine related content items into a single comprehensive piece."""
        if not items:
            return ""

        # Extract project name from the first item
        project_match = re.search(r'\*\*([^*]+)\*\*', items[0])
        project_name = project_match.group(1) if project_match else "General"

        # Collect all links and contents separately
        links = []
        contents = []
        for item in items:
            # Extract link
            link_match = re.search(r'\[(?:here|[^\]]+)\]\((https://[^)]+)\)', item)
            if link_match:
                links.append(link_match.group(1))
            
            # Extract content without the link part
            content = re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', item)
            content = re.sub(r'\*\*[^*]+\*\*:', '', content)
            contents.append(content.strip())

        # Combine contents and links
        combined_content = " ".join(contents)
        combined_links = link_separator.join(
            f"[discussion {i+1}]({link})" for i, link in enumerate(links)
        )
        
        return f"- **{project_name}**: {combined_content} Read more: {combined_links}"
