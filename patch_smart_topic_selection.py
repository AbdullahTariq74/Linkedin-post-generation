"""
Patch workflow-1a for smart topic selection:
- Weekdays: Tavily finds trending topics → check Post Log for similarity → pick best unused
- Sunday: Content Ideas (what you built) still used
- Post Log read added to flow for duplicate detection
- Keyword similarity matching (not exact — conceptual overlap)
"""
import json, re, sys, io, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILE = r"C:\Users\abdta\Desktop\Portfolio\n8n-workflows\workflow-1a-morning-generator.json"

with open(FILE, 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes = wf['nodes']
connections = wf['connections']

def find_node(name):
    return next((n for n in nodes if n['name'] == name), None)

def find_gsheets_credential(nodes):
    """Find credential info from any existing Google Sheets node."""
    for n in nodes:
        if 'googleSheets' in n.get('type', ''):
            creds = n.get('credentials', {})
            if creds:
                return creds
    return {}

# ─────────────────────────────────────────────────────────────────────────────
# 1. Update "Select Best Idea" — weekdays skip Content Ideas entirely
# ─────────────────────────────────────────────────────────────────────────────
select_node = find_node('Select Best Idea')
if not select_node:
    print("ERROR: Select Best Idea not found"); sys.exit(1)

select_node['parameters']['jsCode'] = r"""// Weekdays: Tavily drives the topic — Content Ideas not used
// Sunday: check Content Ideas for what you built this week
// Any day with explicit High priority override: use it

const isSunday = $('Get Today').first().json.isSunday;
const rows = $input.all();
const category = $('Get Today Topic').first().json.category;

// ── Non-Sunday: only respect explicit High priority override ──────────────
if (!isSunday) {
  const highOverride = rows.find(r => {
    const cat = String(r.json['Category'] || '').trim();
    const status = String(r.json['Status'] || '').trim().toLowerCase();
    const priority = String(r.json['Priority'] || '').trim().toLowerCase();
    return cat === category && status === 'unused' && priority === 'high';
  });

  if (highOverride) {
    console.log(`High priority override found: "${highOverride.json['Idea Title']}"`);
    return [{ json: {
      useIdea: true,
      isSunday: false,
      category,
      ideaTitle: highOverride.json['Idea Title'] || '',
      fullIdea: highOverride.json['Full Idea / Angle'] || '',
      ideaRow: rows.indexOf(highOverride) + 2
    }}];
  }

  // Default for all weekdays: let Tavily find the topic
  console.log(`${category} — Tavily will discover today's topic from trending content`);
  return [{ json: { useIdea: false, isSunday: false, category, ideaTitle: '', fullIdea: '', ideaRow: -1 }}];
}

// ── Sunday: look for "What I Built" idea ────────────────────────────────────
const sundayIdeas = rows.filter(r => {
  const cat = String(r.json['Category'] || '').trim();
  const status = String(r.json['Status'] || '').trim().toLowerCase();
  return cat === 'What I Built' && status === 'unused';
});

const priorityOrder = { 'high': 0, 'medium': 1, 'low': 2 };
sundayIdeas.sort((a, b) => {
  const pa = priorityOrder[String(a.json['Priority'] || 'low').toLowerCase()] ?? 2;
  const pb = priorityOrder[String(b.json['Priority'] || 'low').toLowerCase()] ?? 2;
  return pa - pb;
});

if (sundayIdeas.length > 0) {
  const best = sundayIdeas[0];
  console.log(`Sunday build post: "${best.json['Idea Title']}"`);
  return [{ json: {
    useIdea: true,
    isSunday: true,
    category,
    ideaTitle: best.json['Idea Title'] || '',
    fullIdea: best.json['Full Idea / Angle'] || '',
    ideaRow: rows.indexOf(best) + 2
  }}];
}

console.log('Sunday but no build idea in Content Ideas — will generate general AI insight post');
return [{ json: { useIdea: false, isSunday: true, category, ideaTitle: '', fullIdea: '', ideaRow: -1 }}];"""

print("Updated: Select Best Idea node")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Add "Read Post Log" node — reads past post titles for duplicate detection
#    Copy credential format from existing Google Sheets node
# ─────────────────────────────────────────────────────────────────────────────
gsheets_creds = find_gsheets_credential(nodes)
print(f"Found Google Sheets credentials: {list(gsheets_creds.keys())}")

# Determine auth type from existing nodes
existing_gsheets = next((n for n in nodes if 'googleSheets' in n.get('type', '')), None)
auth_type = existing_gsheets['parameters'].get('authentication', 'serviceAccount') if existing_gsheets else 'serviceAccount'

read_post_log_node = {
    "parameters": {
        "authentication": auth_type,
        "operation": "getRows",
        "documentId": {
            "__rl": True,
            "value": "1IwKjyPCJ0tGpFpRceUxQwGACf9Uk0IZoSsoXqJyAAjY",
            "mode": "id"
        },
        "sheetName": {
            "__rl": True,
            "value": "📝 Post Log",
            "mode": "name"
        },
        "options": {
            "returnFirstMatch": False
        }
    },
    "id": "aaa00001-0000-4000-8000-000000000009d",
    "name": "Read Post Log (Past Topics)",
    "type": "n8n-nodes-base.googleSheets",
    "typeVersion": 4.4,
    "position": [1980, 300],
    "credentials": copy.deepcopy(gsheets_creds)
}

print("Created: Read Post Log (Past Topics) node")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Update "Pick Best Trend" — add similarity check against past post titles
# ─────────────────────────────────────────────────────────────────────────────
pick_node = find_node('Pick Best Trend')
if not pick_node:
    print("ERROR: Pick Best Trend not found"); sys.exit(1)

pick_node['parameters']['jsCode'] = r"""// Pick the best trending topic that we haven't written about yet
// Uses keyword similarity — not exact matching — to detect overlapping topics

const trendData = $('Tavily Trend Discovery').first().json;
const postLogRows = $input.all(); // past posts from Read Post Log
const idea = $('Select Best Idea').first().json;
const category = $('Get Today Topic').first().json.category;

// ── If manual override or Sunday with idea — skip trend selection ─────────
if (idea.useIdea && idea.ideaTitle) {
  console.log(`Override active: "${idea.ideaTitle}" — skipping trend selection`);
  return [{ json: {
    chosenTopic: idea.ideaTitle,
    chosenSnippet: idea.fullIdea || '',
    chosenUrl: '',
    topicSource: 'manual_override',
    allTrends: [],
    skippedTopics: []
  }}];
}

// ── Build list of past post titles ───────────────────────────────────────────
const pastTitles = postLogRows
  .map(r => String(r.json['Post Title'] || '').trim())
  .filter(t => t.length > 0);

console.log(`Past posts to check against: ${pastTitles.length}`);

// ── Similarity function — keyword overlap ────────────────────────────────────
const STOP_WORDS = new Set([
  'a','an','the','is','are','was','were','be','been','being','have','has','had',
  'do','does','did','will','would','could','should','may','might','must','shall',
  'can','how','what','why','when','where','who','which','that','this','these',
  'those','to','of','in','for','on','with','at','by','from','up','about','into',
  'and','but','or','nor','not','just','also','all','some','any','each','every',
  'more','most','other','such','very','even','still','back','down','here','there',
  'than','then','so','as','if','its','your','our','their','new','top','best',
  'using','use','uses','used','get','make','build','know','need','want','help',
  'good','great','way','ways','find','take','give','work','works','working',
  'tip','tips','trick','tricks','guide','look','looks','things','thing','one',
  'two','three','five','ten','first','last','next','most','many','much',
  'without','within','between','through','because','when','while','after','before'
]);

function extractKeywords(text) {
  return text.toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 2 && !STOP_WORDS.has(w));
}

function isTooSimilar(candidateTopic, pastTitle) {
  const candidateWords = new Set(extractKeywords(candidateTopic));
  const pastWords = extractKeywords(pastTitle);

  // Count how many meaningful words overlap
  const overlap = pastWords.filter(w => candidateWords.has(w));

  // 2+ meaningful keyword overlap = too similar
  if (overlap.length >= 2) {
    return { similar: true, overlap, matchedTitle: pastTitle };
  }
  return { similar: false };
}

function isTooSimilarToPast(candidateTopic) {
  for (const pastTitle of pastTitles) {
    const result = isTooSimilar(candidateTopic, pastTitle);
    if (result.similar) return result;
  }
  return { similar: false };
}

// ── Parse Tavily trend results ────────────────────────────────────────────────
let trendResults = [];
try {
  if (trendData.results && Array.isArray(trendData.results)) {
    trendResults = trendData.results
      .filter(r => r.title && r.content)
      .map(r => ({
        title: r.title,
        snippet: (r.content || '').slice(0, 300),
        url: r.url || '',
        score: parseFloat(r.score) || 0
      }))
      .sort((a, b) => b.score - a.score);
  }
} catch(e) {
  console.log('Error parsing trend results:', e.message);
}

console.log(`Trend candidates: ${trendResults.length}`);

// ── Pick the best topic we haven't covered ────────────────────────────────────
let chosenTopic = null;
let chosenSnippet = '';
let chosenUrl = '';
const skippedTopics = [];
const allTrends = trendResults.map(r => ({ title: r.title, score: r.score }));

for (const result of trendResults) {
  const similarityCheck = isTooSimilarToPast(result.title);

  if (similarityCheck.similar) {
    skippedTopics.push({
      topic: result.title,
      reason: `Too similar to past post: "${similarityCheck.matchedTitle}" (overlap: ${similarityCheck.overlap.join(', ')})`
    });
    console.log(`SKIP: "${result.title}" — similar to: "${similarityCheck.matchedTitle}"`);
    continue;
  }

  // This topic is fresh — use it
  chosenTopic = result.title;
  chosenSnippet = result.snippet;
  chosenUrl = result.url;
  console.log(`CHOSEN: "${result.title}" (score: ${result.score.toFixed(3)})`);
  break;
}

// ── Fallback: if all trending topics were already covered ────────────────────
if (!chosenTopic) {
  console.log('All trending topics already covered — using highest-score one anyway (oldest coverage)');
  if (trendResults.length > 0) {
    chosenTopic = trendResults[0].title;
    chosenSnippet = trendResults[0].snippet;
    chosenUrl = trendResults[0].url;
  } else {
    chosenTopic = category;
    chosenSnippet = '';
    chosenUrl = '';
    console.log('No trend results at all — using category as fallback');
  }
}

console.log(`Skipped ${skippedTopics.length} topics as already covered`);

return [{ json: {
  chosenTopic,
  chosenSnippet,
  chosenUrl,
  topicSource: 'tavily_trend',
  allTrends,
  skippedTopics
}}];"""

print("Updated: Pick Best Trend node")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Update connections:
#    Tavily Trend Discovery → Read Post Log (Past Topics) → Pick Best Trend
# ─────────────────────────────────────────────────────────────────────────────

# Tavily Trend Discovery now goes to Read Post Log first
connections['Tavily Trend Discovery'] = {
    "main": [[{"node": "Read Post Log (Past Topics)", "type": "main", "index": 0}]]
}

# Read Post Log → Pick Best Trend
connections['Read Post Log (Past Topics)'] = {
    "main": [[{"node": "Pick Best Trend", "type": "main", "index": 0}]]
}

# Pick Best Trend → Tavily Deep Dive (already exists, keep as is)
# (no change needed here)

print("Updated: connections")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Insert Read Post Log node into nodes array
#    Place it between Tavily Trend Discovery and Pick Best Trend
# ─────────────────────────────────────────────────────────────────────────────
tavily_trend_idx = next(i for i, n in enumerate(nodes) if n['name'] == 'Tavily Trend Discovery')
pick_best_idx = next(i for i, n in enumerate(nodes) if n['name'] == 'Pick Best Trend')

# Insert between them
insert_at = tavily_trend_idx + 1
nodes.insert(insert_at, read_post_log_node)
print(f"Inserted Read Post Log (Past Topics) at index {insert_at}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Save
# ─────────────────────────────────────────────────────────────────────────────
with open(FILE, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print("\n=== PATCH COMPLETE ===")
print("\nNew full flow:")
print("  Daily Schedule 8am → Random Delay → Wait → Get Today")
print("  → Read Topic Rotation → Get Today Topic")
print("  → Read Content Ideas → Select Best Idea  (Sunday: check 'What I Built')")
print("  → Tavily Trend Discovery                  (what's trending in this category?)")
print("  → Read Post Log (Past Topics)             (what have we already written?)")
print("  → Pick Best Trend                         (similarity check → choose fresh topic)")
print("  → Tavily Deep Dive                        (deep research on chosen topic)")
print("  → Extract Research                        (combine into rich context)")
print("  → Build Claude Prompt → Claude Draft → Claude Rewrite → Claude Contra")
print("  → Generate Image → Save to Post Log → Email Preview → Done")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Verify
# ─────────────────────────────────────────────────────────────────────────────
with open(FILE, 'r', encoding='utf-8') as f:
    verify = json.load(f)

node_names = [n['name'] for n in verify['nodes']]
required = [
    'Select Best Idea', 'Tavily Trend Discovery', 'Read Post Log (Past Topics)',
    'Pick Best Trend', 'Tavily Deep Dive', 'Extract Research', 'Build Claude Prompt'
]
print("\nNode verification:")
for r in required:
    print(f"  {'OK' if r in node_names else 'MISSING'} — {r}")

print("\nConnection chain:")
chain = [
    ('Select Best Idea', 'Tavily Trend Discovery'),
    ('Tavily Trend Discovery', 'Read Post Log (Past Topics)'),
    ('Read Post Log (Past Topics)', 'Pick Best Trend'),
    ('Pick Best Trend', 'Tavily Deep Dive'),
    ('Tavily Deep Dive', 'Extract Research'),
    ('Extract Research', 'Build Claude Prompt'),
]
for src, expected_target in chain:
    actual = verify['connections'].get(src, {}).get('main', [[]])[0]
    actual_target = actual[0]['node'] if actual else 'NOT FOUND'
    ok = actual_target == expected_target
    print(f"  {'OK' if ok else 'MISMATCH'} — {src} → {actual_target}")
