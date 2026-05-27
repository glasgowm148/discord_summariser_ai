import json
import os
import sys
import argparse

def extract_questions_from_file(filepath):
    """Extracts questions from a single JSON chat export file."""
    questions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            channel_name = data.get('channel', {}).get('name', 'Unknown Channel')
            for message in data.get('messages', []):
                content = message.get('content', '')
                author_name = message.get('author', {}).get('name', 'Unknown Author')
                timestamp = message.get('timestamp', 'No Timestamp')
                # Simple check for question mark at the end, ignoring whitespace
                if content.strip().endswith('?'):
                    questions.append(f"[{timestamp} - {channel_name} - {author_name}]: {content}")
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {filepath}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Error processing file {filepath}: {e}", file=sys.stderr)
    return questions

def main():
    parser = argparse.ArgumentParser(description='Extract questions from Discord chat export JSON files.')
    parser.add_argument('input_dir', help='Directory containing the exported JSON files.')
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    all_questions = []
    for filename in os.listdir(args.input_dir):
        if filename.lower().endswith('.json'):
            filepath = os.path.join(args.input_dir, filename)
            all_questions.extend(extract_questions_from_file(filepath))

    if all_questions:
        # Print sorted questions (optional, but nice)
        # all_questions.sort() # Sorting might mix conversations, maybe sort by timestamp later if needed
        for question in all_questions:
            print(question)
    else:
        print("No questions found in the specified directory.", file=sys.stderr)

if __name__ == "__main__":
    main()
