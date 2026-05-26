import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import gspread
from google.oauth2.service_account import Credentials

CREDENTIALS_FILE = r"C:\Users\abdta\Desktop\Portfolio\service_account.json"
SPREADSHEET_ID = "1IwKjyPCJ0tGpFpRceUxQwGACf9Uk0IZoSsoXqJyAAjY"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)
print(f"Connected to: {spreadsheet.title}")

# ─── 1. Add "Contra Post Content" column to Post Log after "Post Content (Full)" (col 6) ───
post_log = spreadsheet.worksheet("📝 Post Log")
headers = post_log.row_values(1)
print(f"Current Post Log headers ({len(headers)}): {headers}")

if "Contra Post Content" not in headers:
    # Insert new column at index 6 (after Post Content Full which is at col 6 = index 5)
    spreadsheet.batch_update({"requests": [{
        "insertDimension": {
            "range": {
                "sheetId": post_log.id,
                "dimension": "COLUMNS",
                "startIndex": 6,   # after col 6 (Post Content Full), inserts at col 7
                "endIndex": 7
            },
            "inheritFromBefore": False
        }
    }]})
    post_log.update_cell(1, 7, "Contra Post Content")
    print("Added 'Contra Post Content' column at position 7")
else:
    print("Contra Post Content column already exists")

# ─── 2. Update Sunday in Topic Rotation ───
topic_rotation = spreadsheet.worksheet("📅 Topic Rotation")
rows = topic_rotation.get_all_values()
print(f"\nTopic Rotation rows: {len(rows)}")

sunday_row = None
for i, row in enumerate(rows):
    if row[0] == "Sunday":
        sunday_row = i + 1  # 1-indexed
        print(f"Found Sunday at row {sunday_row}: {row[:4]}")
        break

if sunday_row:
    topic_rotation.update_cell(sunday_row, 2, "What I Built")
    topic_rotation.update_cell(sunday_row, 3, "What I Built This Week + Build Idea")
    topic_rotation.update_cell(sunday_row, 4, "Showcase a project or system you worked on this week. End with a recommended build idea for small businesses that readers could ask you to build.")
    print("Updated Sunday topic to 'What I Built'")
else:
    print("Sunday row not found!")

# ─── 3. Update Settings — set LINKEDIN_AUTO_POST to FALSE ───
settings = spreadsheet.worksheet("⚙️ Settings")
settings_rows = settings.get_all_values()
print(f"\nSettings rows: {len(settings_rows)}")

for i, row in enumerate(settings_rows):
    if row[0] == "LINKEDIN_AUTO_POST":
        settings.update_cell(i + 1, 2, "FALSE")
        print(f"Updated LINKEDIN_AUTO_POST to FALSE (was: {row[1]})")
        break

for i, row in enumerate(settings_rows):
    if row[0] == "LAST_UPDATED":
        settings.update_cell(i + 1, 2, "2026-05-25")
        break

# ─── 4. Verify final Post Log headers ───
print("\n=== Final Post Log headers ===")
final_headers = post_log.row_values(1)
for i, h in enumerate(final_headers):
    print(f"  Col {i+1}: {h}")

print("\nDONE — Sheets updated successfully!")
print(f"Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
