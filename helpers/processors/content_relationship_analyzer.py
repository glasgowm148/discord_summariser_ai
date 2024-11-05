"""Analyze relationships between content pieces."""
import re
from typing import Dict, List, Set, Tuple
from collections import Counter

class ContentRelationshipAnalyzer:
    """Analyzes relationships and similarities between content pieces."""
    
    @staticmethod
    def find_related_content(items: List[str], context_window: int = 5) -> Dict[str, List[str]]:
        """
        Find groups of related content with enhanced context awareness.
        
        Args:
            items: List of content items
            context_window: Number of surrounding items to consider for context
        
        Returns:
            Dictionary of related content groups
        """
        # First, filter out unimportant content
        filtered_items = ContentRelationshipAnalyzer._filter_unimportant_content(items)
        
        related_groups: Dict[str, List[str]] = {}
        processed_indices: Set[int] = set()

        # Analyze overall discussion patterns
        discussion_stats = ContentRelationshipAnalyzer._analyze_discussion_patterns(filtered_items)
        
        for i, item in enumerate(filtered_items):
            if i in processed_indices:
                continue

            # Dynamic similarity threshold based on discussion intensity
            similarity_threshold = ContentRelationshipAnalyzer._calculate_dynamic_threshold(
                item, discussion_stats
            )
            
            # Extract main content without formatting
            main_content = ContentRelationshipAnalyzer._extract_plain_content(item)
            
            # Find related items within context window
            related = []
            context_range = range(max(0, i - context_window), min(len(filtered_items), i + context_window + 1))
            
            for j in context_range:
                if j != i and j not in processed_indices:
                    other_item = filtered_items[j]
                    other_content = ContentRelationshipAnalyzer._extract_plain_content(other_item)
                    
                    similarity = ContentRelationshipAnalyzer._calculate_advanced_similarity(
                        main_content, other_content, discussion_stats
                    )
                    
                    if similarity > similarity_threshold:
                        related.append(other_item)
                        processed_indices.add(j)

            if related:
                processed_indices.add(i)
                key_topic = ContentRelationshipAnalyzer._extract_advanced_topic(item, discussion_stats)
                
                if key_topic in related_groups:
                    related_groups[key_topic].extend([item] + related)
                else:
                    related_groups[key_topic] = [item] + related

        return related_groups

    @staticmethod
    def _filter_unimportant_content(items: List[str]) -> List[str]:
        """
        Filter out unimportant, low-information content while preserving useful insights.
        
        Args:
            items: List of content items
        
        Returns:
            Filtered list of content items
        """
        def is_important_content(item: str) -> bool:
            # Remove markdown formatting for analysis
            clean_item = re.sub(r'\*\*[^*]+\*\*:', '', item.lower())
            clean_item = re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', clean_item)
            
            # Useful content indicators
            useful_keywords = [
                # Technical guidance
                'tip', 'advice', 'recommended', 'solution', 'guide', 'how to',
                
                # User experience
                'wallet', 'transaction', 'nft', 'connectivity', 'visibility',
                
                # Positive actions
                'improve', 'help', 'support', 'resolve', 'fix', 'optimize',
                
                # Community insights
                'sponsor', 'collaboration', 'initiative', 'opportunity'
            ]
            
            # Prioritize content with useful keywords
            if any(keyword in clean_item for keyword in useful_keywords):
                return True
            
            # Basic information threshold with lower bar
            return len(clean_item.split()) > 5

        return [item for item in items if is_important_content(item)]

    @staticmethod
    def _analyze_discussion_patterns(items: List[str]) -> Dict[str, float]:
        """
        Analyze discussion patterns to understand context and importance.
        
        Returns:
            Dictionary with statistics about discussion topics
        """
        # Extract topics and their frequencies
        topics = [ContentRelationshipAnalyzer._extract_key_topic(item) for item in items]
        topic_counts = Counter(topics)
        total_items = len(items)
        
        # Calculate topic significance
        topic_stats = {
            topic: count / total_items for topic, count in topic_counts.items()
        }
        
        # Identify technical keywords
        technical_keywords = ContentRelationshipAnalyzer._extract_technical_keywords(items)
        
        # Enhance topic stats with technical keyword presence
        for topic in topic_stats:
            keyword_boost = sum(
                1 for keyword in technical_keywords 
                if keyword.lower() in topic.lower()
            )
            topic_stats[topic] *= (1 + 0.2 * keyword_boost)
        
        return topic_stats

    @staticmethod
    def _calculate_dynamic_threshold(item: str, discussion_stats: Dict[str, float]) -> float:
        """
        Calculate a dynamic similarity threshold based on discussion context.
        
        Args:
            item: Content item
            discussion_stats: Statistics about discussion topics
        
        Returns:
            Dynamic similarity threshold
        """
        topic = ContentRelationshipAnalyzer._extract_key_topic(item)
        base_threshold = 0.3
        
        # Adjust threshold based on topic significance
        topic_significance = discussion_stats.get(topic, 0.5)
        return base_threshold * (1 + topic_significance)

    @staticmethod
    def _calculate_advanced_similarity(
        content1: str, 
        content2: str, 
        discussion_stats: Dict[str, float]
    ) -> float:
        """
        Calculate advanced similarity with context-aware weighting.
        
        Args:
            content1: First content piece
            content2: Second content piece
            discussion_stats: Statistics about discussion topics
        
        Returns:
            Similarity score
        """
        # Basic word-based similarity
        words1 = set(re.findall(r'\b\w+\b', content1.lower()))
        words2 = set(re.findall(r'\b\w+\b', content2.lower()))
        
        common_words = words1.intersection(words2)
        total_words = len(words1.union(words2))
        
        if total_words == 0:
            return 0.0
        
        base_similarity = len(common_words) / total_words
        
        # Technical keyword boost
        technical_keywords = {
            'mining', 'blockchain', 'protocol', 'network', 'performance', 
            'optimization', 'strategy', 'development', 'infrastructure'
        }
        technical_word_boost = len(common_words.intersection(technical_keywords)) * 0.2
        
        return base_similarity + technical_word_boost

    @staticmethod
    def _extract_advanced_topic(item: str, discussion_stats: Dict[str, float]) -> str:
        """
        Extract an advanced topic with context awareness.
        
        Args:
            item: Content item
            discussion_stats: Statistics about discussion topics
        
        Returns:
            Key topic
        """
        # Try project name first
        project_match = re.search(r'\*\*([^*]+)\*\*', item)
        if project_match:
            return project_match.group(1)
        
        # Extract key words
        content = re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', item.lower())
        words = re.findall(r'\b\w+\b', content)
        
        # Prioritize words based on discussion stats
        for word in words:
            if word in discussion_stats:
                return word
        
        return words[1] if len(words) > 1 else words[0] if words else "general"

    @staticmethod
    def _extract_technical_keywords(items: List[str]) -> Set[str]:
        """
        Extract technical keywords from discussion items.
        
        Args:
            items: List of content items
        
        Returns:
            Set of technical keywords
        """
        technical_keywords = {
            'mining', 'blockchain', 'protocol', 'network', 'performance', 
            'optimization', 'strategy', 'development', 'infrastructure',
            'wallet', 'transaction', 'smart contract', 'consensus', 'node'
        }
        
        found_keywords = set()
        for item in items:
            item_lower = item.lower()
            found_keywords.update(
                keyword for keyword in technical_keywords 
                if keyword in item_lower
            )
        
        return found_keywords

    @staticmethod
    def _extract_plain_content(text: str) -> str:
        """Extract plain content without formatting."""
        # Remove project name formatting
        text = re.sub(r'\*\*[^*]+\*\*:', '', text.lower())
        # Remove markdown links
        text = re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', text)
        return text.strip()

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
