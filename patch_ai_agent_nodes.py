"""
Replace Claude HTTP nodes with AI Agent nodes.
- Nodes 0-12 and 19-27: untouched
- Build Claude Prompt: split into systemPrompt + userPrompt
- Claude Draft Post: HTTP → AI Agent
- Parse Draft: update to read agent output
- Claude Rewrite Pass: HTTP → AI Agent
- Extract LinkedIn Post: update to read agent output
- Claude Contra Version: HTTP → AI Agent
- Extract Contra Post: update to read agent output
- Add 3 LM sub-nodes (one per agent)
"""
import json, sys, io, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILE = r"C:\Users\abdta\Desktop\Portfolio\n8n-workflows\workflow-1a-morning-generator.json"

with open(FILE, 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes = wf['nodes']
connections = wf['connections']

def find_node(name):
    return next((n for n in nodes if n['name'] == name), None)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Build Claude Prompt → split into systemPrompt + userPrompt
# ─────────────────────────────────────────────────────────────────────────────
find_node('Build Claude Prompt')['parameters']['jsCode'] = r"""// Build Claude prompt — split into systemPrompt and userPrompt for AI Agent node
const d = $input.first().json;

let systemPrompt, userPrompt;

// ── System prompt: who Abdullah is (same for all days) ───────────────────────
systemPrompt = `You are Abdullah Tariq — an AI automation engineer from Pakistan who runs Trilles AI. You build n8n workflows, AI voice agents, chatbots, and automation systems for real businesses. You write LinkedIn posts from your own experience — direct, practical, no fluff.`;

// ── User prompt: what to write today ─────────────────────────────────────────
if (d.isSunday) {
  const buildContext = d.useIdea && d.ideaTitle
    ? `What you built/worked on this week: ${d.ideaTitle}\n${d.fullIdea ? `Details: ${d.fullIdea}` : ''}`
    : `You don't have a specific build to share today. Write about something you've been thinking about or experimenting with in AI automation this week.`;

  userPrompt = `Write today's Sunday Build Post.

${buildContext}

## What to include
1. What you built or explored this week — be concrete, name the tools, describe the problem it solved
2. One key thing you learned or a problem you ran into
3. A BUILD IDEA for your readers: one specific automation or AI project a small business owner could implement — practical, achievable, valuable
4. End with a question asking what they are building or want to automate

## Research context (use if relevant)
${d.researchBlock || 'No external research today.'}

## Writing rules
- Write like you are sharing with a smart friend in business/tech
- Short sentences, one idea per line, breathing room between thoughts
- Hook: first 2 lines must make someone stop scrolling
- Concrete over vague — tool names, numbers, real problems
- DO NOT use: bullet points, hashtags, emojis, buzzwords like game-changer/leverage/transformative
- DO NOT start the post with the word "I"
- Length: 150-250 words

Return ONLY this JSON:
{
  "title": "5-8 word title for the post",
  "post": "The full post text",
  "image_prompt": "One sentence: bold text to show, background color, visual style."
}`;

} else {
  const overrideNote = d.useIdea && d.ideaTitle
    ? `\nMANUAL TOPIC: Write specifically about "${d.ideaTitle}"${d.fullIdea ? ` — angle: ${d.fullIdea}` : ''}. Use the research as supporting context.`
    : `\nTOPIC SELECTION: Read the research below. Pick the most interesting, timely angle. The topic must come from what is actually happening in the market right now.`;

  userPrompt = `Write a LinkedIn post for today.

## Category: ${d.category}
## Direction: ${d.contentDirection}
${overrideNote}

## Real-time research — what is happening in the market right now:
${d.hasResearch ? d.researchBlock : 'No research available — write from your own expertise.'}

## Your job
${d.useIdea ? 'Write about the manual topic above using research as supporting context.' : 'Read the research. Find the most interesting angle. Write a post that feels like you just noticed something real — because you did. Do not write a generic post.'}

## Writing rules
- Write like texting a smart friend who works in business or tech
- Short sentences. One idea per line. Space between thoughts.
- Hook: first 2 lines must make someone stop scrolling — lead with the insight
- Include one specific concrete detail: a number, a tool name, a real example
- If research has a stat or fact, use it naturally
- End with a question that makes people want to reply
- DO NOT use: bullet points, hashtags, emojis, "game-changer", "leverage", "delve", "transformative"
- DO NOT start the post with the word "I"
- Length: 150-250 words

Return ONLY this JSON:
{
  "title": "5-8 word title summarising what the post is actually about",
  "post": "The full post text",
  "image_prompt": "One sentence: bold text to show, background color, visual style."
}`;
}

return [{ json: { systemPrompt, userPrompt, ...d } }];"""

print("Updated: Build Claude Prompt")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Replace Claude Draft Post (HTTP) → AI Agent
# ─────────────────────────────────────────────────────────────────────────────
draft_node = find_node('Claude Draft Post')
draft_node['type'] = '@n8n/n8n-nodes-langchain.agent'
draft_node['typeVersion'] = 1.7
draft_node['parameters'] = {
    "promptType": "define",
    "text": "={{ $json.userPrompt }}",
    "options": {
        "systemMessage": "={{ $json.systemPrompt }}"
    }
}
draft_node.pop('credentials', None)
print("Replaced: Claude Draft Post → AI Agent")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Parse Draft → read from agent output field
# ─────────────────────────────────────────────────────────────────────────────
find_node('Parse Draft')['parameters']['jsCode'] = r"""// Parse AI Agent draft response
const agentOutput = $input.first().json.output || '';
let postData;

try {
  const cleaned = agentOutput.replace(/^```json\s*/i, '').replace(/```\s*$/i, '').trim();
  postData = JSON.parse(cleaned);
} catch(e) {
  throw new Error('Agent returned invalid JSON: ' + e.message + ' | Raw: ' + agentOutput.slice(0, 200));
}

if (!postData.post || !postData.title) {
  throw new Error('Agent response missing required fields (post or title)');
}

const ctx = $('Extract Research').first().json;
console.log(`Draft ready: "${postData.title}"`);

return [{ json: {
  title: postData.title,
  post: postData.post,
  imagePrompt: postData.image_prompt || '',
  category: ctx.category,
  sources: ctx.sources,
  dateStr: ctx.dateStr,
  dayName: ctx.dayName,
  isSunday: ctx.isSunday,
  researchBlock: ctx.researchBlock
}}];"""
print("Updated: Parse Draft")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Replace Claude Rewrite Pass (HTTP) → AI Agent
# ─────────────────────────────────────────────────────────────────────────────
rewrite_node = find_node('Claude Rewrite Pass')
rewrite_node['type'] = '@n8n/n8n-nodes-langchain.agent'
rewrite_node['typeVersion'] = 1.7
rewrite_node['parameters'] = {
    "promptType": "define",
    "text": r"""=Here are 3 examples of high-performing LinkedIn posts from the automation/AI space. Study the rhythm and structure:

---
EXAMPLE 1:
My client's team was spending 6 hours a week on a task that took my automation 4 minutes to do.

The task: pulling data from 3 tools, formatting it, sending a summary email.

Total build time: 90 minutes.

Here's what I've learned building 40+ automations:

The ROI of automation isn't in the hours you save.
It's in what those hours get spent on instead.

One of my clients used those 6 hours to finally start their newsletter.
Another used it to take Friday afternoons off.

That's the real value.

What's one task in your business that you keep doing manually because you haven't gotten around to automating it?
---

EXAMPLE 2:
Most businesses don't need more AI tools.

They need the ones they already have to talk to each other.

I've audited 20+ small business tech stacks this year.
Almost every one has the same problem:

Good tools. Bad connections.

HubSpot that doesn't know what happened in Calendly.
Slack that doesn't know what closed in Stripe.
A team that fills the gaps manually every single day.

Fix the connections first.
The fancy AI agents can wait.

What does your tech stack look like right now?
---

EXAMPLE 3:
Built an AI voice receptionist for a dental clinic last month.

It answers calls, books appointments, and handles FAQs.
24/7. No staff needed.

The clinic owner told me this week they've stopped missing new patient calls entirely.

Before: 3-4 missed calls a day going to voicemail.
After: every call answered, 40% convert to bookings.

The tech: Retell AI + Twilio + n8n + Google Calendar.
Build time: about 12 hours over 2 days.

If you run a service business, I promise missed calls are costing you more than you think.

Has anyone else built voice agents for their clients? What worked?
---

Now rewrite this draft post in the same style:

DRAFT:
{{ $('Parse Draft').first().json.post }}

RULES:
- Keep all facts and insights — do not lose the research
- Strengthen the hook — first 2 lines must make someone stop scrolling
- Use the rhythm from examples: short punchy lines, then one slightly longer insight, back to short
- Sound like Abdullah: direct, practical, someone who builds real things
- DO NOT add bullet points, hashtags, emojis, or buzzwords
- DO NOT start with the word "I"
- Keep the question at the end
- Length: 150-250 words

Return ONLY the rewritten post text. No explanation.""",
    "options": {
        "systemMessage": "You are a professional content editor who helps technical founders write LinkedIn posts that get read and shared. You preserve all facts from the original while making the writing sharper, more direct, and human."
    }
}
rewrite_node.pop('credentials', None)
print("Replaced: Claude Rewrite Pass → AI Agent")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Extract LinkedIn Post → read from agent output
# ─────────────────────────────────────────────────────────────────────────────
find_node('Extract LinkedIn Post')['parameters']['jsCode'] = r"""// Extract LinkedIn post from AI Agent rewrite output
const agentOutput = $input.first().json.output || '';
let linkedInPost = agentOutput.trim();

if (!linkedInPost) {
  console.log('Rewrite agent returned empty — falling back to draft');
  linkedInPost = $('Parse Draft').first().json.post;
}

const draft = $('Parse Draft').first().json;
console.log(`LinkedIn post ready. Length: ${linkedInPost.length} chars`);

return [{ json: {
  title: draft.title,
  linkedInPost,
  imagePrompt: draft.imagePrompt,
  category: draft.category,
  sources: draft.sources,
  dateStr: draft.dateStr,
  dayName: draft.dayName,
  isSunday: draft.isSunday
}}];"""
print("Updated: Extract LinkedIn Post")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Replace Claude Contra Version (HTTP) → AI Agent
# ─────────────────────────────────────────────────────────────────────────────
contra_node = find_node('Claude Contra Version')
contra_node['type'] = '@n8n/n8n-nodes-langchain.agent'
contra_node['typeVersion'] = 1.7
contra_node['parameters'] = {
    "promptType": "define",
    "text": r"""=Here is the LinkedIn post:

{{ $('Extract LinkedIn Post').first().json.linkedInPost }}

Rewrite this as a Contra post (100-130 words) that:
1. Keeps the core topic and insight from the LinkedIn post
2. Shifts the angle slightly toward service availability — "here is what I build" or "here is what this looks like as a service"
3. Is more direct and results-focused — business owners read fast
4. Ends with a soft CTA like "If you need this built, message me on Contra" — not pushy
5. Same writing style: no jargon, no emojis, no hashtags
6. DO NOT start with "I"

Return ONLY the Contra post text. No explanation.""",
    "options": {
        "systemMessage": "You help Abdullah Tariq — an AI automation engineer at Trilles AI — adapt his LinkedIn posts for Contra, a freelancer platform where small business owners look to hire specialists. The tone is direct, practical, and service-oriented."
    }
}
contra_node.pop('credentials', None)
print("Replaced: Claude Contra Version → AI Agent")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Extract Contra Post → read from agent output
# ─────────────────────────────────────────────────────────────────────────────
find_node('Extract Contra Post')['parameters']['jsCode'] = r"""// Extract Contra post from AI Agent output
const agentOutput = $input.first().json.output || '';
let contraPost = agentOutput.trim();

if (!contraPost) {
  console.log('Contra agent returned empty — using LinkedIn post as fallback');
  contraPost = $('Extract LinkedIn Post').first().json.linkedInPost;
}

const ctx = $('Extract LinkedIn Post').first().json;
console.log(`Contra post ready. Length: ${contraPost.length} chars`);

return [{ json: {
  title: ctx.title,
  linkedInPost: ctx.linkedInPost,
  contraPost,
  imagePrompt: ctx.imagePrompt,
  category: ctx.category,
  sources: ctx.sources,
  dateStr: ctx.dateStr,
  dayName: ctx.dayName,
  isSunday: ctx.isSunday
}}];"""
print("Updated: Extract Contra Post")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Add 3 Language Model sub-nodes (one per AI Agent)
#    User needs to create an Anthropic credential in n8n and connect these
# ─────────────────────────────────────────────────────────────────────────────
lm_nodes = [
    {
        "parameters": {"model": "claude-sonnet-4-6", "options": {}},
        "id": "aaa00001-0000-4000-8000-000000000030",
        "name": "LM — Draft Post",
        "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
        "typeVersion": 1.3,
        "position": [2420, 500],
        "credentials": {
            "anthropicApi": {
                "id": "REPLACE_WITH_ANTHROPIC_CREDENTIAL_ID",
                "name": "Anthropic"
            }
        }
    },
    {
        "parameters": {"model": "claude-sonnet-4-6", "options": {}},
        "id": "aaa00001-0000-4000-8000-000000000031",
        "name": "LM — Rewrite Pass",
        "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
        "typeVersion": 1.3,
        "position": [2860, 500],
        "credentials": {
            "anthropicApi": {
                "id": "REPLACE_WITH_ANTHROPIC_CREDENTIAL_ID",
                "name": "Anthropic"
            }
        }
    },
    {
        "parameters": {"model": "claude-sonnet-4-6", "options": {}},
        "id": "aaa00001-0000-4000-8000-000000000032",
        "name": "LM — Contra Version",
        "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
        "typeVersion": 1.3,
        "position": [3300, 500],
        "credentials": {
            "anthropicApi": {
                "id": "REPLACE_WITH_ANTHROPIC_CREDENTIAL_ID",
                "name": "Anthropic"
            }
        }
    }
]

for lm in lm_nodes:
    nodes.append(lm)
print("Added: 3 LM sub-nodes (LM — Draft Post, LM — Rewrite Pass, LM — Contra Version)")

# ─────────────────────────────────────────────────────────────────────────────
# 9. Add ai_languageModel connections (sub-node → agent)
# ─────────────────────────────────────────────────────────────────────────────
connections['LM — Draft Post'] = {
    "ai_languageModel": [[{"node": "Claude Draft Post", "type": "ai_languageModel", "index": 0}]]
}
connections['LM — Rewrite Pass'] = {
    "ai_languageModel": [[{"node": "Claude Rewrite Pass", "type": "ai_languageModel", "index": 0}]]
}
connections['LM — Contra Version'] = {
    "ai_languageModel": [[{"node": "Claude Contra Version", "type": "ai_languageModel", "index": 0}]]
}
print("Added: ai_languageModel connections")

# ─────────────────────────────────────────────────────────────────────────────
# 10. Save
# ─────────────────────────────────────────────────────────────────────────────
with open(FILE, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────────────────────────────────────────
# 11. Verify
# ─────────────────────────────────────────────────────────────────────────────
with open(FILE, 'r', encoding='utf-8') as f:
    v = json.load(f)

print("\n=== VERIFICATION ===")
agent_nodes = [n for n in v['nodes'] if 'langchain' in n.get('type','')]
print(f"AI/LM nodes: {len(agent_nodes)}")
for n in agent_nodes:
    print(f"  {n['name']} | {n['type'].split('.')[-1]}")

print("\nConnections check:")
for lm in ['LM — Draft Post','LM — Rewrite Pass','LM — Contra Version']:
    conn = v['connections'].get(lm,{}).get('ai_languageModel',[[]])[0]
    target = conn[0]['node'] if conn else 'MISSING'
    print(f"  {lm} --ai_languageModel--> {target}")

print("\nDone. One step left:")
print("  n8n → Settings → Credentials → Add Credential → search 'Anthropic'")
print("  Paste your Claude API key → Save → connect to all 3 LM nodes")
print("  Then swap to OpenAI anytime: just change the LM node credential")
