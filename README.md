# LinkedIn & Contra Auto Post Generation System

An n8n-based automation system that researches trending topics daily, drafts LinkedIn + Contra posts using Claude AI, generates branded images, and emails a preview for review — all on autopilot.

---

## What It Does

- **Every morning at 8am** — researches what's trending in your content category, drafts two posts (LinkedIn + Contra), generates a branded image card (HCTI) + an AI visual (Kie AI), and emails everything for review
- **Every evening** — checks for approved posts and sends them (or emails for manual copy-paste during test period)
- **Every Sunday 8pm** — refills the Content Ideas sheet with fresh trending ideas using Tavily + Claude Haiku
- **Every Monday 10am** — emails a reminder to fill in post analytics (reactions, impressions)

---

## Architecture

```
workflow-1a  Morning Generator     (daily 8am)
workflow-1b  Evening Publisher     (daily 6pm)
workflow-2   Analytics Reminder    (weekly Monday)
workflow-3   Weekly Ideas Refill   (weekly Sunday)
```

### Daily Post Flow (workflow-1a)
```
Schedule → Random Delay → Get Today's Category
→ Read Topic Rotation → Select Best Idea (Sunday: manual; weekdays: Tavily)
→ Tavily Trend Discovery → Check Past Posts (duplicate detection)
→ Pick Best Trend → Tavily Deep Dive (research chosen topic)
→ Extract Research → Build Claude Prompt
→ Claude Draft Post (AI Agent) → Rewrite Pass → LinkedIn Post
→ Claude Contra Version (AI Agent) → Contra Post + Image Prompt
→ Build Kie Request → Kie AI Image Generation (google/nano-banana)
→ Generate HCTI Card (branded title card)
→ Collect All Data → Save to Post Log → Email Preview → Done
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| **n8n** (self-hosted) | Workflow automation engine |
| **Claude Sonnet 4.6** | Post drafting and rewriting (AI Agent nodes) |
| **Claude Haiku 4.5** | Weekly ideas generation (cheap batch task) |
| **Tavily API** | Real-time web research (trending topics) |
| **Google Sheets** | Content Ideas, Topic Rotation, Post Log |
| **Gmail OAuth2** | Email previews and notifications |
| **HCTI** | HTML → branded image card (title + category) |
| **Kie AI** | AI-generated visual (google/nano-banana model) |

---

## Content Calendar

| Day | Category |
|-----|----------|
| Monday | Automation Tip |
| Tuesday | Tool Spotlight |
| Wednesday | AI & Automation News |
| Thursday | Did You Know? |
| Friday | Use Case |
| Saturday | Personal Brand |
| Sunday | What I Built |

---

## Cost Estimate (monthly)

| Service | Cost |
|---------|------|
| Claude Sonnet 4.6 | ~$0.93/mo (30 posts × $0.031) |
| Claude Haiku 4.5 | ~$0.04/mo (weekly ideas) |
| Tavily API | Free (1,000 searches/mo) |
| HCTI | Free (100 images/mo) |
| Kie AI | ~$0.60/mo (30 images × $0.02) |
| n8n self-hosted | Free (Docker) |
| **Total** | **~$1.57/month** |

---

## Files

```
n8n-workflows/
  workflow-1a-morning-generator.json   Main daily post generator
  workflow-1b-evening-publisher.json   Evening post publisher
  workflow-2-analytics.json            Weekly analytics reminder
  workflow-3-weekly-ideas.json         Weekly ideas refill
  SETUP-GUIDE.md                       Full step-by-step setup guide
  LinkedIn Brand Engine.json           Brand voice guidelines

scripts/
  setup_sheets.py                      One-time Google Sheets setup
  update_sheets_v2.py                  Add columns + seed data
  update_content_calendar.py           Populate Topic Rotation sheet
  build_weekly_ideas_workflow.py       Build workflow-3 from scratch

patches/  (applied in order during initial setup)
  patch_two_step_tavily.py             Two-step Tavily research
  patch_smart_topic_selection.py       Smart topic selection logic
  patch_fix_discovery_queries.py       Specific Tavily search queries
  patch_ai_agent_nodes.py              Replace HTTP nodes with AI Agents
  patch_workflow.py                    Dynamic year in queries
  patch_image_template.py              HCTI image template
  patch_kie_image_chain.py             Kie AI image generation chain
  patch_hcti_clean.py                  Clean HCTI card + email layout
```

---

## Quick Start

See [`n8n-workflows/SETUP-GUIDE.md`](n8n-workflows/SETUP-GUIDE.md) for full step-by-step setup.

**API keys you need:**
- Anthropic (Claude) — [console.anthropic.com](https://console.anthropic.com)
- Tavily — [tavily.com](https://tavily.com) (free 1,000/mo)
- HCTI — [htmlcsstoimage.com](https://htmlcsstoimage.com) (free 100/mo)
- Kie AI — [kie.ai](https://kie.ai) (80 free credits on signup)
- Google Service Account — for Sheets access
- Gmail OAuth2 — for email previews

---

## Google Sheets Structure

**Topic Rotation** — 7-day content calendar  
**Content Ideas** — idea bank (auto-refilled weekly)  
**Post Log** — every post drafted, with status tracking (`review → ready → sent → posted`)  
**Settings** — system config (LINKEDIN_AUTO_POST, etc.)

---

## Notes

- LinkedIn auto-posting is disabled during test period — posts are emailed for manual copy-paste
- Duplicate detection uses keyword similarity (2+ meaningful word overlap = skip topic)
- All credentials are stored in n8n — never committed to this repo
- Patch scripts use absolute paths — update `FILE =` paths if cloning to a different machine
