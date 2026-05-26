"""Revert Tavily Trend Discovery queries to specific tool-based searches."""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILE = r"C:\Users\abdta\Desktop\Portfolio\n8n-workflows\workflow-1a-morning-generator.json"

with open(FILE, 'r', encoding='utf-8') as f:
    wf = json.load(f)

tavily_node = next(n for n in wf['nodes'] if n['name'] == 'Tavily Trend Discovery')
existing_body = tavily_node['parameters'].get('jsonBody', '')
key_match = re.search(r"api_key:\s*['\"]([^'\"]+)['\"]", existing_body)
tavily_api_key = key_match.group(1) if key_match else 'PASTE_YOUR_TAVILY_API_KEY_HERE'
print(f"API key: {'found' if not tavily_api_key.startswith('PASTE') else 'placeholder'}")

NEW_BODY = (
    "={{ (() => {\n"
    "  const category = $('Get Today Topic').first().json.category;\n"
    "  const idea = $('Select Best Idea').first().json;\n"
    "  const year = new Date().getFullYear();\n"
    "\n"
    "  const discoveryQueries = {\n"
    "    'Automation Tip':         `n8n Make.com Zapier automation workflow tip trick latest ${year}`,\n"
    "    'Tool Spotlight':         `n8n Make.com Vapi Retell AI LangChain Claude tool update release ${year}`,\n"
    "    'AI & Automation News':   `n8n Make.com AI automation business news trending ${year}`,\n"
    "    'Did You Know?':          `n8n Make.com automation workflow surprising fact statistic ${year}`,\n"
    "    'Use Case':               `n8n Make.com AI automation business use case ROI result ${year}`,\n"
    "    'Personal Brand':         `freelance AI automation engineer career n8n Make.com ${year}`,\n"
    "    'What I Built':           `n8n AI automation voice agent workflow project build ${year}`\n"
    "  };\n"
    "\n"
    "  const query = idea.useIdea && idea.ideaTitle\n"
    "    ? `${idea.ideaTitle} ${year}`\n"
    "    : (discoveryQueries[category] || `${category} automation ${year}`);\n"
    "\n"
    "  return JSON.stringify({\n"
    f"    api_key: '{tavily_api_key}',\n"
    "    query: query,\n"
    "    search_depth: 'basic',\n"
    "    max_results: 8,\n"
    "    include_answer: false,\n"
    "    days: 7\n"
    "  });\n"
    "})() }}"
)

tavily_node['parameters']['jsonBody'] = NEW_BODY

with open(FILE, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print("Restored specific queries:")
print("  Automation Tip     → n8n Make.com Zapier automation workflow tip trick latest 2026")
print("  Tool Spotlight     → n8n Make.com Vapi Retell AI LangChain Claude tool update release 2026")
print("  AI & Automation News → n8n Make.com AI automation business news trending 2026")
print("  Did You Know?      → n8n Make.com automation workflow surprising fact statistic 2026")
print("  Use Case           → n8n Make.com AI automation business use case ROI result 2026")
print("  Personal Brand     → freelance AI automation engineer career n8n Make.com 2026")
print("  What I Built       → n8n AI automation voice agent workflow project build 2026")
