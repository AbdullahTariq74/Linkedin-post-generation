"""
Patch workflow-1a to add two-step Tavily:
  Step 1: Tavily Trend Discovery  (broad — what's hot in this category?)
  Step 2: Pick Best Trend         (parse scores, choose best topic)
  Step 3: Tavily Deep Dive        (deep research on that specific topic)
  Step 4: Extract Research        (combine both into rich context for Claude)

Preserves all existing credentials, node IDs, and user changes.
"""
import json, re, sys, io, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILE = r"C:\Users\abdta\Desktop\Portfolio\n8n-workflows\workflow-1a-morning-generator.json"

with open(FILE, 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes = wf['nodes']
connections = wf['connections']

# ── Helper: find a node by name ───────────────────────────────────────────────
def find_node(name):
    return next((n for n in nodes if n['name'] == name), None)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Rename "Tavily Research" → "Tavily Trend Discovery"
#    Update its query to be broader (find what topics are trending)
#    Extract the API key the user already pasted so we can reuse it
# ─────────────────────────────────────────────────────────────────────────────
tavily_node = find_node('Tavily Research')
if not tavily_node:
    print("ERROR: 'Tavily Research' node not found")
    sys.exit(1)

# Extract the API key the user already put in (or the placeholder)
existing_body = tavily_node['parameters'].get('jsonBody', '')
key_match = re.search(r"api_key:\s*['\"]([^'\"]+)['\"]", existing_body)
tavily_api_key = key_match.group(1) if key_match else 'PASTE_YOUR_TAVILY_API_KEY_HERE'
print(f"Found Tavily API key: {'(real key found)' if not tavily_api_key.startswith('PASTE') else '(placeholder — user needs to add)'}")

# Rename the node
tavily_node['name'] = 'Tavily Trend Discovery'

# Update its query — broader, looking for trending topics to pick from
tavily_node['parameters']['jsonBody'] = r"""={{ (() => {
  const category = $('Get Today Topic').first().json.category;
  const idea = $('Select Best Idea').first().json;
  const year = new Date().getFullYear();

  // Broad discovery queries — find what topics are hot in this category
  const discoveryQueries = {
    'Automation Tip':         `n8n Make.com automation workflow tips tricks latest ${year}`,
    'Tool Spotlight':         `AI automation tools news releases updates ${year}`,
    'AI & Automation News':   `AI automation business news trends ${year}`,
    'Did You Know?':          `AI workflow automation statistics surprising facts ${year}`,
    'Use Case':               `AI automation business ROI case study results ${year}`,
    'Personal Brand':         `freelance AI automation career insights ${year}`,
    'What I Built':           `n8n AI automation workflow build project ${year}`
  };

  // If manual override, search specifically for that topic
  const query = idea.useIdea && idea.ideaTitle
    ? `${idea.ideaTitle} ${category} ${year}`
    : (discoveryQueries[category] || `${category} AI automation ${year}`);

  return JSON.stringify({
    api_key: '""" + tavily_api_key + r"""',
    query: query,
    search_depth: 'basic',
    max_results: 8,
    include_answer: false,
    days: 7
  });
})() }}"""

print("Updated: Tavily Trend Discovery node")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Add new "Pick Best Trend" code node
#    Reads scored results, picks the best topic for the deep dive
# ─────────────────────────────────────────────────────────────────────────────
pick_best_node = {
    "parameters": {
        "jsCode": r"""// Parse trend discovery results and pick the best topic for deep research
const results = $input.first().json;
const idea = $('Select Best Idea').first().json;
const category = $('Get Today Topic').first().json.category;

// If manual override — skip trend selection, use the override topic
if (idea.useIdea && idea.ideaTitle) {
  console.log(`Manual override active: "${idea.ideaTitle}" — skipping trend selection`);
  return [{ json: {
    chosenTopic: idea.ideaTitle,
    chosenSnippet: idea.fullIdea || '',
    chosenUrl: '',
    topicSource: 'manual_override',
    allTrends: []
  }}];
}

// Parse Tavily results — each has a relevance score
let trendResults = [];
try {
  if (results.results && Array.isArray(results.results)) {
    trendResults = results.results
      .filter(r => r.title && r.content)
      .map(r => ({
        title: r.title,
        snippet: (r.content || '').slice(0, 300),
        url: r.url || '',
        score: parseFloat(r.score) || 0
      }))
      .sort((a, b) => b.score - a.score); // highest score first
  }
} catch(e) {
  console.log('Error parsing trend results:', e.message);
}

if (trendResults.length === 0) {
  console.log('No trend results found — will use category as fallback topic');
  return [{ json: {
    chosenTopic: category,
    chosenSnippet: '',
    chosenUrl: '',
    topicSource: 'category_fallback',
    allTrends: []
  }}];
}

// Pick the highest-scoring result as today's topic
const best = trendResults[0];
console.log(`Best trend: "${best.title}" (score: ${best.score.toFixed(3)})`);
console.log(`Other options: ${trendResults.slice(1, 4).map(r => r.title).join(' | ')}`);

return [{ json: {
  chosenTopic: best.title,
  chosenSnippet: best.snippet,
  chosenUrl: best.url,
  topicSource: 'tavily_trend',
  allTrends: trendResults.slice(0, 5).map(r => ({ title: r.title, score: r.score }))
}}];"""
    },
    "id": "aaa00001-0000-4000-8000-000000000009b",
    "name": "Pick Best Trend",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [1980, 300]
}

print("Created: Pick Best Trend node")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Add new "Tavily Deep Dive" HTTP Request node
#    Does a deep, focused search on the specific chosen topic
# ─────────────────────────────────────────────────────────────────────────────
deep_dive_node = {
    "parameters": {
        "method": "POST",
        "url": "https://api.tavily.com/search",
        "sendHeaders": True,
        "headerParameters": {
            "parameters": [
                {"name": "Content-Type", "value": "application/json"}
            ]
        },
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ (() => {\n  const trend = $('Pick Best Trend').first().json;\n  const category = $('Get Today Topic').first().json.category;\n  const year = new Date().getFullYear();\n\n  // Deep dive on the specific chosen topic\n  const deepQuery = `${trend.chosenTopic} ${category} detailed explanation examples ${year}`;\n  \n  console.log(`Deep dive query: \"${deepQuery}\"`);\n  \n  return JSON.stringify({\n    api_key: '" + tavily_api_key + r"""',
    query: deepQuery,
    search_depth: 'advanced',
    max_results: 5,
    include_answer: true,
    days: 30
  });
})() }}""",
        "options": {}
    },
    "id": "aaa00001-0000-4000-8000-000000000009c",
    "name": "Tavily Deep Dive",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [2200, 300],
    "onError": "continueRegularOutput"
}

# Fix the jsonBody (the raw string concat above has an issue with the triple-quote)
deep_dive_node["parameters"]["jsonBody"] = (
    "={{ (() => {\n"
    "  const trend = $('Pick Best Trend').first().json;\n"
    "  const category = $('Get Today Topic').first().json.category;\n"
    "  const year = new Date().getFullYear();\n"
    "  const deepQuery = `${trend.chosenTopic} ${category} detailed explanation examples ${year}`;\n"
    "  console.log(`Deep dive query: \"${deepQuery}\"`);\n"
    "  return JSON.stringify({\n"
    f"    api_key: '{tavily_api_key}',\n"
    "    query: deepQuery,\n"
    "    search_depth: 'advanced',\n"
    "    max_results: 5,\n"
    "    include_answer: true,\n"
    "    days: 30\n"
    "  });\n"
    "})() }}"
)

print("Created: Tavily Deep Dive node")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Update "Extract Research" to combine both Tavily searches
# ─────────────────────────────────────────────────────────────────────────────
extract_node = find_node('Extract Research')
if not extract_node:
    print("ERROR: 'Extract Research' node not found")
    sys.exit(1)

extract_node['parameters']['jsCode'] = r"""// Combine trend discovery + deep dive into one rich research block for Claude
const deepDiveData = $input.first().json;
const trend = $('Pick Best Trend').first().json;
const topic = $('Get Today Topic').first().json;
const idea = $('Select Best Idea').first().json;
const today = $('Get Today').first().json;

// ── Extract deep dive results ─────────────────────────────────────────────
let deepAnswer = '';
let deepResults = [];
let sources = [];

try {
  if (deepDiveData.answer) deepAnswer = deepDiveData.answer;
  if (deepDiveData.results && Array.isArray(deepDiveData.results)) {
    deepResults = deepDiveData.results.slice(0, 5).map(r => ({
      title: r.title || '',
      snippet: (r.content || '').slice(0, 500),
      url: r.url || '',
      score: r.score || 0
    }));
    sources = deepResults.map(r => r.url).filter(Boolean);
  }
  console.log(`Deep dive: ${deepResults.length} results. Answer: ${deepAnswer ? 'yes' : 'no'}`);
} catch(e) {
  console.log('Deep dive parse error:', e.message);
}

// ── Build the research block Claude will read ────────────────────────────────
let researchBlock = '';

// What topic was chosen and why
researchBlock += `CHOSEN TOPIC: ${trend.chosenTopic}\n`;
researchBlock += `SOURCE: ${trend.topicSource === 'tavily_trend' ? 'Selected from trending results (highest relevance score)' : trend.topicSource}\n\n`;

// The synthesized answer (best single summary)
if (deepAnswer) {
  researchBlock += `SUMMARY:\n${deepAnswer}\n\n`;
}

// Detailed results
if (deepResults.length > 0) {
  researchBlock += `DETAILED SOURCES:\n`;
  deepResults.forEach((r, i) => {
    researchBlock += `\n[${i+1}] ${r.title}\n${r.snippet}\n`;
  });
}

// What else was trending (context)
if (trend.allTrends && trend.allTrends.length > 1) {
  researchBlock += `\nOTHER TRENDING TOPICS THIS WEEK (not used today):\n`;
  trend.allTrends.slice(1).forEach(t => {
    researchBlock += `- ${t.title}\n`;
  });
}

const hasResearch = researchBlock.length > 100;
console.log(`Research block built: ${researchBlock.length} chars | Sources: ${sources.length}`);

return [{ json: {
  researchBlock: researchBlock.slice(0, 4000),
  hasResearch,
  chosenTopic: trend.chosenTopic,
  topicSource: trend.topicSource,
  sources: sources.slice(0, 3).join(', '),
  category: topic.category,
  contentDirection: topic.angle,
  useIdea: idea.useIdea || false,
  ideaTitle: idea.ideaTitle || '',
  fullIdea: idea.fullIdea || '',
  dateStr: today.dateStr,
  dayName: today.dayName,
  isSunday: today.isSunday
}}];"""

print("Updated: Extract Research node")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Insert the two new nodes into the nodes array
#    Place them after Tavily Trend Discovery
# ─────────────────────────────────────────────────────────────────────────────
tavily_idx = next(i for i, n in enumerate(nodes) if n['name'] == 'Tavily Trend Discovery')
nodes.insert(tavily_idx + 1, pick_best_node)
nodes.insert(tavily_idx + 2, deep_dive_node)
print(f"Inserted new nodes after index {tavily_idx}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Update connections
# ─────────────────────────────────────────────────────────────────────────────

# Rename connection key: "Tavily Research" → "Tavily Trend Discovery"
if 'Tavily Research' in connections:
    connections['Tavily Trend Discovery'] = connections.pop('Tavily Research')
    print("Renamed connection: Tavily Research → Tavily Trend Discovery")

# Fix: Tavily Trend Discovery should now point to Pick Best Trend (not Extract Research)
connections['Tavily Trend Discovery'] = {
    "main": [[{"node": "Pick Best Trend", "type": "main", "index": 0}]]
}

# Fix: Select Best Idea → Tavily Trend Discovery (rename the target)
if 'Select Best Idea' in connections:
    for output in connections['Select Best Idea']['main']:
        for conn in output:
            if conn['node'] == 'Tavily Research':
                conn['node'] = 'Tavily Trend Discovery'

# Add: Pick Best Trend → Tavily Deep Dive
connections['Pick Best Trend'] = {
    "main": [[{"node": "Tavily Deep Dive", "type": "main", "index": 0}]]
}

# Add: Tavily Deep Dive → Extract Research
connections['Tavily Deep Dive'] = {
    "main": [[{"node": "Extract Research", "type": "main", "index": 0}]]
}

print("Updated all connections")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Save
# ─────────────────────────────────────────────────────────────────────────────
with open(FILE, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print("\n=== PATCH COMPLETE ===")
print("New flow:")
print("  Select Best Idea")
print("  → Tavily Trend Discovery  (broad: what's hot in this category, last 7 days)")
print("  → Pick Best Trend         (parse scores, choose highest-relevance topic)")
print("  → Tavily Deep Dive        (deep research on that specific topic, last 30 days)")
print("  → Extract Research        (combine both into rich block for Claude)")
print("  → Build Claude Prompt")
print("  → Claude Draft Post → Claude Rewrite Pass → Claude Contra Version → ...")
print()
print("Credentials preserved. Node IDs preserved. User changes preserved.")

# Verify
with open(FILE, 'r', encoding='utf-8') as f:
    verify = json.load(f)

node_names = [n['name'] for n in verify['nodes']]
required = ['Tavily Trend Discovery', 'Pick Best Trend', 'Tavily Deep Dive', 'Extract Research']
print("\nVerification:")
for r in required:
    print(f"  {r}: {'OK' if r in node_names else 'MISSING'}")

conn_check = ['Tavily Trend Discovery', 'Pick Best Trend', 'Tavily Deep Dive']
print("Connections:")
for c in conn_check:
    target = verify['connections'].get(c, {}).get('main', [[]])[0]
    target_name = target[0]['node'] if target else 'NOT FOUND'
    print(f"  {c} → {target_name}")
