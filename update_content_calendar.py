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

# ─── Update Topic Rotation with new content calendar ───
topic_rotation = spreadsheet.worksheet("📅 Topic Rotation")
topic_rotation.clear()

headers = ["Day", "Post Type", "Category", "Content Direction", "Active"]
topic_rotation.append_row(headers)

new_schedule = [
    [
        "Sunday",
        "Build Post",
        "What I Built",
        "Showcase a specific project, automation, or system you worked on this week. Be concrete — name the tools, the problem it solved, and who it helped. End the post with a practical build idea that a small business owner could ask you to build for them.",
        "YES"
    ],
    [
        "Monday",
        "Value Post",
        "Automation Tip",
        "Share one specific, actionable automation tip using n8n, Make, or any automation tool. Walk through a real node, trick, or workflow pattern that saves measurable time. Concrete beats general every time.",
        "YES"
    ],
    [
        "Tuesday",
        "Value Post",
        "Tool Spotlight",
        "Spotlight one tool — n8n, Make, Zapier, Vapi, Retell AI, Claude, LangChain, etc. Give an honest take: what it does well, where it falls short, and one specific use case where you'd recommend it. Write from experience, not a product page.",
        "YES"
    ],
    [
        "Wednesday",
        "Value Post",
        "AI & Automation News",
        "Cover a real trend or recent development in AI automation. Explain what it means practically for small businesses or freelancers — not tech hype, actual implications. Take a clear opinion on whether it matters.",
        "YES"
    ],
    [
        "Thursday",
        "Value Post",
        "Did You Know?",
        "Share a surprising, counterintuitive, or little-known fact about automation or AI workflows. Something most people overlook or get wrong. Lead with the fact, then explain why it matters in practice.",
        "YES"
    ],
    [
        "Friday",
        "Value Post",
        "Use Case",
        "Describe a specific automation or AI workflow that a real type of business (dental clinic, law firm, e-commerce store, real estate agent, etc.) could use to save time or make more money. Make it detailed enough that someone could visualize building it.",
        "YES"
    ],
    [
        "Saturday",
        "Value Post",
        "Personal Brand",
        "Share a personal insight about building a freelance AI career, a mindset shift, or a lesson learned at Trilles AI. Be honest and specific — readers connect with real experiences, not motivational fluff.",
        "YES"
    ],
]

topic_rotation.append_rows(new_schedule)
print("Topic Rotation updated with new 7-day content calendar")

# ─── Update Content Ideas to match new category names ───
content_ideas = spreadsheet.worksheet("💡 Content Ideas")
content_ideas.clear()

idea_headers = ["Date Added", "Idea Title", "Category", "Full Idea / Angle", "Priority", "Status", "Notes"]
content_ideas.append_row(idea_headers)

new_ideas = [
    # Sunday — What I Built
    ["2026-05-25", "I built an AI voice receptionist for a dental clinic",             "What I Built",       "Retell AI + n8n + Google Calendar. Walk through the build: how it answers calls, books appointments, and what it took to set up. End with: 'Any service business with a phone could use this.'",                                                                "High",   "Unused", "Great first Sunday build post"],
    ["2026-05-25", "I automated this entire content system with n8n",                  "What I Built",       "Meta-post: walk through the n8n + Claude + Google Sheets system that generates these posts. Authentic, shows real capability, proves you build what you preach.",                                                                                               "High",   "Unused", "Very authentic — build post about the content workflow itself"],

    # Monday — Automation Tip
    ["2026-05-25", "5 n8n nodes every automation engineer should know",                "Automation Tip",     "HTTP Request, Code, IF, Merge, Wait — explain each with one real-world use case. Keep it practical, not encyclopedic.",                                                                                                                                         "High",   "Unused", ""],
    ["2026-05-25", "The n8n Wait node changes everything",                             "Automation Tip",     "Most people build automations that run in one shot. The Wait node lets you pause and resume — enabling human-in-the-loop workflows, retries, and scheduled follow-ups.",                                                                                          "Medium", "Unused", ""],
    ["2026-05-25", "How to use the n8n Code node to do anything",                      "Automation Tip",     "The Code node is where n8n gets unlimited. Show a practical example: parsing complex JSON, calculating dates, filtering arrays. Remove the fear of writing JavaScript.",                                                                                         "Medium", "Unused", ""],

    # Tuesday — Tool Spotlight
    ["2026-05-25", "Vapi vs Retell AI: which one should you choose?",                  "Tool Spotlight",     "Compare both honestly from real experience. Pricing, voice quality, ease of setup, integration options. Give a clear recommendation for different use cases.",                                                                                                    "High",   "Unused", ""],
    ["2026-05-25", "Why I use n8n instead of Make or Zapier",                          "Tool Spotlight",     "Self-hosted, unlimited executions, Code node for custom logic, better for complex multi-step flows. Be fair about where Make/Zapier win (ease of use, fewer technical skills).",                                                                                 "High",   "Unused", ""],
    ["2026-05-25", "What Claude API can do that ChatGPT API can't",                    "Tool Spotlight",     "Long context window, tool use, better instruction following for structured outputs. Real examples from workflows you've built.",                                                                                                                                   "Medium", "Unused", ""],

    # Wednesday — AI & Automation News
    ["2026-05-25", "AI agents are replacing entire workflows, not just tasks",         "AI & Automation News", "The shift from 'AI does one thing' to 'AI runs a process end to end.' What this means for businesses that automate now vs. wait.",                                                                                                                             "High",   "Unused", ""],
    ["2026-05-25", "Voice AI is about to be everywhere in small business",             "AI & Automation News", "The cost of AI voice agents has dropped 90% in 2 years. What's coming for local businesses: dental, legal, real estate, home services.",                                                                                                                       "Medium", "Unused", ""],

    # Thursday — Did You Know?
    ["2026-05-25", "Most businesses lose 30% of leads after hours",                    "Did You Know?",      "After-hours calls go to voicemail. Studies show 80% of callers don't leave a message. An AI receptionist running 24/7 fixes this for under $200/month.",                                                                                                         "High",   "Unused", ""],
    ["2026-05-25", "Automating one repetitive task saves 200+ hours a year",           "Did You Know?",      "A task that takes 30 minutes a day = 182 hours a year. What could your team actually do with 182 hours? Build the math into the post.",                                                                                                                          "Medium", "Unused", ""],

    # Friday — Use Case
    ["2026-05-25", "How a real estate agency could automate lead follow-up with AI",   "Use Case",           "New lead fills out a form → AI sends personalised email → books a call → logs to CRM → sends reminder. Full stack: n8n + Claude + Calendly + HubSpot.",                                                                                                         "High",   "Unused", ""],
    ["2026-05-25", "AI chatbot for a law firm: intake, FAQs, appointment booking",     "Use Case",           "Law firms spend hours on intake calls. An AI chatbot qualifies leads 24/7, answers common questions, and books consultations. Walk through the build.",                                                                                                           "High",   "Unused", ""],
    ["2026-05-25", "How an e-commerce brand could automate order follow-ups",          "Use Case",           "Order confirmed → wait 3 days → check delivery status via API → if delayed, send proactive email → if delivered, ask for review. Full n8n workflow walkthrough.",                                                                                                "Medium", "Unused", ""],

    # Saturday — Personal Brand
    ["2026-05-25", "From zero to AI Automation Engineer: my path",                     "Personal Brand",     "Share your journey honestly: where you started, what you learned, Trilles AI, where you're going. Not a highlight reel — the real path with the hard parts.",                                                                                                    "Medium", "Unused", ""],
    ["2026-05-25", "Why I left a job to build AI systems for businesses",              "Personal Brand",     "The decision to go independent. What made you believe in this space. What Trilles AI is building. Keep it grounded — not a 'quit your job' post, a 'here's what I actually did' post.",                                                                          "Medium", "Unused", ""],
]

content_ideas.append_rows(new_ideas)
print(f"Content Ideas updated with {len(new_ideas)} seeded ideas across all 7 categories")

# ─── Print summary ───
print("\n=== New Content Calendar ===")
rows = topic_rotation.get_all_values()
for row in rows[1:]:
    print(f"  {row[0]:<12} | {row[1]:<12} | {row[2]}")

print(f"\nDONE")
print(f"Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
