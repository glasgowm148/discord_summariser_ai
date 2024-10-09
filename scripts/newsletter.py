import pandas as pd
import openai
import os
import re
from dotenv import load_dotenv

# === SECTION 1: Environment Setup ===
# Load environment variables from .env file
load_dotenv()

# Set the OpenAI API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")
openai.api_key = api_key

# === SECTION 2: Data Loading and Preprocessing ===
# Load the CSV file into a DataFrame
file_path = './output/bullet_points_summary.csv'
df = pd.read_csv(file_path)

# Display the first few rows of the DataFrame
print(df.head())

# Prepare the data for summarization by extracting bullet points
messages = df['Bullet Points'].tolist()

# Function to extract URLs from a text
def extract_urls(text):
    url_pattern = re.compile(r'(https?://[^\s]+)')
    urls = url_pattern.findall(text)
    return urls

# === SECTION 3: Initial Category Suggestions from OpenAI ===
# Define the initial prompt for category suggestions
initial_prompt = (
    "Please analyze the following bullet points and suggest appropriate categories for organizing them.\n"
    f"{'; '.join(messages)}"
)

# Function to get suggested categories from OpenAI
def get_suggested_categories(initial_prompt):
    print("Getting suggested categories...")
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant tasked with analyzing discussions."},
                {"role": "user", "content": initial_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        suggested_categories = response.model_dump()["choices"][0]["message"]["content"]
        print("Received suggested categories.")
        return suggested_categories
    except Exception as e:
        print(f"Error occurred: {e}. Could not get categories.")
        return None

# Get suggested categories from OpenAI
categories_response = get_suggested_categories(initial_prompt)

# === SECTION 4: Organizing Bullet Points into Categories and Markdown Sections ===
if categories_response:
    # Parse and clean category suggestions
    categories = [category.strip() for category in categories_response.split('\n') if category.strip()]
    categorized_bullet_points = {category: [] for category in categories}

    # Assign bullet points to categories using keywords from the suggestions
    for bullet in messages:
        assigned = False
        for category in categories:
            if any(keyword.lower() in bullet.lower() for keyword in category.split()):
                categorized_bullet_points[category].append(bullet)
                assigned = True
                break
        if not assigned:
            categorized_bullet_points.setdefault('Uncategorized', []).append(bullet)

    # Remove lines that are cut off and merge duplicates
    for category in categorized_bullet_points:
        unique_points = set()
        cleaned_points = []
        for point in categorized_bullet_points[category]:
            if point.endswith('...'):
                continue
            if point not in unique_points:
                unique_points.add(point)
                cleaned_points.append(point)
        categorized_bullet_points[category] = cleaned_points

    # Construct the summary with markdown headers for each category and retain links
    newsletter = ["# Ergo Community Weekly Newsletter: Updates from the Past 7 Days\n"]
    newsletter.append("Welcome to this week's edition of the Ergo Community Newsletter. Below are the most important updates, covering development, market insights, token performance, and community activities from the past 7 days.\n")
    newsletter.append("---\n")
    
    for category, points in categorized_bullet_points.items():
        if points:
            newsletter.append(f"## {category}\n")
            for point in points:
                newsletter.append(f"- {point}\n")
            newsletter.append("\n")

    full_summary = '\n'.join(newsletter)

    # Feed the full summary back into OpenAI for final improvement
    final_prompt = ("Please enhance the following newsletter to make it more coherent, remove any lines that seem cut off, merge duplicate entries, and ensure the overall structure reads smoothly. Maintain all URLs and keep the detailed nature intact. " f"{full_summary}")

    def improve_summary(final_prompt, original_length):
        print("Improving the summary...")
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant tasked with improving a newsletter."},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            improved_summary = response.model_dump()["choices"][0]["message"]["content"]
            print("Received improved summary.")
            
            # Check if the refined summary is significantly shorter
            if len(improved_summary) < 0.8 * original_length:
                follow_up_prompt = ("The improved summary is too short compared to the original. Please expand it to match the length of the input while retaining all URLs and details. Ensure the detailed nature is intact. " f"{full_summary}")

                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant tasked with improving a newsletter."},
                        {"role": "user", "content": follow_up_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )

                improved_summary = response.model_dump()["choices"][0]["message"]["content"]

                print("Received expanded improved summary.")

            return improved_summary
        
        except Exception as e:
            print(f"Error occurred: {e}")
            return None

    # Get the refined summary
    original_length = len(full_summary)
    full_summary = improve_summary(final_prompt, original_length)

    # === SECTION 5: Filling Missing URLs ===
    # Extract URLs from the original bullet points
    url_mapping = {message: extract_urls(message) for message in messages}

    # Iterate through final output and compare with original data to fill missing URLs
    final_lines = full_summary.split("\n")
    updated_summary = []

    for line in final_lines:
        if line.startswith("- "):  # This is a bullet point line
            # Extract the original message content without the markdown symbols
            clean_bullet = line.lstrip("- ").strip()
            for original_message, urls in url_mapping.items():
                if clean_bullet in original_message and urls:  # If bullet matches original message and has URLs
                    for url in urls:
                        if url not in line:  # Add missing URL if not present
                            line += f" [Source]({url})"
        updated_summary.append(line)

    # Join updated lines back into the final summary
    full_summary_with_urls = '\n'.join(updated_summary)

    # Write the final summary to a markdown file
    output_file_path = './output/newsletter_summary.md'
    with open(output_file_path, 'w') as file:
        file.write(full_summary_with_urls)
    print(f"Summary with URLs written to {output_file_path}")

else:
    full_summary_with_urls = "Unable to get suggested categories."
    print(full_summary_with_urls)

# === SECTION 6: Display Final Summary with URLs ===
# Display the markdown-style summary with grouped sections and URLs filled in
print(f"Summary with URLs:\n{full_summary_with_urls}\n")
