# n8n Setup Guide — Full Step by Step
## Abdullah Tariq · Trilles AI · Daily Content Engine

---

# PART 1 — Get Your API Keys First

Before touching n8n, collect all the keys you need. Open each link, get the key, paste it in Notepad for now.

---

## Key 1 — Claude API Key (Anthropic)

You already have $5 credits. Get the key:

1. Go to **https://console.anthropic.com**
2. Sign in with your account
3. Click **"API Keys"** in the left sidebar
4. Click **"Create Key"**
5. Give it a name: `n8n content workflow`
6. Copy the key — it starts with `sk-ant-...`
7. Paste it in Notepad. **You only see it once.**

---

## Key 2 — Tavily API Key (Free)

Tavily is what searches the internet for trending topics.

1. Go to **https://app.tavily.com**
2. Click **"Sign Up"** — use your Google account or email
3. After login, you land on the dashboard
4. Your API key is shown on the main page — starts with `tvly-...`
5. Copy it → paste in Notepad

Free tier = **1,000 searches per month** (you'll use ~30/month — plenty).

---

## Key 3 — Google Sheets (You already have this)

The file is already at:
`C:\Users\abdta\Desktop\Portfolio\service_account.json`

You don't need to do anything for this one yet. Just remember where it is.

---

## Key 4 — Gmail (OAuth — done during n8n setup, no key to copy)

You'll sign in with Google directly inside n8n. No key needed right now.

---

# PART 2 — Import the Workflows into n8n

1. Open **http://localhost:5678** in your browser
2. You should see the n8n dashboard (canvas with nodes)
3. Look at the **top left** — click the **n8n logo** to go to the main menu if needed

### Import Workflow 1 (Morning Generator)

1. Click the **"+"** button (top left, next to "Workflows")
2. Click **"Import from file"**
3. Navigate to: `C:\Users\abdta\Desktop\Portfolio\n8n-workflows\`
4. Select **`workflow-1a-morning-generator.json`**
5. Click Open
6. The workflow loads — you'll see ~22 nodes connected together
7. **Don't activate it yet** — just leave it as draft
8. Click **Save** (top right)

### Import Workflow 2 (Evening Publisher)

1. Click **"+"** again → **"Import from file"**
2. Select **`workflow-1b-evening-publisher.json`**
3. Click Open → Click Save

### Import Workflow 3 (Analytics)

1. Click **"+"** again → **"Import from file"**
2. Select **`workflow-2-analytics.json`**
3. Click Open → Click Save

You should now see 3 workflows listed on the left sidebar.

---

# PART 3 — Set Up Google Sheets Credential

1. Click **"Settings"** in the left sidebar (gear icon, bottom left)
2. Click **"Credentials"**
3. Click **"Add Credential"** (top right)
4. In the search box type: `Google Sheets`
5. Select **"Google Sheets API"**
6. You'll see an Auth Type dropdown — select **"Service Account"**
7. A text field appears asking for the JSON key
8. Open **Notepad** or any text editor
9. Open the file: `C:\Users\abdta\Desktop\Portfolio\service_account.json`
10. Press **Ctrl+A** to select all → **Ctrl+C** to copy
11. Go back to n8n → paste the entire JSON into the field
12. At the top of the credential form, change the name to: **`Google Sheets`** (exactly this)
13. Click **"Save"**
14. You should see a green checkmark — it's connected

---

# PART 4 — Set Up Gmail Credential

1. Still in Settings → Credentials
2. Click **"Add Credential"**
3. Search: `Gmail`
4. Select **"Gmail OAuth2 API"**
5. Name it: **`Gmail OAuth2`** (exactly this)
6. Click **"Sign in with Google"**
7. A Google popup opens — select **abdtariq3274@gmail.com**
8. Click **"Allow"** on all permission screens
9. You'll be redirected back to n8n — it shows "Connected"
10. Click **"Save"**

---

# PART 5 — Connect Credentials to Workflow 1a (Morning Generator)

Now you link your saved credentials to the nodes inside the workflow.

1. Go back to **Workflows** (left sidebar)
2. Open **"Daily Post Generator (Morning Phase)"**
3. You'll see some nodes have a red warning icon — those need credentials fixed

### Fix all Google Sheets nodes (there are 5)

Look for these nodes — click each one:
- **"Read Topic Rotation"**
- **"Read Content Ideas"**
- **"Save to Post Log"**
- **"Mark Email Sent"**
- (and one more Google Sheets node if visible)

For **each one**:
1. Click the node to open its settings
2. Look for the **"Credential"** field — it shows an error or a placeholder
3. Click the dropdown → select **"Google Sheets"** (the one you just created)
4. Click outside to close

### Fix all Gmail nodes (there are 2)

Look for:
- **"Email Preview"**
- **"Error Email"**

For **each one**:
1. Click the node
2. Find the Credential field
3. Select **"Gmail OAuth2"**
4. Click outside

### Add Claude API Key (3 nodes)

Look for these 3 nodes:
- **"Claude Draft Post"**
- **"Claude Rewrite Pass"**
- **"Claude Contra Version"**

For **each one**:
1. Click the node to open it
2. Look for the **"Headers"** section
3. Find the header named **`x-api-key`**
4. Replace `PASTE_YOUR_CLAUDE_API_KEY_HERE` with your actual Claude key (`sk-ant-...`)
5. Click outside to close

### Add Tavily API Key (1 node)

1. Find the **"Tavily Research"** node — click it
2. Look for the **Body / JSON** field
3. Find where it says `PASTE_YOUR_TAVILY_API_KEY_HERE`
4. Replace it with your Tavily key (`tvly-...`)
5. Click outside

### Save the workflow

Click **"Save"** (top right) — important, don't skip this.

---

# PART 6 — Connect Credentials to Workflow 1b (Evening Publisher)

1. Open **"Daily Post Publisher (Evening Phase)"**
2. Fix these nodes the same way as above:

| Node name | Credential to select |
|-----------|---------------------|
| Read Post Log | Google Sheets |
| Update Status to Sent | Google Sheets |
| Send Posts Email | Gmail OAuth2 |
| Error Email | Gmail OAuth2 |

3. Click **Save**

---

# PART 7 — Connect Credentials to Workflow 2 (Analytics)

1. Open **"Weekly LinkedIn Analytics Collector"**
2. Fix these nodes:

| Node name | Credential to select |
|-----------|---------------------|
| Read Post Log | Google Sheets |
| Send Analytics Reminder Email | Gmail OAuth2 |

3. Click **Save**

---

# PART 8 — Test the Morning Workflow

**Do this before activating anything.**

1. Open **"Daily Post Generator (Morning Phase)"**
2. Find the **"Daily Schedule 8am"** node (first node, left side)
3. Click it → toggle it to **Disabled** (so it doesn't trigger automatically during testing)
4. Click **"Test Workflow"** button (top right area)
5. The workflow starts running — you'll see each node light up green as it executes
6. Wait ~30-60 seconds for all nodes to finish

### What to check after the test runs:

**In Gmail** (abdtariq3274@gmail.com):
- You should have a new email with subject like `[Review Post] 5 n8n nodes...`
- It contains: the LinkedIn post version + the Contra post version + the image (if HCTI is set up)

**In Google Sheets** → Post Log tab:
- A new row should appear at the top
- Status column = `review`
- Post Content (Full) = LinkedIn post text
- Contra Post Content = Contra post text

**If a node turned red during the test:**
- Click the red node → click "View Error"
- Most common issues:
  - Credential not connected → go back and re-select it
  - API key wrong → double-check you pasted it correctly (no extra spaces)
  - Google Sheets permission error → re-save the Google Sheets credential

---

# PART 9 — Test the Evening Workflow

1. Go to **Google Sheets → Post Log**
2. Find the test row you just created
3. Change the **Status** column from `review` → `ready`
4. Go back to n8n → open **"Daily Post Publisher (Evening Phase)"**
5. Disable the "Daily Schedule 6pm" trigger
6. Click **"Test Workflow"**

### What to check:
- Gmail: new email arrives with both posts formatted to copy-paste
- Google Sheets: Status column changes from `ready` → `sent`

---

# PART 10 — Activate Everything

Once both tests pass:

1. Open **workflow-1a** → turn the "Daily Schedule 8am" trigger back **ON** → toggle workflow to **Active**
2. Open **workflow-1b** → turn the "Daily Schedule 6pm" trigger back **ON** → toggle workflow to **Active**
3. Open **workflow-2** → toggle to **Active**

All three are now running. You're live.

---

# PART 11 — Your Daily Routine

```
Every morning (between 8am and 11am):
  ✉ Email arrives: "Review Post — [Title]"
  → Read the LinkedIn post
  → Read the Contra post
  → If both look good:
      Open Google Sheets → Post Log
      Change Status: review → ready
  → If you want to edit something:
      Edit directly in the Post Content columns in Google Sheets
      Then change Status to ready

Every evening at 6pm:
  ✉ Email arrives: "Post Ready to Publish — [Title]"
  → Copy LinkedIn post → go to linkedin.com/feed → paste → post
  → Copy Contra post → go to contra.com → paste → post
  → Open Google Sheets → Post Log → change Status to posted

Every Monday at 10am:
  ✉ Email arrives: "Weekly Review — Update your analytics"
  → Open the LinkedIn Analytics tab in Google Sheets
  → Fill in Reactions, Comments, Impressions for last week's posts
```

---

# PART 12 — Sunday (Build Post)

On Saturday evening, before Sunday's workflow runs:

1. Open Google Sheets → **Content Ideas** tab
2. Add a new row:
   - **Idea Title**: What you built/worked on this week (e.g. "AI chatbot for a restaurant booking system")
   - **Category**: `What I Built`
   - **Full Idea / Angle**: More details — tools used, problem solved, result
   - **Priority**: `High`
   - **Status**: `Unused`
3. Save

Sunday morning the workflow picks this up and writes the post around it.

If you forget — no problem. The workflow generates a general AI automation insight post instead.

---

# Quick Reference

| Thing | Where |
|-------|-------|
| n8n | http://localhost:5678 |
| Google Sheets | https://docs.google.com/spreadsheets/d/1IwKjyPCJ0tGpFpRceUxQwGACf9Uk0IZoSsoXqJyAAjY |
| Claude API keys | https://console.anthropic.com |
| Tavily API keys | https://app.tavily.com |
| Start n8n after PC restart | Run: `docker start n8n` in PowerShell |

---

# If n8n Stops (PC Restart)

n8n stops when you restart your PC. To bring it back:

1. Open **PowerShell**
2. Run: `docker start n8n`
3. Open http://localhost:5678

Done — all your workflows and credentials are saved.
