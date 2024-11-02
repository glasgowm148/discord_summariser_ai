import sqlite3
from collections import defaultdict

# Connect to the database file
db_path = 'output/projects.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Standardize names mapping for merging similar project names
name_mapping = {
    "Ergo Hack 9": "Ergo Hack",
    "Ergo Hack": "Ergo Hack",
    "Hack": "Ergo Hack",
    "Gluon Gold": "Gluon",
    # Add more mappings here as needed
}

# Retrieve and process the first 10 rows, normalizing names
cursor.execute("SELECT name, category, twitter_handle, github_repo, website, last_updated, last_summary FROM projects LIMIT 10")
rows = cursor.fetchall()

# Use defaultdict to collect merged entries
merged_data = defaultdict(list)

for row in rows:
    # Normalize the project name based on the mapping
    name = name_mapping.get(row[0], row[0])  # Use mapped name if available, otherwise original name
    category, twitter_handle, github_repo, website, last_updated, last_summary = row[1:]
    
    # Append each row's data to the merged entry
    merged_data[name].append({
        "category": category,
        "twitter_handle": twitter_handle,
        "github_repo": github_repo,
        "website": website,
        "last_updated": last_updated,
        "last_summary": last_summary
    })

# Print the consolidated result
print("First 10 rows (merged duplicates, excluding 'description'):")
for name, entries in merged_data.items():
    # Display merged information for each project name
    print(f"\n{name}:")
    for entry in entries:
        print(entry)

# Check for Cloudflare messages in the database
cursor.execute("SELECT * FROM projects WHERE description LIKE '%Cloudflare%'")
cloudflare_rows = cursor.fetchall()

if cloudflare_rows:
    print("\nCloudflare messages found in the database:")
    for row in cloudflare_rows:
        print(row)
else:
    print("\nNo Cloudflare messages found in the database.")

# Close the connection
conn.close()
