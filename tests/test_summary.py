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
        summary_prompt = SummaryPrompts.get_final_summary_prompt(
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
        "- 🔧 **OnErgo**: An educational platform with DeFi and event calendar features. [Join us on Discord](https://discord.com/channels/123456789)",
        "- 🚀 **Rosen Bridge**: P2P transaction signing available 24 hours. [Join us on Discord](https://discord.com/channels/987654321)",
        "- 🛠️ **Miner Rights Protocol**: Developer [NeuralYogi](https://discord.com/channels/668903786361651200/1153460448214122526/1301947310988595296) shared a link to the whitepaper for the **Miner Rights Protocol**, introducing innovative governance concepts within the mining community. Community feedback is encouraged for further refinement.",
        "- 🔧 **Cloudflare**: A developer reported issues with Cloudflare's edge servers impacting tunnel connections, but services were restored shortly after, ensuring minimal impact to the community. For more details, see the update [here](https://discord.com/channels/668903786361651200).",
        "- 🔧 **RocksDB**: Developer Paul highlighted potential issues with **RocksDB**, emphasizing the importance of resolving current dependencies with an alternative version of the library. A review of pull request #2115 is requested as part of ongoing development efforts. For more details, check the discussion [here](https://discord.com/channels/668903786361651200).",
        "- 🛠️ **Ergo One Stop Shop**: Developer [tulo_ergominnow](https://discord.com/channels/668903786361651200/1295700255807111209/1302057590473232494) confirmed the update of project documentation to Medium, aimed at improving accessibility and engagement.",
        "- 🔧 **Rosen**: Developer [Paul1938](https://discord.com/channels/668903786361651200/964131671609860126/1301937602445967371) emphasized the need for a community manager and a communication/status page to enhance user trust and improve interaction within the ecosystem.",
        "- 🔧 **Rosen Bridge**: Ongoing discussions are addressing a P2P issue affecting transaction signing, with developers actively working on a resolution as mentioned by [zargarzadehmoein](https://discord.com/channels/668903786361651200).",
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
