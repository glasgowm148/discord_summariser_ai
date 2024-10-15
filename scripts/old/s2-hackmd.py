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

        # Access the response correctly
        suggested_categories = response.choices[0].message.content

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
    # Assuming categories are listed line by line
    categories = [category.strip('- ').strip() for category in categories_response.split('\n') if category.strip()]
    categorized_bullet_points = {category: [] for category in categories}

    # Assign bullet points to categories using OpenAI
    def categorize_bullet_points(bullets, categories):
        categorized_points = {category: [] for category in categories}
        uncategorized = []

        for bullet in bullets:
            prompt = (
                f"Please assign the following bullet point to one of these categories: {', '.join(categories)}.\n"
                f"Bullet point: {bullet}"
            )
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant tasked with categorizing bullet points."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    max_tokens=10
                )

                # Access the response correctly
                assigned_category = response.choices[0].message.content.strip()

                if assigned_category in categories:
                    categorized_points[assigned_category].append(bullet)
                else:
                    uncategorized.append(bullet)
            except Exception as e:
                print(f"Error occurred while categorizing bullet point: {e}")
                uncategorized.append(bullet)
        if uncategorized:
            categorized_points['Uncategorized'] = uncategorized
        return categorized_points

    # Categorize bullet points
    print("Categorizing bullet points...")
    categorized_bullet_points = categorize_bullet_points(messages, categories)

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

    # === SECTION 5: Improving the Summary with OpenAI while Retaining URLs ===
    # Adjust the final prompt to emphasize retaining URLs
    final_prompt = (
        "Please improve the following newsletter. It is very important that you retain all hyperlinks exactly as they are, so readers can access the original sources. Ensure that the newsletter is coherent, remove any lines that seem cut off, merge duplicate entries, and ensure the overall structure reads smoothly. Keep the detailed nature intact.\n"
        f"{full_summary}"
    )

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
                max_tokens=1500  # Increased max_tokens for longer output
            )

            # Access the response correctly
            improved_summary = response.choices[0].message.content

            print("Received improved summary.")

            # Check if the refined summary is significantly shorter
            if len(improved_summary) < 0.8 * original_length:
                follow_up_prompt = (
                    "The improved summary is too short compared to the original. Please expand it to match the length of the input while retaining all URLs and details. It is very important that you retain all hyperlinks exactly as they are. Ensure the detailed nature is intact.\n"
                    f"{full_summary}"
                )

                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant tasked with improving a newsletter."},
                        {"role": "user", "content": follow_up_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )

                # Access the response correctly
                improved_summary = response.choices[0].message.content

                print("Received expanded improved summary.")

            return improved_summary

        except Exception as e:
            print(f"Error occurred: {e}")
            return None

    # Get the refined summary
    original_length = len(full_summary)
    full_summary = improve_summary(final_prompt, original_length)

    # === SECTION 6: Filling Missing URLs ===
    # Extract URLs from the original bullet points
    url_mapping = {}
    for message in messages:
        urls = extract_urls(message)
        # Remove any markdown or bullet point markers
        clean_message = re.sub(r'^[-*]\s*', '', message).strip()
        url_mapping[clean_message] = urls

    # Iterate through final output and compare with original data to fill missing URLs
    final_lines = full_summary.split("\n")
    updated_summary = []

    for line in final_lines:
        if line.startswith("- "):  # This is a bullet point line
            # Extract the bullet point content without the markdown symbols
            clean_bullet = line.lstrip("- ").strip()
            for original_message, urls in url_mapping.items():
                if clean_bullet in original_message and urls:  # If bullet matches original message and has URLs
                    for url in urls:
                        if url not in line:  # Add missing URL if not present
                            line += f" [Source]({url})"
                    break  # Stop searching after the first match
        updated_summary.append(line)

    # Join updated lines back into the final summary
    full_summary_with_urls = '\n'.join(updated_summary)

    # Write the final summary to a markdown file
    output_file_path = './output/newsletter_summary.md'
    with open(output_file_path, 'w') as file:
        file.write(full_summary_with_urls)
    print(f"Summary with URLs written to {output_file_path}")

    # === SECTION 7: Generate Daily Tweet Summary ===
    tweet_prompt = (
        "Please generate a tweet highlighting the most interesting points of this newsletter. The tweet should be concise, engaging, and highlight the main updates. Use relevant hashtags and maintain any URLs exactly as they are.\n"
        f"{full_summary_with_urls}"
    )

    def generate_tweet(tweet_prompt):
        print("Generating daily tweet summary...")
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant tasked with creating a daily summary for the Ergo Ecosystem with the attached context."},
                    {"role": "user", "content": tweet_prompt}
                ],
                temperature=0.7,
                max_tokens=275
            )

            # Access the response correctly
            tweet_summary = response.choices[0].message.content

            print("Received daily tweet summary.")
            return tweet_summary
        except Exception as e:
            print(f"Error occurred: {e}")
            return None

    # Get the tweet summary
    daily_tweet_summary = generate_tweet(tweet_prompt)

    # Write the tweet summary to a markdown file
    tweet_output_file_path = './output/daily_tweet.md'
    if daily_tweet_summary:
        with open(tweet_output_file_path, 'w') as file:
            file.write(daily_tweet_summary)
        print(f"Daily tweet summary written to {tweet_output_file_path}")
    else:
        print("Unable to generate daily tweet summary.")

else:
    full_summary_with_urls = "Unable to get suggested categories."
    print(full_summary_with_urls)

# === SECTION 8: Display Final Summary with URLs ===
# Display the markdown-style summary with grouped sections and URLs filled in
print(f"Summary with URLs:\n{full_summary_with_urls}\n")
