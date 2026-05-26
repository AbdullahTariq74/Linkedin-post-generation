import gspread
from google.oauth2.service_account import Credentials
import time

# Config
CREDENTIALS_FILE = r"C:\Users\abdta\Desktop\Portfolio\service_account.json"
SPREADSHEET_ID = "1IwKjyPCJ0tGpFpRceUxQwGACf9Uk0IZoSsoXqJyAAjY"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticate
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)

print(f"Connected to: {spreadsheet.title}")

# ─────────────────────────────────────────────
# Helper: get or create sheet tab
# ─────────────────────────────────────────────
def get_or_create_sheet(name, rows=1000, cols=20):
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)

# ─────────────────────────────────────────────
# Helper: format header row (bold + colored bg)
# ─────────────────────────────────────────────
def format_header(sheet, num_cols, bg_color):
    spreadsheet.batch_update({
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet.id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": bg_color,
                            "textFormat": {"bold": True, "fontSize": 10},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat"
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet.id,
                        "gridProperties": {"frozenRowCount": 1}
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            }
        ]
    })

# Color palette (RGB 0-1 scale)
BLUE   = {"red": 0.13, "green": 0.37, "blue": 0.92, "alpha": 1}
GREEN  = {"red": 0.06, "green": 0.73, "blue": 0.51, "alpha": 1}
PURPLE = {"red": 0.49, "green": 0.23, "blue": 0.93, "alpha": 1}
ORANGE = {"red": 0.96, "green": 0.62, "blue": 0.04, "alpha": 1}
TEAL   = {"red": 0.10, "green": 0.60, "blue": 0.70, "alpha": 1}

# ═══════════════════════════════════════════════════════════════
# SHEET 1 — Topic Rotation
# ═══════════════════════════════════════════════════════════════
print("Setting up Topic Rotation...")
s1 = get_or_create_sheet("📅 Topic Rotation")
s1.clear()

headers = ["Day", "Category", "Topic Title", "Description / Angle", "Hashtags", "Active", "Last Used Date", "Times Used"]
s1.append_row(headers)

topics = [
    ["Monday",    "n8n Tip",              "n8n Workflow Tip of the Week",       "Share a specific n8n node, trick, or workflow pattern that saves time",              "#n8n #automation #nocode",                    "YES", "", "0"],
    ["Tuesday",   "Voice AI",             "AI Voice Agent Use Case",             "Real-world use case for Vapi or Retell AI — dentist, law firm, contractor etc",      "#voiceai #vapi #retellai #aiagent",           "YES", "", "0"],
    ["Wednesday", "Business Automation",  "Automate This Business Process",      "Pick a common manual business task and show how to automate it with AI/n8n",         "#businessautomation #ai #productivity",       "YES", "", "0"],
    ["Thursday",  "Tool Spotlight",       "Tool Deep Dive",                       "Spotlight one tool: Vapi, Retell, LangChain, Claude, Make, Zapier — pros/cons/tips", "#aitools #langchain #claudeai #n8n",          "YES", "", "0"],
    ["Friday",    "Case Study",           "Mini Case Study / Result",             "Share a result or project from Trilles AI work — anonymized if needed",              "#casestudy #aiautomation #results",           "YES", "", "0"],
    ["Saturday",  "Engagement",           "Question / Poll",                      "Ask audience a question about automation, AI, or freelancing to drive comments",     "#ai #automation #poll #discussion",           "YES", "", "0"],
    ["Sunday",    "Personal / Insight",   "Lesson Learned / Mindset",             "Share a personal insight about freelancing, AI career, or building systems",        "#freelance #aiengineer #growthmindset",       "YES", "", "0"],
]
s1.append_rows(topics)
format_header(s1, len(headers), BLUE)
time.sleep(1)

# ═══════════════════════════════════════════════════════════════
# SHEET 2 — Post Log
# ═══════════════════════════════════════════════════════════════
print("Setting up Post Log...")
s2 = get_or_create_sheet("📝 Post Log")
s2.clear()

headers = [
    "Date", "Day", "Topic Category", "Post Title",
    "Post Content (Full)", "Image URL", "Research Sources",
    "LinkedIn Post URL", "LinkedIn Status",
    "Contra Status", "Email Sent", "Notes"
]
s2.append_row(headers)
format_header(s2, len(headers), GREEN)
time.sleep(1)

# ═══════════════════════════════════════════════════════════════
# SHEET 3 — LinkedIn Analytics
# ═══════════════════════════════════════════════════════════════
print("Setting up LinkedIn Analytics...")
s3 = get_or_create_sheet("📊 LinkedIn Analytics")
s3.clear()

headers = [
    "Date Posted", "Post Title", "Topic Category",
    "LinkedIn Post URL", "Reactions", "Comments", "Shares",
    "Impressions", "Engagement Rate (%)", "Top Reaction Type",
    "Last Checked", "Notes"
]
s3.append_row(headers)
format_header(s3, len(headers), PURPLE)
time.sleep(1)

# ═══════════════════════════════════════════════════════════════
# SHEET 4 — Content Ideas
# ═══════════════════════════════════════════════════════════════
print("Setting up Content Ideas...")
s4 = get_or_create_sheet("💡 Content Ideas")
s4.clear()

headers = [
    "Date Added", "Idea Title", "Category", "Full Idea / Angle",
    "Priority", "Status", "Assigned Day", "Notes"
]
s4.append_row(headers)

# Seed with some starter ideas
ideas = [
    ["2026-05-21", "How I built a voice agent that books appointments",    "Voice AI",            "Walk through the Retell AI + n8n + Google Calendar build step by step",        "High",   "Unused", "Friday",    "Good case study post"],
    ["2026-05-21", "5 n8n nodes every automation engineer should know",    "n8n Tip",             "HTTP Request, Code, IF, Merge, Wait — explain each with real use case",         "High",   "Unused", "Monday",    ""],
    ["2026-05-21", "Why local businesses lose 30% of leads after hours",   "Business Automation", "Set up the problem then pitch AI receptionist as the solution",                  "High",   "Unused", "Wednesday", "Good hook"],
    ["2026-05-21", "Vapi vs Retell AI — which should you choose?",         "Tool Spotlight",      "Compare both tools honestly — pricing, voice quality, integrations",             "Medium", "Unused", "Thursday",  ""],
    ["2026-05-21", "I automated my content posting with n8n and Claude",   "Case Study",          "Meta-post: show this exact workflow we built as a portfolio piece",               "High",   "Unused", "Friday",    "Very authentic"],
    ["2026-05-21", "What automation task would save you the most time?",   "Engagement",          "Simple poll question to drive comments and engagement",                          "Medium", "Unused", "Saturday",  ""],
    ["2026-05-21", "From zero to AI Automation Engineer — my path",        "Personal / Insight",  "Share your journey, Trilles AI, and where you're going",                         "Medium", "Unused", "Sunday",    "Personal branding"],
]
s4.append_rows(ideas)
format_header(s4, len(headers), ORANGE)
time.sleep(1)

# ═══════════════════════════════════════════════════════════════
# SHEET 5 — Workflow Settings
# ═══════════════════════════════════════════════════════════════
print("Setting up Workflow Settings...")
s5 = get_or_create_sheet("⚙️ Settings")
s5.clear()

headers = ["Setting Key", "Value", "Description"]
s5.append_row(headers)

settings = [
    ["POST_TIME",              "09:00",                        "Time to trigger daily post generation (24hr format)"],
    ["TIMEZONE",               "Asia/Karachi",                 "Your timezone for scheduling"],
    ["LINKEDIN_AUTO_POST",     "TRUE",                         "Whether to auto-post to LinkedIn (TRUE/FALSE)"],
    ["CONTRA_EMAIL",           "abdtariq3274@gmail.com",       "Email address to send Contra post to"],
    ["EMAIL_SUBJECT_PREFIX",   "[Contra Post]",                "Email subject line prefix"],
    ["IMAGE_GENERATION",       "htmlcsstoimage",               "Image service to use: htmlcsstoimage / dalle / flux"],
    ["ACTIVE_DAYS",            "Mon,Tue,Wed,Thu,Fri,Sat,Sun",  "Days to post (comma separated)"],
    ["CLAUDE_MODEL",           "claude-sonnet-4-6",            "Claude model to use for post generation"],
    ["TAVILY_SEARCH",          "TRUE",                         "Whether to use Tavily for research (TRUE/FALSE)"],
    ["MIN_POST_LENGTH",        "150",                          "Minimum character count for generated posts"],
    ["MAX_POST_LENGTH",        "700",                          "Maximum character count for generated posts"],
    ["WORKFLOW_VERSION",       "1.0",                          "Current workflow version"],
    ["LAST_UPDATED",           "2026-05-21",                   "Last time settings were updated"],
]
s5.append_rows(settings)
format_header(s5, len(headers), TEAL)
time.sleep(1)

# ─────────────────────────────────────────────
# Delete default "Sheet1" if it exists
# ─────────────────────────────────────────────
try:
    default = spreadsheet.worksheet("Sheet1")
    spreadsheet.del_worksheet(default)
    print("Removed default Sheet1")
except:
    pass

print("\nDONE - All sheets created successfully!")
print(f"Open your sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
