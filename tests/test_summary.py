"""Test summary generation against expected content."""
import re
from typing import List, Dict

class SummaryValidator:
    def __init__(self):
        # Define expected categories and their key points
        self.expected_categories = {
            "ErgoHack": [
                {"project": "OnErgo", "keywords": ["educational platform", "DeFi", "event calendar"]},
                {"project": "3D Explorer", "keywords": ["ergo-3d-explorer.vercel.app"]},
                {"project": "Minotaur", "keywords": ["implementation", "testing", "video"]},
                {"project": "Miner Rights Protocol", "keywords": ["whitepaper", "github"]},
                {"project": "Last Byte Bar", "keywords": ["Token Flight", "prototype"]},
                {"project": "Satergo", "keywords": ["Offline Vault", "per-wallet passwords", "multi-wallet"]}
            ],
            "DeFi/Infrastructure": [
                {"project": "Rosen Bridge", "keywords": ["P2P", "transaction signing", "24 hours"]},
                {"project": "DuckPools", "keywords": ["withdrawal", "Vanadium", "JIT"]},
                {"project": "Gluon", "keywords": ["150% reserve ratio", "Djed", "SigmaUSD"]},
                {"project": "Bober YF", "keywords": ["ErgoDEX", "whitelist", "Farm ID"]},
                {"project": "RocksDB", "keywords": ["HDD", "SSD", "performance"]},
                {"project": "DexYUSD", "keywords": ["code changes", "testing"]},
                {"project": "CyberVerse", "keywords": ["partnership"]}
            ],
            "Documentation": [
                {"project": "Ergo One Stop Shop", "keywords": ["Medium", "Google Doc", "ErgoMinnow"]}
            ],
            "Infrastructure": [
                {"project": "Vanadium", "keywords": ["JIT", "Javascript", "permission"]}
            ]
        }

        # Define expected emoji variety
        self.emoji_categories = {
            "development": ["🔧", "⚙️", "🛠️", "🔨"],
            "launch": ["🚀", "🌟", "✨"],
            "documentation": ["📚", "📝", "📖"],
            "infrastructure": ["🏗️", "🔌", "🌐"],
            "defi": ["💰", "💱", "🏦"],
            "testing": ["🧪", "🔍", "✅"],
            "community": ["👥", "🤝", "💬"]
        }

    def validate_bullet(self, bullet: str) -> Dict[str, List[str]]:
        """Validate a single bullet point."""
        issues = {
            "missing_emoji": [],
            "missing_project": [],
            "missing_link": [],
            "missing_keywords": [],
            "emoji_variety": []
        }

        # Check emoji
        if not re.search(r'^- [^\w\s]', bullet):
            issues["missing_emoji"].append("Bullet missing emoji")
        else:
            emoji = re.search(r'^- ([^\w\s])', bullet).group(1)
            if emoji in self._get_used_emojis():
                issues["emoji_variety"].append(f"Emoji {emoji} already used")

        # Check project name
        if not re.search(r'\*\*([^*]+)\*\*', bullet):
            issues["missing_project"].append("Missing project name in bold")

        # Check Discord link
        if not re.search(r'\[([^\]]+)\]\(https://discord\.com/channels/[^)]+\)', bullet):
            issues["missing_link"].append("Missing Discord link")

        # Check content against expected categories
        project_match = re.search(r'\*\*([^*]+)\*\*', bullet)
        if project_match:
            project_name = project_match.group(1).strip()
            found_category = False
            for category, points in self.expected_categories.items():
                for point in points:
                    if point["project"] in project_name:
                        found_category = True
                        # Check for expected keywords
                        missing_keywords = []
                        for keyword in point["keywords"]:
                            if keyword.lower() not in bullet.lower():
                                missing_keywords.append(keyword)
                        if missing_keywords:
                            issues["missing_keywords"].append(
                                f"Missing keywords for {project_name}: {', '.join(missing_keywords)}"
                            )
                        break
                if found_category:
                    break

        return issues

    def validate_summary(self, bullets: List[str]) -> Dict[str, List[str]]:
        """Validate the entire summary."""
        all_issues = {
            "missing_categories": [],
            "bullet_issues": {},
            "overall_issues": []
        }

        # Check for missing categories
        covered_projects = set()
        for bullet in bullets:
            project_match = re.search(r'\*\*([^*]+)\*\*', bullet)
            if project_match:
                covered_projects.add(project_match.group(1).strip())

        # Find missing projects from expected categories
        for category, points in self.expected_categories.items():
            for point in points:
                if not any(point["project"] in proj for proj in covered_projects):
                    all_issues["missing_categories"].append(
                        f"Missing coverage for {point['project']} in {category}"
                    )

        # Validate each bullet
        for i, bullet in enumerate(bullets):
            issues = self.validate_bullet(bullet)
            if any(issues.values()):
                all_issues["bullet_issues"][f"Bullet {i+1}"] = issues

        # Check overall summary structure
        if len(bullets) < 5:
            all_issues["overall_issues"].append("Summary seems too short")

        return all_issues

    def _get_used_emojis(self) -> set:
        """Track used emojis to ensure variety."""
        return set()

    def suggest_improvements(self, issues: Dict[str, List[str]]) -> List[str]:
        """Generate improvement suggestions based on validation issues."""
        suggestions = []

        if issues["missing_categories"]:
            suggestions.append(
                "Prompt Improvement: Add explicit category requirements to ensure coverage of all key projects"
            )

        if any("missing_emoji" in b for b in issues.get("bullet_issues", {}).values()):
            suggestions.append(
                "Prompt Improvement: Emphasize emoji requirement and provide category-specific emoji suggestions"
            )

        if any("emoji_variety" in b for b in issues.get("bullet_issues", {}).values()):
            suggestions.append(
                "Code Improvement: Implement emoji tracking to ensure variety across bullets"
            )

        if any("missing_keywords" in b for b in issues.get("bullet_issues", {}).values()):
            suggestions.append(
                "Prompt Improvement: Add specific keyword requirements for each project category"
            )

        return suggestions
