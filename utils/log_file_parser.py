import re
import json
import os
from pathlib import Path
from datetime import datetime
import traceback # For detailed error info

def process_accumulated_content(lines):
    """
    Processes a list of lines belonging to a single message to extract
    reaction count and clean the message text.

    Args:
        lines (list): A list of strings representing the content lines of a message.

    Returns:
        tuple: (cleaned_message_text, reaction_count)
    """
    full_content = "\n".join(lines).strip()
    message_text = full_content
    reaction_count = 0

    # Regex patterns to find specific sections within a message's content block.
    attachment_pattern = re.compile(r"\{Attachments\}\s*\n(.*?)(?=\n\{|\Z)", re.DOTALL)
    embed_pattern = re.compile(r"\{Embed\}\s*\n(.*?)(?=\n\{|\Z)", re.DOTALL)
    reaction_pattern = re.compile(r"\{Reactions\}\s*\n(.*?)(?=\n\{|\Z)", re.DOTALL)

    try:
        # --- Find and Remove Attachments Section ---
        attachment_match = attachment_pattern.search(full_content)
        if attachment_match:
            message_text = message_text.replace(attachment_match.group(0), "").strip()

        # --- Find and Remove Embeds Section ---
        embed_match = embed_pattern.search(full_content)
        if embed_match:
            message_text = message_text.replace(embed_match.group(0), "").strip()

        # --- Find, Count, and Remove Reactions Section ---
        reaction_match = reaction_pattern.search(full_content)
        if reaction_match:
            reaction_block = reaction_match.group(1).strip()
            reactions_list = [r for r in re.split(r'\s+', reaction_block) if r]
            reaction_count = len(reactions_list)
            message_text = message_text.replace(reaction_match.group(0), "").strip()

        # --- Final Message Text Cleanup ---
        message_text = message_text.strip() # Ensure leading/trailing whitespace removed
        message_text = re.sub(r'^Forwarded from [\w#()_\-\.]+:\s*', '', message_text).strip()
        # Replace internal newlines within a message with spaces for single-line output per message
        message_text = message_text.replace('\n', ' ')
        # Remove any leftover markers just in case
        message_text = re.sub(r'\{Attachments\}|\{Embed\}|\{Reactions\}', '', message_text).strip()

    except Exception as e:
        print(f"    ERROR in process_accumulated_content: {e}")
        print(f"      Problematic content block (first 200 chars): {full_content[:200]}")
        # Keep original text on error to avoid losing data completely
        message_text = full_content.replace('\n', ' ') # Fallback


    return message_text, reaction_count


def extract_details_line_by_line(log_content):
    """
    Extracts structured message details by iterating line-by-line and
    identifying message start patterns. Includes DEBUG print statements and
    error catching within the loop.

    Args:
        log_content (str): The text content of the log file.

    Returns:
        list: A list of dictionaries, each representing a parsed message.
              Timestamp is converted to ISO 8601 format.
    """
    messages = []
    # Regex to detect the start of a new message line ONLY.
    start_pattern = re.compile(
        r"^\[(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM))\]\s+" # Grp 1: Timestamp
        r"([^\n]+)$"                                                 # Grp 2: Username (rest of line)
    )

    current_message_data = None
    current_content_lines = []
    lines = log_content.splitlines() # Split content into lines
    print(f"DEBUG: Processing {len(lines)} lines total...") # DEBUG

    for i, line in enumerate(lines):
        line_num = i + 1
        try: # <<< Added try block around line processing
            # print(f"DEBUG Line {line_num}: Processing '{line[:80]}...'") # Optional: Very verbose debug

            # Skip empty lines that might separate messages
            if not line.strip():
                # print(f"DEBUG Line {line_num}: Skipping empty line") # Optional debug
                continue

            match = start_pattern.match(line)
            if match:
                # --- Found start of a new message ---
                print(f"DEBUG Line {line_num}: Matched start pattern.") # DEBUG
                # 1. Process the *previous* message's accumulated content (if any)
                if current_message_data is not None:
                    print(f"  DEBUG: Finalizing previous message for user: {current_message_data['username']}") # DEBUG
                    # No inner try-except needed here for process_accumulated_content
                    # as it's handled by the outer loop's except block now.
                    msg_text, react_count = process_accumulated_content(current_content_lines)
                    current_message_data["message"] = msg_text
                    current_message_data["reaction_count"] = react_count
                    messages.append(current_message_data)
                    print(f"  DEBUG: Appended message. Total messages now: {len(messages)}") # DEBUG

                # 2. Start the new message
                original_timestamp_str, username = match.groups()
                username = username.strip()

                # Convert timestamp
                iso_timestamp_str = None
                try:
                    dt_object = datetime.strptime(original_timestamp_str.strip(), "%m/%d/%Y %I:%M %p")
                    iso_timestamp_str = dt_object.isoformat()
                except ValueError as e_ts: # Catch specific error
                    print(f"    Warning: Could not parse timestamp '{original_timestamp_str}': {e_ts}")
                    iso_timestamp_str = original_timestamp_str # Fallback

                print(f"  DEBUG: Starting new message for user: {username} at {iso_timestamp_str}") # DEBUG
                current_message_data = {
                    "iso_timestamp": iso_timestamp_str,
                    "username": username,
                    "message": "", # Will be filled when next message starts or EOF
                    "reaction_count": 0
                }
                current_content_lines = [] # Reset content accumulator

            elif current_message_data is not None:
                # --- Line is part of the current message's content ---
                # print(f"DEBUG Line {line_num}: Appending to content for user {current_message_data['username']}") # Optional debug
                current_content_lines.append(line)
            else:
                # Line is before the first message (e.g., header) or malformed - ignore
                # print(f"DEBUG Line {line_num}: Skipping line before first message match.") # Optional debug
                pass

        except Exception as loop_error: # <<< Catch errors inside the loop
            print(f"\n!!!!!!!!!!!!!!!!! ERROR DURING LOOP AT LINE {line_num} !!!!!!!!!!!!!!!!!!!")
            print(f"Current Line Content (first 100 chars): '{line[:100]}'")
            print(f"Error Details: {loop_error}")
            print("-------------------- TRACEBACK START --------------------")
            traceback.print_exc() # Print full traceback
            print("--------------------- TRACEBACK END ---------------------")
            print("Stopping further processing due to error.")
            break # Stop processing on error to see where it happened

    # --- Process the very last message accumulated after the loop ---
    # This block only runs if the loop completed without breaking
    if current_message_data is not None:
        print(f"DEBUG: Finalizing last message after loop for user: {current_message_data['username']}") # DEBUG
        try:
            msg_text, react_count = process_accumulated_content(current_content_lines)
            current_message_data["message"] = msg_text
            current_message_data["reaction_count"] = react_count
            messages.append(current_message_data)
            print(f"  DEBUG: Appended last message. Total messages now: {len(messages)}") # DEBUG
        except Exception as e:
            print(f"  ERROR: Failed to process content for last message (User: {current_message_data.get('username', 'N/A')}). Error: {e}")
            print("-------------------- TRACEBACK START --------------------")
            traceback.print_exc() # Print full traceback
            print("--------------------- TRACEBACK END ---------------------")


    print(f"DEBUG: Finished processing lines. Total messages extracted: {len(messages)}") # DEBUG
    return messages


def sanitize_and_extract(input_path_str, output_filename="extracted_log_data.txt"):
    """
    Reads log files from an input path (file or directory), sanitizes content,
    extracts relevant details using line-by-line processing, formats them
    into LLM-friendly text lines, and saves the combined data to a text file.

    Args:
        input_path_str (str): Path to the input log file or directory containing logs.
        output_filename (str): Name of the TXT file to save results to.
    """
    all_formatted_lines = []
    input_path = Path(input_path_str) # Convert string path to Path object

    files_to_process = []
    # Check if the input path is a file or directory.
    if input_path.is_file():
        if input_path.suffix.lower() == '.txt':
            files_to_process.append(input_path)
        else:
             print(f"Warning: Input file '{input_path}' is not a .txt file. Skipping.")
    elif input_path.is_dir():
        # Find all .txt files in the directory.
        files_to_process.extend(input_path.glob('*.txt'))
    else:
        print(f"Error: Input path '{input_path}' is not a valid file or directory.")
        return # Exit if path is invalid

    if not files_to_process:
        print(f"No .txt files found in '{input_path}'.")
        return # Exit if no files found

    print(f"Processing {len(files_to_process)} file(s)...")

    # Process each found file.
    for file_path in files_to_process:
        print(f"  Processing: {file_path.name}")
        try:
            # Read file content with UTF-8 encoding (strict errors)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"DEBUG: Read {len(content)} characters from {file_path.name}")

            # --- Corrected Sanitization ---
            content_len_before = len(content)
            header_pattern = re.compile(r"^={8,}.*?\n^={8,}\r?\n?", re.MULTILINE | re.DOTALL)
            footer_pattern = re.compile(r"^={8,}.*?\n^={8,}\r?\n?$", re.MULTILINE | re.DOTALL)

            header_match = header_pattern.search(content)
            if header_match and header_match.start() == 0:
                print("DEBUG: Removing detected header.")
                content = content[header_match.end():]
            else:
                print("DEBUG: Header pattern not found at the start.")

            footer_matches = list(footer_pattern.finditer(content))
            if footer_matches:
                last_footer_match = footer_matches[-1]
                if last_footer_match.end() > len(content) - 200:
                     print("DEBUG: Removing detected footer near end.")
                     content = content[:last_footer_match.start()]
                else:
                     print("DEBUG: Footer pattern found, but not near the end. Skipping removal.")
            else:
                print("DEBUG: Footer pattern not found.")

            content = content.strip()
            content_len_after = len(content)
            print(f"DEBUG: Sanitization removed approx {content_len_before - content_len_after} characters.")

            if not content:
                 print(f"    Warning: Content became empty after sanitization for {file_path.name}")
                 continue

            # Extract messages using the line-by-line method.
            extracted_messages = extract_details_line_by_line(content)

            # --- Format for Output ---
            for msg in extracted_messages:
                # Format: [ISO_Timestamp] Username: Message Text [Reactions: N]
                if msg['message'] or msg['reaction_count'] > 0:
                    formatted_line = (
                        f"[{msg['iso_timestamp']}] {msg['username']}: {msg['message']} "
                        f"[Reactions: {msg['reaction_count']}]"
                    )
                    all_formatted_lines.append(formatted_line)

        except Exception as e:
            # Catch errors during file read or initial sanitization
            print(f"    ERROR processing file {file_path.name}: {e}")
            print("-------------------- TRACEBACK START --------------------")
            traceback.print_exc()
            print("--------------------- TRACEBACK END ---------------------")


    # --- Save Combined Results to Text File ---
    if not all_formatted_lines:
        print("\nNo messages were formatted from the processed files.")
        return

    try:
        # Write the formatted lines to a text file, one line per message.
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            for line in all_formatted_lines:
                outfile.write(line + '\n') # Add newline after each message
        print(f"\nSuccessfully formatted {len(all_formatted_lines)} messages.")
        print(f"Output saved to '{output_filename}'")
    except Exception as e:
        print(f"\nError writing output file '{output_filename}': {e}")
        print("-------------------- TRACEBACK START --------------------")
        traceback.print_exc()
        print("--------------------- TRACEBACK END ---------------------")

# --- Main execution block ---
if __name__ == "__main__":
    # --- Instructions for Use ---
    print("\n--- Log Parser Script Instructions ---")
    print("1. Save this script as a Python file (e.g., 'parser.py').")
    print("2. Place the script in a convenient directory.")
    print("3. Decide where your log files are:")
    print("   a) Single File: Note the full path to your .txt log file.")
    print("   b) Directory: Create a directory (e.g., 'logs') and place all your .txt log files inside it.")
    print("4. Open a terminal or command prompt and navigate to the directory where you saved the script.")
    print("5. Run the script, providing the path to your log file or directory as an argument:")
    print("   - For a single file: python parser.py /path/to/your/single_log.txt")
    print("   - For a directory:   python parser.py /path/to/your/logs_directory")
    print("   * If you don't provide a path, it will look for a directory named 'logs' in the current location.")
    print("6. The script will process the file(s) and create 'extracted_log_data.txt' (formatted for LLMs) in the script's directory.")
    print("7. OBSERVE THE DEBUG OUTPUT in the console. Look for any 'ERROR DURING LOOP' messages or tracebacks.")
    print("-" * 35)

    # --- Get Input Path ---
    import sys
    if len(sys.argv) > 1:
        input_log_path = sys.argv[1]
    else:
        input_log_path = 'logs'
        print(f"No path provided. Defaulting to directory: '{input_log_path}'")
        if not os.path.exists(input_log_path):
            print(f"Creating example directory '{input_log_path}'. Place your logs here before running again, or provide a specific path.")
            os.makedirs(input_log_path, exist_ok=True)
            dummy_file_path = os.path.join(input_log_path, 'placeholder.txt')
            if not os.path.exists(dummy_file_path):
                 with open(dummy_file_path, 'w') as f:
                      f.write("Placeholder for empty logs directory.\n")

    # --- Run the main function ---
    sanitize_and_extract(input_log_path, output_filename='extracted_log_data.txt')
