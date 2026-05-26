"""Build workflow-3-weekly-ideas.json — reads credentials from existing workflows."""
import json, re, sys, io, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Read credentials and API keys from existing workflows ─────────────────────
with open(r'n8n-workflows/workflow-1a-morning-generator.json', encoding='utf-8') as f:
    wf1a = json.load(f)

with open(r'n8n-workflows/workflow-1b-evening-publisher.json', encoding='utf-8') as f:
    wf1b = json.load(f)

# Tavily key
tavily_node = next(n for n in wf1a['nodes'] if n['name'] == 'Tavily Trend Discovery')
key_match = re.search(r"api_key:\s*'([^']+)'", tavily_node['parameters']['jsonBody'])
tavily_key = key_match.group(1) if key_match else 'PASTE_YOUR_TAVILY_API_KEY_HERE'
print(f"Tavily key: {'found' if not tavily_key.startswith('PASTE') else 'placeholder'}")

# Claude key
claude_node = next(n for n in wf1a['nodes'] if n['name'] == 'Claude Draft Post')
claude_headers = claude_node['parameters'].get('headerParameters', {}).get('parameters', [])
claude_key = next((h['value'] for h in claude_headers if h['name'] == 'x-api-key'), 'PASTE_YOUR_CLAUDE_API_KEY_HERE')
print(f"Claude key: {'found' if not claude_key.startswith('PASTE') else 'placeholder'}")

# Google Sheets credential (from workflow-1b)
gsheets_node = next(n for n in wf1b['nodes'] if 'googleSheets' in n.get('type', ''))
gsheets_creds = copy.deepcopy(gsheets_node.get('credentials', {}))
gsheets_auth = gsheets_node['parameters'].get('authentication', 'serviceAccount')
print(f"Google Sheets creds: {list(gsheets_creds.keys())}")

# Gmail credential (from workflow-1b)
gmail_node = next(n for n in wf1b['nodes'] if 'gmail' in n.get('type', ''))
gmail_creds = copy.deepcopy(gmail_node.get('credentials', {}))
print(f"Gmail creds: {list(gmail_creds.keys())}")

# ── Build workflow ─────────────────────────────────────────────────────────────
SPREADSHEET_ID = "1IwKjyPCJ0tGpFpRceUxQwGACf9Uk0IZoSsoXqJyAAjY"

workflow = {
    "name": "Weekly Content Ideas Refill",
    "nodes": [

        # ── 1. Schedule: Sunday 8pm ──────────────────────────────────────────
        {
            "parameters": {
                "rule": {
                    "interval": [{"field": "cronExpression", "expression": "0 20 * * 0"}]
                }
            },
            "id": "ccc00001-0000-4000-8000-000000000001",
            "name": "Every Sunday 8pm",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 300]
        },

        # ── 2. Build category list ────────────────────────────────────────────
        {
            "parameters": {
                "jsCode": r"""// Build one item per category — each will be processed by Tavily + Claude
const year = new Date().getFullYear();

const categories = [
  {
    category: 'Automation Tip',
    day: 'Monday',
    trendQuery: `n8n Make.com Zapier automation workflow tip trick latest ${year}`,
    direction: 'A specific actionable automation tip, node trick, or workflow pattern that saves real time'
  },
  {
    category: 'Tool Spotlight',
    day: 'Tuesday',
    trendQuery: `n8n Make.com Vapi Retell AI LangChain Claude tool update release ${year}`,
    direction: 'A specific AI or automation tool — honest take on what it does, pros/cons, when to use it'
  },
  {
    category: 'AI & Automation News',
    day: 'Wednesday',
    trendQuery: `n8n Make.com AI automation business news trending ${year}`,
    direction: 'A real trend or news item in AI automation — what it means practically for businesses'
  },
  {
    category: 'Did You Know?',
    day: 'Thursday',
    trendQuery: `n8n Make.com automation workflow surprising fact statistic ${year}`,
    direction: 'A surprising, counterintuitive, or overlooked fact about automation or AI workflows'
  },
  {
    category: 'Use Case',
    day: 'Friday',
    trendQuery: `n8n Make.com AI automation business use case ROI result ${year}`,
    direction: 'A specific automation or AI workflow a real business type could use to save time or make money'
  },
  {
    category: 'Personal Brand',
    day: 'Saturday',
    trendQuery: `freelance AI automation engineer career n8n Make.com ${year}`,
    direction: 'A personal insight about building a freelance AI career, mindset, or lessons learned'
  }
];

console.log(`Building ideas for ${categories.length} categories`);
return categories.map(c => ({ json: c }));"""
            },
            "id": "ccc00001-0000-4000-8000-000000000002",
            "name": "Build Category List",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [220, 300]
        },

        # ── 3. Tavily: search trending topics per category ────────────────────
        {
            "parameters": {
                "method": "POST",
                "url": "https://api.tavily.com/search",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [{"name": "Content-Type", "value": "application/json"}]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": f"""={{ JSON.stringify({{
  api_key: '{tavily_key}',
  query: $json.trendQuery,
  search_depth: 'basic',
  max_results: 6,
  include_answer: false,
  days: 7
}}) }}""",
                "options": {}
            },
            "id": "ccc00001-0000-4000-8000-000000000003",
            "name": "Tavily Search",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [440, 300],
            "onError": "continueRegularOutput"
        },

        # ── 4. Prepare Claude input: merge category info + Tavily results ─────
        {
            "parameters": {
                "jsCode": r"""// Combine category context with Tavily results for Claude
const trendData = $input.first().json;
const category = $('Build Category List').item.json.category;
const direction = $('Build Category List').item.json.direction;
const day = $('Build Category List').item.json.day;
const year = new Date().getFullYear();

// Format Tavily results
let trendSummary = '';
try {
  if (trendData.results && Array.isArray(trendData.results)) {
    trendSummary = trendData.results.slice(0, 5).map((r, i) =>
      `[${i+1}] ${r.title}\n${(r.content || '').slice(0, 300)}`
    ).join('\n\n');
  }
} catch(e) {
  console.log('Tavily parse error:', e.message);
}

return [{ json: { category, direction, day, year, trendSummary: trendSummary || 'No results' }}];"""
            },
            "id": "ccc00001-0000-4000-8000-000000000004",
            "name": "Prepare Claude Input",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [660, 300]
        },

        # ── 5. Claude: generate 2 ideas per category ─────────────────────────
        {
            "parameters": {
                "method": "POST",
                "url": "https://api.anthropic.com/v1/messages",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "x-api-key", "value": claude_key},
                        {"name": "anthropic-version", "value": "2023-06-01"},
                        {"name": "content-type", "value": "application/json"}
                    ]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": r"""={
  "model": "claude-haiku-4-5-20251001",
  "max_tokens": 800,
  "messages": [{
    "role": "user",
    "content": "You help Abdullah Tariq — an AI automation engineer at Trilles AI — plan LinkedIn content.\n\nCategory: " + $json.category + "\nDay: " + $json.day + "\nContent direction: " + $json.direction + "\n\nHere are trending topics from this week:\n\n" + $json.trendSummary + "\n\nGenerate 2 content ideas for this category. Each idea should:\n- Be based on something from the trending results above (pick what would make the strongest LinkedIn post)\n- Have a specific, concrete angle — not vague\n- Be practical and relevant to AI automation / small business owners\n- Feel fresh and timely, not generic\n\nReturn ONLY this JSON array (no explanation):\n[\n  {\n    \"title\": \"Specific post title (8-12 words max)\",\n    \"angle\": \"The specific angle, what to include, why it's interesting right now (2-3 sentences)\",\n    \"priority\": \"High or Medium\"\n  },\n  {\n    \"title\": \"...\",\n    \"angle\": \"...\",\n    \"priority\": \"...\"\n  }\n]"
  }]
}"""
            },
            "id": "ccc00001-0000-4000-8000-000000000005",
            "name": "Claude Generate Ideas",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [880, 300]
        },

        # ── 6. Parse Claude response → format as sheet rows ──────────────────
        {
            "parameters": {
                "jsCode": r"""// Parse Claude's ideas and format as Content Ideas sheet rows
const response = $input.first().json;
const category = $('Build Category List').item.json.category;
const today = new Date().toISOString().split('T')[0];

let ideas = [];
try {
  const text = response.content[0].text;
  const cleaned = text.replace(/^```json\s*/i, '').replace(/```\s*$/i, '').trim();
  ideas = JSON.parse(cleaned);
} catch(e) {
  console.log(`Failed to parse Claude response for ${category}:`, e.message);
  // Return empty — this category will be skipped
  return [];
}

console.log(`${category}: parsed ${ideas.length} ideas`);

return ideas.map(idea => ({
  json: {
    'Date Added': today,
    'Idea Title': idea.title || '',
    'Category': category,
    'Full Idea / Angle': idea.angle || '',
    'Priority': idea.priority || 'Medium',
    'Status': 'Unused',
    'Notes': `Auto-generated ${today}`
  }
}));"""
            },
            "id": "ccc00001-0000-4000-8000-000000000006",
            "name": "Parse Ideas",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1100, 300]
        },

        # ── 7. Aggregate all ideas from all categories ────────────────────────
        {
            "parameters": {
                "aggregate": "aggregateAllItemData",
                "destinationFieldName": "allIdeas",
                "options": {}
            },
            "id": "ccc00001-0000-4000-8000-000000000007",
            "name": "Aggregate All Ideas",
            "type": "n8n-nodes-base.aggregate",
            "typeVersion": 1,
            "position": [1320, 300]
        },

        # ── 8. Flatten into rows for Google Sheets ────────────────────────────
        {
            "parameters": {
                "jsCode": r"""// Flatten aggregated ideas into individual rows
const allIdeas = $input.first().json.allIdeas || [];

const rows = [];
for (const item of allIdeas) {
  if (item['Idea Title']) {
    rows.push({ json: item });
  }
}

console.log(`Total ideas to write: ${rows.length}`);
if (rows.length === 0) throw new Error('No ideas generated — check Tavily and Claude nodes');

return rows;"""
            },
            "id": "ccc00001-0000-4000-8000-000000000008",
            "name": "Flatten Ideas",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1540, 300]
        },

        # ── 9. Write all ideas to Content Ideas sheet ─────────────────────────
        {
            "parameters": {
                "authentication": gsheets_auth,
                "operation": "append",
                "documentId": {
                    "__rl": True,
                    "value": SPREADSHEET_ID,
                    "mode": "id"
                },
                "sheetName": {
                    "__rl": True,
                    "value": "💡 Content Ideas",
                    "mode": "name"
                },
                "columns": {
                    "mappingMode": "defineBelow",
                    "value": {
                        "Date Added":       "={{ $json['Date Added'] }}",
                        "Idea Title":       "={{ $json['Idea Title'] }}",
                        "Category":         "={{ $json['Category'] }}",
                        "Full Idea / Angle":"={{ $json['Full Idea / Angle'] }}",
                        "Priority":         "={{ $json['Priority'] }}",
                        "Status":           "={{ $json['Status'] }}",
                        "Notes":            "={{ $json['Notes'] }}"
                    },
                    "matchingColumns": []
                },
                "options": {}
            },
            "id": "ccc00001-0000-4000-8000-000000000009",
            "name": "Write to Content Ideas",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4.4,
            "position": [1760, 300],
            "credentials": copy.deepcopy(gsheets_creds)
        },

        # ── 10. Build summary email ────────────────────────────────────────────
        {
            "parameters": {
                "jsCode": r"""// Build the weekly ideas summary email HTML
const rows = $input.all();
const today = new Date().toISOString().split('T')[0];

// Group by category
const byCategory = {};
for (const row of rows) {
  const cat = row.json['Category'] || 'Other';
  if (!byCategory[cat]) byCategory[cat] = [];
  byCategory[cat].push(row.json);
}

const categoryColors = {
  'Automation Tip':       '#6366f1',
  'Tool Spotlight':       '#0ea5e9',
  'AI & Automation News': '#f59e0b',
  'Did You Know?':        '#10b981',
  'Use Case':             '#ef4444',
  'Personal Brand':       '#8b5cf6'
};

let tableRows = '';
for (const [cat, ideas] of Object.entries(byCategory)) {
  const color = categoryColors[cat] || '#6b7280';
  for (const idea of ideas) {
    tableRows += `
    <tr>
      <td style="padding:10px 8px; border-bottom:1px solid #f3f4f6;">
        <span style="background:${color}20; color:${color}; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600;">${cat}</span>
      </td>
      <td style="padding:10px 8px; border-bottom:1px solid #f3f4f6; font-weight:500;">${idea['Idea Title']}</td>
      <td style="padding:10px 8px; border-bottom:1px solid #f3f4f6; color:#6b7280; font-size:13px;">${idea['Full Idea / Angle']}</td>
      <td style="padding:10px 8px; border-bottom:1px solid #f3f4f6; text-align:center;">
        <span style="color:${idea['Priority']==='High'?'#ef4444':'#f59e0b'}; font-weight:600; font-size:13px;">${idea['Priority']}</span>
      </td>
    </tr>`;
  }
}

const html = `
<div style="font-family:Arial,sans-serif; max-width:800px; margin:0 auto; padding:24px; color:#111;">
  <h2 style="color:#1a1f3a; border-bottom:3px solid #6366f1; padding-bottom:10px;">
    Weekly Content Ideas — ${rows.length} ideas queued for next week
  </h2>
  <p style="color:#6b7280;">These have been added to your <a href="https://docs.google.com/spreadsheets/d/1IwKjyPCJ0tGpFpRceUxQwGACf9Uk0IZoSsoXqJyAAjY">Content Ideas sheet</a>.
  Review them below — delete any you don't want posted.</p>

  <table style="width:100%; border-collapse:collapse; margin-top:16px;">
    <thead>
      <tr style="background:#f8fafc;">
        <th style="padding:10px 8px; text-align:left; font-size:13px; color:#6b7280; width:150px;">Category</th>
        <th style="padding:10px 8px; text-align:left; font-size:13px; color:#6b7280;">Topic</th>
        <th style="padding:10px 8px; text-align:left; font-size:13px; color:#6b7280;">Angle</th>
        <th style="padding:10px 8px; text-align:left; font-size:13px; color:#6b7280; width:70px;">Priority</th>
      </tr>
    </thead>
    <tbody>${tableRows}</tbody>
  </table>

  <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:8px; padding:16px; margin-top:24px; font-size:14px;">
    <strong>What to do:</strong><br>
    1. Review the ideas above<br>
    2. Open <a href="https://docs.google.com/spreadsheets/d/1IwKjyPCJ0tGpFpRceUxQwGACf9Uk0IZoSsoXqJyAAjY">Content Ideas sheet</a> → delete any rows you don't like<br>
    3. Change Priority to <strong>High</strong> for ones you want posted first<br>
    4. The daily workflow picks from these automatically all week
  </div>

  <p style="color:#d1d5db; font-size:11px; margin-top:24px;">Generated by your n8n weekly workflow · Trilles AI</p>
</div>`;

return [{ json: { html, count: rows.length, date: today } }];"""
            },
            "id": "ccc00001-0000-4000-8000-000000000010",
            "name": "Build Email",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1980, 300]
        },

        # ── 11. Send summary email ─────────────────────────────────────────────
        {
            "parameters": {
                "sendTo": "abdtariq3274@gmail.com",
                "subject": "=Weekly Content Ideas Ready — {{ $json.count }} ideas for next week",
                "message": "={{ $json.html }}",
                "options": {"appendAttribution": False}
            },
            "id": "ccc00001-0000-4000-8000-000000000011",
            "name": "Send Summary Email",
            "type": "n8n-nodes-base.gmail",
            "typeVersion": 2.1,
            "position": [2200, 300],
            "credentials": copy.deepcopy(gmail_creds)
        },

        # ── 12. Done ──────────────────────────────────────────────────────────
        {
            "parameters": {
                "jsCode": r"""const count = $('Build Email').first().json.count;
console.log(`Weekly ideas refill complete. ${count} ideas written to Content Ideas sheet.`);
return [{ json: { status: 'done', ideasGenerated: count } }];"""
            },
            "id": "ccc00001-0000-4000-8000-000000000012",
            "name": "Done",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2420, 300]
        },

        # ── Error handling ─────────────────────────────────────────────────────
        {
            "parameters": {},
            "id": "ccc00001-0000-4000-8000-000000000099",
            "name": "Error Trigger",
            "type": "n8n-nodes-base.errorTrigger",
            "typeVersion": 1,
            "position": [0, 560]
        },
        {
            "parameters": {
                "sendTo": "abdtariq3274@gmail.com",
                "subject": "=[ERROR] Weekly Ideas Refill Failed",
                "message": "=<h2 style='color:red;'>Weekly ideas workflow failed</h2><p><strong>Error:</strong> {{ $json.execution.error.message }}</p><p><strong>Node:</strong> {{ $json.execution.lastNode }}</p><p>Content Ideas sheet may not have been updated this week.</p>",
                "options": {"appendAttribution": False}
            },
            "id": "ccc00001-0000-4000-8000-000000000098",
            "name": "Error Email",
            "type": "n8n-nodes-base.gmail",
            "typeVersion": 2.1,
            "position": [220, 560],
            "credentials": copy.deepcopy(gmail_creds)
        }
    ],

    "connections": {
        "Every Sunday 8pm":     {"main": [[{"node": "Build Category List",  "type": "main", "index": 0}]]},
        "Build Category List":  {"main": [[{"node": "Tavily Search",        "type": "main", "index": 0}]]},
        "Tavily Search":        {"main": [[{"node": "Prepare Claude Input", "type": "main", "index": 0}]]},
        "Prepare Claude Input": {"main": [[{"node": "Claude Generate Ideas","type": "main", "index": 0}]]},
        "Claude Generate Ideas":{"main": [[{"node": "Parse Ideas",          "type": "main", "index": 0}]]},
        "Parse Ideas":          {"main": [[{"node": "Aggregate All Ideas",  "type": "main", "index": 0}]]},
        "Aggregate All Ideas":  {"main": [[{"node": "Flatten Ideas",        "type": "main", "index": 0}]]},
        "Flatten Ideas":        {"main": [[{"node": "Write to Content Ideas","type": "main", "index": 0}]]},
        "Write to Content Ideas":{"main": [[{"node": "Build Email",         "type": "main", "index": 0}]]},
        "Build Email":          {"main": [[{"node": "Send Summary Email",   "type": "main", "index": 0}]]},
        "Send Summary Email":   {"main": [[{"node": "Done",                 "type": "main", "index": 0}]]},
        "Error Trigger":        {"main": [[{"node": "Error Email",          "type": "main", "index": 0}]]}
    },

    "active": False,
    "settings": {"executionOrder": "v1"},
    "id": "weekly-ideas-refill-001"
}

OUT = r'n8n-workflows/workflow-3-weekly-ideas.json'
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"\nWritten: {OUT}")
print(f"\nWorkflow: {len(workflow['nodes'])} nodes")
print("\nFlow:")
print("  Every Sunday 8pm")
print("  → Build Category List  (6 categories, runs once each)")
print("  → Tavily Search        (6 calls, one per category — last 7 days)")
print("  → Prepare Claude Input")
print("  → Claude Generate Ideas (uses claude-haiku — cheap, fast)")
print("  → Parse Ideas")
print("  → Aggregate All Ideas  (collects all 6 × 2 = 12 ideas)")
print("  → Flatten Ideas")
print("  → Write to Content Ideas sheet (12 new rows)")
print("  → Build Email")
print("  → Send Summary Email   (you review + delete what you don't want)")
print("  → Done")
print(f"\nClaude model: claude-haiku (cheapest — just formatting ideas, ~$0.01/week)")
