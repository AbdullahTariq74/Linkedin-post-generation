"""
Patch workflow-1a — Kie AI image generation chain.
Only touches nodes AFTER Extract Contra Post.

Changes:
  1. Claude Contra Version   — append IMAGE_PROMPT instruction to user prompt
  2. Extract Contra Post     — parse imagePrompt out of agent output
  3. Build Kie Request       — NEW node: formats API body (model + prompt)
  4. Create Task1            — fix body field ($json.body not $json.imagePrompt)
  5. Parse Kie Image URL     — NEW node: extracts URL, merges with post data
  6. Generate Image (HCTI)   — uses Kie image as background + dark overlay
  7. Connections             — wire everything together
"""
import json, sys, io, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILE = r"C:\Users\abdta\Desktop\Portfolio\n8n-workflows\workflow-1a-morning-generator.json"

with open(FILE, 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes       = wf['nodes']
connections = wf['connections']

def find_node(name):
    return next((n for n in nodes if n['name'] == name), None)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Claude Contra Version — append IMAGE_PROMPT instruction to user prompt
# ─────────────────────────────────────────────────────────────────────────────
contra_node = find_node('Claude Contra Version')
current_text = contra_node['parameters'].get('text', '')

IMAGE_PROMPT_INSTRUCTION = (
    "\n\nFinally, on the very last line write exactly this (no blank line before it):\n"
    "IMAGE_PROMPT: [one sentence for an AI image generator — "
    "abstract tech visualization directly related to this post topic, "
    "dark cinematic background, purple and blue tones, "
    "no text, no logos, no people, photorealistic]"
)

if 'IMAGE_PROMPT' not in current_text:
    contra_node['parameters']['text'] = current_text + IMAGE_PROMPT_INSTRUCTION
    print("Updated: Claude Contra Version — IMAGE_PROMPT instruction appended")
else:
    print("Skipped: Claude Contra Version — IMAGE_PROMPT already present")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Extract Contra Post — parse imagePrompt from agent output
# ─────────────────────────────────────────────────────────────────────────────
extract_node = find_node('Extract Contra Post')
extract_node['parameters']['jsCode'] = r"""// Extract Contra post and IMAGE_PROMPT from AI Agent output
const agentOutput = $input.first().json.output || '';

// Split on IMAGE_PROMPT: — everything before is the post, after is the prompt
const parts = agentOutput.split(/IMAGE_PROMPT:/i);
let contraPost   = parts[0].trim();
const rawPrompt  = parts.length > 1 ? parts[1].trim() : '';

// Fallback image prompt if Claude didn't include one
const category = $('Get Today Topic').first().json.category || 'AI automation';
const topic    = $('Pick Best Trend').first().json.chosenTopic || category;
const imagePrompt = rawPrompt ||
  `Abstract tech visualization of ${topic}, dark cinematic background, purple blue tones, no text, no people`;

if (!contraPost) {
  console.log('Contra agent returned empty — using LinkedIn post as fallback');
  contraPost = $('Extract LinkedIn Post').first().json.linkedInPost;
}

const ctx = $('Extract LinkedIn Post').first().json;
console.log(`Contra post ready. Length: ${contraPost.length} chars`);
console.log(`Image prompt: "${imagePrompt.slice(0, 80)}..."`);

return [{ json: {
  title:        ctx.title,
  linkedInPost: ctx.linkedInPost,
  contraPost,
  imagePrompt,
  category:     ctx.category,
  sources:      ctx.sources,
  dateStr:      ctx.dateStr,
  dayName:      ctx.dayName,
  isSunday:     ctx.isSunday
}}];"""

print("Updated: Extract Contra Post — now parses imagePrompt")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Add "Build Kie Request" node
#    Formats the Kie AI API body: model + prompt + output settings
# ─────────────────────────────────────────────────────────────────────────────
build_kie_node = {
    "parameters": {
        "jsCode": r"""// Format the Kie AI API request body
const imagePrompt = $input.first().json.imagePrompt || 'Abstract tech visualization, dark background, no text';

const requestBody = {
  model: 'google/nano-banana',
  input: {
    prompt: imagePrompt,
    output_format: 'png',
    image_size: '16:9'
  }
};

console.log(`Kie request — prompt: "${imagePrompt.slice(0, 80)}..."`);

return [{ json: { body: JSON.stringify(requestBody) } }];"""
    },
    "id": "bbb00001-0000-4000-8000-000000000001a",
    "name": "Build Kie Request",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [6480, 1664]
}

# Insert before Create Task1
create_task_idx = next(i for i, n in enumerate(nodes) if n['name'] == 'Create Task1')
nodes.insert(create_task_idx, build_kie_node)
print("Added: Build Kie Request node")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Fix Create Task1 — body should be $json.body (from Build Kie Request)
# ─────────────────────────────────────────────────────────────────────────────
create_task_node = find_node('Create Task1')
create_task_node['parameters']['body'] = '={{ $json.body }}'
print("Fixed: Create Task1 — body now reads $json.body")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Add "Parse Kie Image URL" node
#    Extracts image URL from Kie result, merges with post data for HCTI
# ─────────────────────────────────────────────────────────────────────────────
parse_kie_node = {
    "parameters": {
        "jsCode": r"""// Extract the generated image URL from Kie AI result
const data  = $input.first().json;
let kieImageUrl = '';

try {
  const state         = data.data?.state;
  const resultJsonStr = data.data?.resultJson;

  if (state === 'success' && resultJsonStr) {
    const resultData = JSON.parse(resultJsonStr);
    kieImageUrl = resultData.resultUrls?.[0] || '';
  } else {
    console.log(`Kie state: ${state} — continuing without image`);
  }
} catch(e) {
  console.log('Kie parse error: ' + e.message + ' — continuing without image');
}

if (kieImageUrl) {
  console.log('Kie image ready: ' + kieImageUrl);
} else {
  console.log('No Kie image — HCTI will use gradient fallback background');
}

// Merge Kie image URL with all post data needed by Generate Image (HCTI)
const ctx = $('Extract Contra Post').first().json;
return [{ json: { ...ctx, kieImageUrl } }];"""
    },
    "id": "bbb00001-0000-4000-8000-000000000001b",
    "name": "Parse Kie Image URL",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [7700, 1664],
    "onError": "continueRegularOutput"
}

# Insert after If1
if1_idx = next(i for i, n in enumerate(nodes) if n['name'] == 'If1')
nodes.insert(if1_idx + 1, parse_kie_node)
print("Added: Parse Kie Image URL node")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Update Generate Image (HCTI) — Kie image as background + dark overlay
# ─────────────────────────────────────────────────────────────────────────────
image_node = find_node('Generate Image')

NEW_HTML = (
    # Outer wrapper — background switches between Kie image and gradient fallback
    "=<div style=\"font-family:'Inter',Arial,sans-serif;"
    "background:{{ $json.kieImageUrl ? 'url(' + $json.kieImageUrl + ') center/cover no-repeat' : 'linear-gradient(135deg,#0a0e1a 0%,#1a1f3a 100%)' }};"
    "color:white;width:1200px;height:628px;display:flex;"
    "flex-direction:column;padding:64px 80px;box-sizing:border-box;"
    "position:relative;overflow:hidden;\">"

    # Dark overlay — only visible when Kie image is present, transparent on gradient
    "<div style=\"position:absolute;top:0;left:0;right:0;bottom:0;"
    "background:rgba(8,12,24,{{ $json.kieImageUrl ? '0.68' : '0' }});"
    "z-index:0;\"></div>"

    # Subtle gradient blobs (always visible, add depth over both backgrounds)
    "<div style=\"position:absolute;top:-100px;right:-100px;width:520px;height:520px;"
    "background:radial-gradient(circle,rgba(99,102,241,{{ $json.kieImageUrl ? '0.12' : '0.20' }}) 0%,transparent 65%);"
    "border-radius:50%;z-index:0;\"></div>"

    "<div style=\"position:absolute;bottom:-80px;left:-60px;width:420px;height:420px;"
    "background:radial-gradient(circle,rgba(59,130,246,{{ $json.kieImageUrl ? '0.08' : '0.13' }}) 0%,transparent 65%);"
    "border-radius:50%;z-index:0;\"></div>"

    # Main content — sits above overlay
    "<div style=\"position:relative;z-index:1;flex:1;display:flex;"
    "flex-direction:column;justify-content:center;\">"

    # Category badge
    "<div style=\"display:inline-flex;align-items:center;gap:10px;"
    "margin-bottom:28px;width:fit-content;\">"
    "<div style=\"width:10px;height:10px;background:#6366f1;border-radius:50%;"
    "box-shadow:0 0 12px rgba(99,102,241,0.9);\"></div>"
    "<span style=\"font-size:12px;font-weight:700;letter-spacing:3px;"
    "text-transform:uppercase;color:#818cf8;\">{{ $json.category }}</span>"
    "</div>"

    # Title — adaptive font size
    "<div style=\"font-size:{{ ($json.title||'').length<55 ? '50' : ($json.title||'').length<85 ? '43' : '37' }}px;"
    "font-weight:800;line-height:1.15;margin-bottom:28px;"
    "max-width:860px;word-wrap:break-word;\">{{ $json.title }}</div>"

    # Accent bar
    "<div style=\"width:80px;height:4px;"
    "background:linear-gradient(90deg,#6366f1,#3b82f6);"
    "border-radius:4px;margin-bottom:28px;\"></div>"

    # Insight line — 2nd meaningful sentence from the post
    "<div style=\"font-size:19px;color:rgba(255,255,255,0.80);"
    "max-width:820px;line-height:1.65;font-weight:400;\">"
    "{{ ($json.linkedInPost||'').split('\\n').map(l=>l.trim()).filter(l=>l.length>35)[1]?.slice(0,155)||'' }}"
    "</div>"

    "</div>"  # end main content

    # Bottom decorative bar
    "<div style=\"position:relative;z-index:1;display:flex;align-items:center;"
    "gap:6px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.12);\">"
    "<div style=\"width:32px;height:3px;background:#6366f1;border-radius:2px;\"></div>"
    "<div style=\"width:20px;height:3px;background:#3b82f6;border-radius:2px;opacity:0.6;\"></div>"
    "<div style=\"width:10px;height:3px;background:rgba(255,255,255,0.3);border-radius:2px;\"></div>"
    "</div>"

    "</div>"
)

image_node['parameters']['bodyParameters']['parameters'][0]['value'] = NEW_HTML
print("Updated: Generate Image — Kie AI background + dark overlay")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Update connections
# ─────────────────────────────────────────────────────────────────────────────

# Extract Contra Post → Build Kie Request (was → Create Task1)
connections['Extract Contra Post'] = {
    "main": [[{"node": "Build Kie Request", "type": "main", "index": 0}]]
}

# Build Kie Request → Create Task1
connections['Build Kie Request'] = {
    "main": [[{"node": "Create Task1", "type": "main", "index": 0}]]
}

# If1 — true (index 0) → Wait for Generation1 (already exists, keep)
#        false (index 1) → Parse Kie Image URL (NEW)
connections['If1'] = {
    "main": [
        [{"node": "Wait for Generation1", "type": "main", "index": 0}],  # true  (still waiting)
        [{"node": "Parse Kie Image URL",  "type": "main", "index": 0}]   # false (done)
    ]
}

# Parse Kie Image URL → Generate Image
connections['Parse Kie Image URL'] = {
    "main": [[{"node": "Generate Image", "type": "main", "index": 0}]]
}

print("Updated: all connections")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Save
# ─────────────────────────────────────────────────────────────────────────────
with open(FILE, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print("\n=== PATCH COMPLETE ===")
print("\nFull chain after Extract LinkedIn Post:")
print("  Extract LinkedIn Post")
print("  → Claude Contra Version    (writes Contra post + IMAGE_PROMPT)")
print("  → Extract Contra Post      (parses both fields)")
print("  → Build Kie Request        (formats API body)")
print("  → Create Task1             (POST to api.kie.ai — starts generation)")
print("  → Wait for Generation1     (10 seconds)")
print("  → Check Task Status1       (poll recordInfo)")
print("  → If1                      (state=waiting → loop | done → proceed)")
print("  → Parse Kie Image URL      (extract URL, merge with post data)")
print("  → Generate Image (HCTI)    (Kie image as background + text overlay)")
print("  → Collect All Data")
print("  → Save to Post Log → Email Preview → Done")

# ─────────────────────────────────────────────────────────────────────────────
# 9. Verify
# ─────────────────────────────────────────────────────────────────────────────
with open(FILE, 'r', encoding='utf-8') as f:
    v = json.load(f)

node_names = [n['name'] for n in v['nodes']]
required   = ['Build Kie Request', 'Parse Kie Image URL', 'Claude Contra Version',
              'Extract Contra Post', 'Create Task1', 'Generate Image']
print("\nNode check:")
for r in required:
    print(f"  {'OK' if r in node_names else 'MISSING'} — {r}")

chain = [
    ('Extract Contra Post',  'Build Kie Request'),
    ('Build Kie Request',    'Create Task1'),
    ('Create Task1',         'Wait for Generation1'),
    ('Wait for Generation1', 'Check Task Status1'),
    ('Check Task Status1',   'If1'),
    ('Parse Kie Image URL',  'Generate Image'),
    ('Generate Image',       'Collect All Data'),
]
print("\nConnection chain:")
for src, expected in chain:
    actual = v['connections'].get(src, {}).get('main', [[]])[0]
    target = actual[0]['node'] if actual else 'NOT CONNECTED'
    ok = target == expected
    print(f"  {'OK' if ok else 'FAIL'} — {src} → {target}")

# Check If1 both branches
if1_conns = v['connections'].get('If1', {}).get('main', [])
true_target  = if1_conns[0][0]['node'] if len(if1_conns) > 0 and if1_conns[0] else 'MISSING'
false_target = if1_conns[1][0]['node'] if len(if1_conns) > 1 and if1_conns[1] else 'MISSING'
print(f"  {'OK' if true_target  == 'Wait for Generation1' else 'FAIL'} — If1 [true]  → {true_target}")
print(f"  {'OK' if false_target == 'Parse Kie Image URL'  else 'FAIL'} — If1 [false] → {false_target}")

# Check IMAGE_PROMPT in contra prompt
contra = find_node('Claude Contra Version')
has_prompt = 'IMAGE_PROMPT' in (contra['parameters'].get('text', ''))
print(f"\n  {'OK' if has_prompt else 'FAIL'} — Claude Contra has IMAGE_PROMPT instruction")

# Check Extract Contra Post parses imagePrompt
extract = find_node('Extract Contra Post')
has_parse = 'imagePrompt' in (extract['parameters'].get('jsCode', ''))
print(f"  {'OK' if has_parse else 'FAIL'} — Extract Contra Post parses imagePrompt")

# Check HCTI uses kieImageUrl
img = find_node('Generate Image')
html_val = img['parameters']['bodyParameters']['parameters'][0]['value']
has_kie_bg = 'kieImageUrl' in html_val
print(f"  {'OK' if has_kie_bg else 'FAIL'} — HCTI template uses kieImageUrl as background")
