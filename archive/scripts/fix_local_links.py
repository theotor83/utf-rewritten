import re

# This script was made by AI, use with caution and check the output. A log file will be created to easily track changes.

def convert_bbcode_urls(input_file_path, output_file_path, log_file_path):
    """
    Reads a file, converts specific bbcode [url] tags, writes the result to a new file,
    and logs the changes.

    The conversion rule is now more general:
    [url=t[number]-*.html*] -> [url=https://utf-rewritten.org/archive/t[number]-*]
    This handles URLs with or without query parameters after '.html'.

    For example:
    [url=t77-la-th-orie-de-suzy06a3.html?q=suzy]
    becomes
    [url=https://utf-rewritten.org/archive/t77-la-th-orie-de-suzy06a3]

    Args:
        input_file_path (str): The path to the input file (e.g., "posts_data.json").
        output_file_path (str): The path to the output file (e.g., "posts_data_fix.json").
        log_file_path (str): The path to the log file (e.g., "edit_logs.txt").
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f_in:
            lines = f_in.readlines()
    except FileNotFoundError:
        print(f"Error: The file '{input_file_path}' was not found.")
        return

    # This updated regex is more robust:
    # 1. (\[url=)                - Captures the opening '[url=' tag.
    # 2. (t\d+-.+?)              - Captures the essential URL part: 't', digits, a hyphen, 
    #                            and then any character non-greedily until it finds...
    # 3. \.html[^\]]*\]          - ...the literal '.html', followed by any character that is NOT a ']'
    #                            (to match query strings), and the final ']'. This part is matched but not captured.
    pattern = re.compile(r'(\[url=)(t\d+-.+?)\.html[^\]]*\]')
    
    updated_lines = []
    log_entries = []
    
    for i, line in enumerate(lines):
        # We check if the pattern exists in the current line
        if pattern.search(line):
            # If a match is found, we perform the replacement using the captured groups.
            # The new URL is constructed from group 1, the prefix, and group 2.
            # We discard everything matched after group 2.
            modified_line = pattern.sub(r'\1https://utf-rewritten.org/archive/\2]', line)
            
            # Format the log entry to show the original and the modified line
            log_entry = (
                f"Change detected on line {i+1}:\n"
                f"{line.strip()}\n"
                f"{modified_line.strip()}\n\n"
            )
            log_entries.append(log_entry)
            
            updated_lines.append(modified_line)
        else:
            # If no match, add the original line without changes
            updated_lines.append(line)

    # Write the updated content to the new file
    with open(output_file_path, 'w', encoding='utf-8') as f_out:
        f_out.writelines(updated_lines)

    # Write the logs to the log file
    with open(log_file_path, 'w', encoding='utf-8') as f_log:
        if log_entries:
            f_log.write("--- Log of all modified lines ---\n\n")
            f_log.writelines(log_entries)
        else:
            f_log.write("No matching bbcode tags were found to convert.\n")
            
    print("Processing complete.")
    print(f"Modified data saved to: {output_file_path}")
    print(f"Edit logs saved to: {log_file_path}")

if __name__ == '__main__':
    # Define the file paths
    input_file = "archive\\scripts\\posts_data.json"
    output_file = "archive\\scripts\\posts_data_fix.json"
    log_file = "archive\\scripts\\edit_logs.txt"

    # Execute the conversion
    convert_bbcode_urls(input_file, output_file, log_file)