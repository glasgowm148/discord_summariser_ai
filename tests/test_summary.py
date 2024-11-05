"""Test summary generation and suggest improvements for prompt coverage."""

import os
import re
import sys
from typing import Dict, List
from utils.prompts import SummaryPrompts
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="config/.env")
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class SummaryValidator:
    def __init__(self):
        # Define expected projects
        self.expected_projects = [
            "OnErgo",
            "3D Explorer",
            "Minotaur",
            "Miner Rights Protocol",
            "Last Byte Bar",
            "Satergo",
            "Rosen Bridge",
            "DuckPools",
            "Gluon",
            "Bober YF",
            "RocksDB",
            "DexYUSD",
            "CyberVerse",
            "Ergo One Stop Shop",
        ]

    def validate_summary(self, bullets: List[str]) -> Dict[str, List[str]]:
        """Validate the entire summary and suggest prompt improvements."""
        all_issues = {"missing_projects": [], "bullet_issues": {}, "overall_issues": []}

        # Check for missing projects
        covered_projects = set()
        for bullet in bullets:
            project_match = re.search(r"\*\*([^*]+)\*\*", bullet)
            if project_match:
                covered_projects.add(project_match.group(1).strip())

        # Find missing projects from expected projects
        for project in self.expected_projects:
            if project not in covered_projects:
                all_issues["missing_projects"].append(f"Missing coverage for {project}")

        # Suggest improvements to the prompt
        self.suggest_prompt_improvements(all_issues["missing_projects"])

        # Generate a summary using SummaryPrompts
        summary_prompt = SummaryPrompts.get_reddit_summary_prompt(
            bullets, days_covered=7
        )
        recommendations = self.get_gpt_recommendations(summary_prompt, bullets)
        print("\nGPT-4 Recommendations:")
        print(recommendations)

        # Print project names in a table with ticks and crosses
        print("\nProject Coverage Table:")
        print(f"{'Covered Projects':<30} {'Expected Projects':<30} {'Status':<10}")
        print("-" * 70)
        for project in self.expected_projects:
            covered_project = project if project in covered_projects else ""
            status = "✔️" if project in covered_projects else "❌"
            print(f"{covered_project:<30} {project:<30} {status:<10}")

        # Calculate and display coverage statistics
        total_projects = len(self.expected_projects)
        covered_count = len(covered_projects)
        success_rate = (covered_count / total_projects) * 100
        print(f"\nTotal Projects: {total_projects}")
        print(f"Covered Projects: {covered_count}")
        print(f"Success Rate: {success_rate:.2f}%")

        return all_issues

    def suggest_prompt_improvements(self, missing_projects: List[str]):
        """Suggest improvements to the prompt based on missing projects."""
        if missing_projects:
            print("\nSuggested Prompt Improvements:")
            print(
                "Consider updating the prompt to ensure coverage of the following projects:"
            )
            for project in missing_projects:
                print(f"  - {project}")

    def get_gpt_recommendations(self, prompt: str, bullets: List[str]) -> str:
        """Get recommendations from GPT-4 based on the prompt and bullets."""
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Prompt: {prompt}\nBullets: {bullets}"},
            ],
        )
        return response.choices[0].message.content.strip()


def main():
    # Create an instance of SummaryValidator
    validator = SummaryValidator()

    # Example bullet points to validate
    bullets = [
        "- **CyberVerse**: Developer [gvuldis](https://discord.com/channels/668903786361651200/1046474534473171114/1301987982739243109) shared plans for an educational platform, **OneErgo**, aimed at onboarding new users into the Ergo DeFi ecosystem through gamification and event aggregation.",
        "- **Documentation**: Developer [NeuralYogi](https://discord.com/channels/668903786361651200/840316505849987092/1301945380610506754) submitted a document linking to prototype code, showcasing ongoing development efforts.",
        "- **DuckPools**: User [__daddychill__](https://discord.com/channels/668903786361651200/1003474403683729469/1301942061691568171) reported an issue with the withdrawal function hanging during transactions and is actively seeking insights into required permissions and known issues.",
        "- **Ergo One Stop Shop**: Developer [tulo_ergominnow](https://discord.com/channels/668903786361651200/1295700255807111209/1302057441873100871) released a Medium article outlining project goals, focusing on scalability and accommodating various wallets.",
        "- **Miner Rights Protocol**: Developer [NeuralYogi](https://discord.com/channels/668903786361651200/1153460448214122526/1301947310988595296) submitted a detailed whitepaper for review during Ergo Hack 9, focusing on enhancing community involvement through a governance structure for mining rights.",
        "- **Gluon Gold**: User [Zahnentferner](https://discord.com/channels/668903786361651200/1158052036026302495/1302127363709993032) discussed the influence of leverage in Gluon Gold based on reserve ratios, particularly in the context of recent ERG price fluctuations.",
    ]

    # Validate the summary
    issues = validator.validate_summary(bullets)

    # Print the validation issues
    print("\nValidation Issues:")
    for issue_type, issue_list in issues.items():
        print(f"{issue_type}:")
        for issue in issue_list:
            print(f"  - {issue}")


if __name__ == "__main__":
    main()
