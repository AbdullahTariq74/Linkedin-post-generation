"""Patch Tavily queries to use dynamic current year instead of hardcoded 2025."""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WORKFLOW_FILE = r"C:\Users\abdta\Desktop\Portfolio\n8n-workflows\workflow-1a-morning-generator.json"

with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# The Tavily node uses n8n expression syntax — we inject the year dynamically via JS
NEW_TAVILY_BODY = r"""={{ (() => {
  const category = $('Get Today Topic').first().json.category;
  const idea = $('Select Best Idea').first().json;
  const year = new Date().getFullYear();

  const trendQueries = {
    'Automation Tip':         `n8n Make.com workflow automation tip trick latest ${year}`,
    'Tool Spotlight':         `AI automation tool launch update comparison ${year} trending`,
    'AI & Automation News':   `AI automation business news this week ${year}`,
    'Did You Know?':          `AI automation surprising statistics fact workflow productivity ${year}`,
    'Use Case':               `AI automation ROI small business case study results ${year}`,
    'Personal Brand':         `freelance AI engineer career automation business ${year}`,
    'What I Built':           `AI automation n8n voice agent workflow build ${year}`
  };

  const baseQuery = idea.useIdea && idea.ideaTitle
    ? `${idea.ideaTitle} ${category} ${year}`
    : (trendQueries[category] || `${category} AI automation trending ${year}`);

  return JSON.stringify({
    api_key: 'PASTE_YOUR_TAVILY_API_KEY_HERE',
    query: baseQuery,
    search_depth: 'advanced',
    max_results: 7,
    include_answer: true,
    days: 7
  });
})() }}"""

updated = False
for node in workflow['nodes']:
    if node.get('name') == 'Tavily Research':
        node['parameters']['jsonBody'] = NEW_TAVILY_BODY
        # Make sure specifyBody is set
        node['parameters']['specifyBody'] = 'json'
        # Remove old bodyParameters if present
        node['parameters'].pop('bodyParameters', None)
        updated = True
        print(f"Updated node: {node['name']}")
        break

if not updated:
    print("ERROR: 'Tavily Research' node not found!")
    sys.exit(1)

with open(WORKFLOW_FILE, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("Patched — year is now dynamic (new Date().getFullYear())")
