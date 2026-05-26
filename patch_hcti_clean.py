"""
Fix Generate Image1, Collect All Data1, Email Preview1:
  - HCTI: clean branded card — title + category only, no Kie background, no personal claims
  - Collect All Data1: stores kieImageUrl separately alongside HCTI imageUrl
  - Email Preview1: shows both images — main card + Kie AI visual
"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILE = r"C:\Users\abdta\Desktop\Portfolio\n8n-workflows\workflow-1a-morning-generator.json"

with open(FILE, 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes = wf['nodes']

def find_node(name):
    return next((n for n in nodes if n['name'] == name), None)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Generate Image1 — clean HCTI card, no Kie background, no personal claims
# ─────────────────────────────────────────────────────────────────────────────
image_node = find_node('Generate Image1')

NEW_HTML = (
    # Outer wrapper — pure dark gradient, no external image
    "=<div style=\"font-family:'Inter',Arial,sans-serif;"
    "background:linear-gradient(135deg,#0a0e1a 0%,#1a1f3a 100%);"
    "color:white;width:1200px;height:628px;display:flex;"
    "flex-direction:column;padding:72px 88px;box-sizing:border-box;"
    "position:relative;overflow:hidden;\">"

    # Glow blob 1 — top right
    "<div style=\"position:absolute;top:-120px;right:-120px;width:560px;height:560px;"
    "background:radial-gradient(circle,rgba(99,102,241,0.22) 0%,transparent 65%);"
    "border-radius:50%;\"></div>"

    # Glow blob 2 — bottom left
    "<div style=\"position:absolute;bottom:-90px;left:-70px;width:440px;height:440px;"
    "background:radial-gradient(circle,rgba(59,130,246,0.14) 0%,transparent 65%);"
    "border-radius:50%;\"></div>"

    # Glow blob 3 — mid right (smaller, violet)
    "<div style=\"position:absolute;top:42%;right:80px;width:260px;height:260px;"
    "background:radial-gradient(circle,rgba(139,92,246,0.10) 0%,transparent 65%);"
    "border-radius:50%;\"></div>"

    # Main content — centered vertically, bigger breathing room (no subtitle)
    "<div style=\"position:relative;z-index:1;flex:1;display:flex;"
    "flex-direction:column;justify-content:center;\">"

    # Category badge
    "<div style=\"display:inline-flex;align-items:center;gap:12px;"
    "margin-bottom:36px;width:fit-content;\">"
    "<div style=\"width:10px;height:10px;background:#6366f1;border-radius:50%;"
    "box-shadow:0 0 14px rgba(99,102,241,0.95);\"></div>"
    "<span style=\"font-size:13px;font-weight:700;letter-spacing:3px;"
    "text-transform:uppercase;color:#818cf8;\">{{ $json.category }}</span>"
    "</div>"

    # Title — bigger since there's no subtitle competing for space
    "<div style=\"font-size:{{ ($json.title||'').length<45 ? '58' : ($json.title||'').length<70 ? '50' : ($json.title||'').length<95 ? '42' : '35' }}px;"
    "font-weight:800;line-height:1.12;margin-bottom:40px;"
    "max-width:900px;word-wrap:break-word;\">{{ $json.title }}</div>"

    # Accent bar — slightly wider for visual weight
    "<div style=\"width:100px;height:5px;"
    "background:linear-gradient(90deg,#6366f1,#3b82f6,rgba(59,130,246,0));"
    "border-radius:4px;\"></div>"

    "</div>"  # end main content

    # Bottom decorative bar
    "<div style=\"position:relative;z-index:1;display:flex;align-items:center;"
    "justify-content:space-between;padding-top:20px;"
    "border-top:1px solid rgba(255,255,255,0.10);\">"
    # Left: three dots
    "<div style=\"display:flex;gap:6px;align-items:center;\">"
    "<div style=\"width:7px;height:7px;background:#6366f1;border-radius:50%;opacity:0.8;\"></div>"
    "<div style=\"width:7px;height:7px;background:#3b82f6;border-radius:50%;opacity:0.5;\"></div>"
    "<div style=\"width:7px;height:7px;background:rgba(255,255,255,0.2);border-radius:50%;\"></div>"
    "</div>"
    # Right: subtle bars
    "<div style=\"display:flex;gap:5px;align-items:center;\">"
    "<div style=\"width:28px;height:3px;background:#6366f1;border-radius:2px;\"></div>"
    "<div style=\"width:18px;height:3px;background:#3b82f6;border-radius:2px;opacity:0.6;\"></div>"
    "<div style=\"width:10px;height:3px;background:rgba(255,255,255,0.25);border-radius:2px;\"></div>"
    "</div>"
    "</div>"

    "</div>"
)

image_node['parameters']['bodyParameters']['parameters'][0]['value'] = NEW_HTML
print("Updated: Generate Image1 — clean card, dark gradient, title + category only")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Collect All Data1 — store kieImageUrl alongside HCTI imageUrl
# ─────────────────────────────────────────────────────────────────────────────
collect_node = find_node('Collect All Data1')
collect_node['parameters']['jsCode'] = r"""// Collect all post data + both image URLs

// ── HCTI branded card (main image) ───────────────────────────────────────────
let imageUrl = '';
try {
  const imgData = $input.first().json;
  imageUrl = imgData.url || imgData.image_url || '';
  if (imageUrl) console.log('HCTI card URL:', imageUrl);
  else console.log('HCTI image not generated — continuing without it');
} catch(e) {
  console.log('HCTI step failed:', e.message);
}

// ── Kie AI generated visual (secondary image) ────────────────────────────────
let kieImageUrl = '';
try {
  kieImageUrl = $('Parse Kie Image URL').first().json.kieImageUrl || '';
  if (kieImageUrl) console.log('Kie image URL:', kieImageUrl);
  else console.log('Kie image not generated — continuing without it');
} catch(e) {
  console.log('Kie image unavailable:', e.message);
}

const ctx = $('Extract Contra Post1').first().json;

return [{ json: {
  title:        ctx.title,
  linkedInPost: ctx.linkedInPost,
  contraPost:   ctx.contraPost,
  imageUrl,        // Main image: HCTI branded card (title + category)
  kieImageUrl,     // Secondary image: Kie AI infographic/visual
  category:     ctx.category,
  sources:      ctx.sources,
  dateStr:      ctx.dateStr,
  dayName:      ctx.dayName,
  isSunday:     ctx.isSunday
}}];"""

print("Updated: Collect All Data1 — stores imageUrl (HCTI) + kieImageUrl (Kie AI)")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Email Preview1 — show both images with clear labels
# ─────────────────────────────────────────────────────────────────────────────
email_node = find_node('Email Preview1')

NEW_EMAIL = (
    "=<div style=\"font-family: Arial, sans-serif; max-width: 720px; margin: 0 auto; padding: 20px; color: #111;\">\n\n"

    "<h2 style=\"color: #1a1f3a; border-bottom: 3px solid #6366f1; padding-bottom: 10px;\">Today's Posts — Ready for Review</h2>\n\n"

    # Meta table
    "<table style=\"width: 100%; margin-bottom: 24px;\">\n"
    "  <tr><td style=\"color:#666; width:120px;\"><strong>Date:</strong></td>"
    "<td>{{ $('Collect All Data1').first().json.dateStr }}</td></tr>\n"
    "  <tr><td style=\"color:#666;\"><strong>Day:</strong></td>"
    "<td>{{ $('Collect All Data1').first().json.dayName }}</td></tr>\n"
    "  <tr><td style=\"color:#666;\"><strong>Category:</strong></td>"
    "<td>{{ $('Collect All Data1').first().json.category }}</td></tr>\n"
    "  <tr><td style=\"color:#666;\"><strong>Title:</strong></td>"
    "<td><strong>{{ $('Collect All Data1').first().json.title }}</strong></td></tr>\n"
    "</table>\n\n"

    # ── Main image: HCTI branded card ──
    "<h3 style=\"color:#1a1f3a; margin-bottom:6px;\">Main Image — Branded Card</h3>\n"
    "<p style=\"color:#6b7280; font-size:13px; margin-bottom:10px;\">Use this as your primary LinkedIn post image.</p>\n"
    "{{ $('Collect All Data1').first().json.imageUrl "
    "? '<img src=\"' + $('Collect All Data1').first().json.imageUrl + '\" "
    "style=\"width:100%; max-width:640px; border-radius:8px; margin-bottom:8px; display:block;\" />'"
    " : '<p style=\"color:#999; font-style:italic; font-size:13px;\">HCTI image not generated.</p>' }}\n"
    "{{ $('Collect All Data1').first().json.imageUrl "
    "? '<p style=\"font-size:12px; color:#9ca3af; margin-bottom:24px;\">URL: ' + $('Collect All Data1').first().json.imageUrl + '</p>'"
    " : '' }}\n\n"

    # ── Secondary image: Kie AI visual ──
    "<h3 style=\"color:#1a1f3a; margin-bottom:6px;\">Secondary Image — AI Visual (Kie)</h3>\n"
    "<p style=\"color:#6b7280; font-size:13px; margin-bottom:10px;\">Use as supporting visual or infographic in your post.</p>\n"
    "{{ $('Collect All Data1').first().json.kieImageUrl "
    "? '<img src=\"' + $('Collect All Data1').first().json.kieImageUrl + '\" "
    "style=\"width:100%; max-width:640px; border-radius:8px; margin-bottom:8px; display:block;\" />'"
    " : '<p style=\"color:#999; font-style:italic; font-size:13px;\">Kie AI image not generated.</p>' }}\n"
    "{{ $('Collect All Data1').first().json.kieImageUrl "
    "? '<p style=\"font-size:12px; color:#9ca3af; margin-bottom:24px;\">URL: ' + $('Collect All Data1').first().json.kieImageUrl + '</p>'"
    " : '' }}\n\n"

    "<hr style=\"border: 1px solid #e5e7eb; margin: 24px 0;\">\n\n"

    # LinkedIn post
    "<h3 style=\"color: #1a1f3a; margin-bottom: 8px;\">LinkedIn Post</h3>\n"
    "<p style=\"color: #6b7280; font-size: 13px; margin-bottom: 12px;\">Copy and paste this to LinkedIn manually.</p>\n"
    "<div style=\"background: #f0f4ff; border-left: 4px solid #6366f1; padding: 20px; "
    "border-radius: 4px; white-space: pre-line; font-size: 15px; line-height: 1.7;\">\n"
    "{{ $('Collect All Data1').first().json.linkedInPost }}\n"
    "</div>\n\n"

    "<hr style=\"border: 1px solid #e5e7eb; margin: 24px 0;\">\n\n"

    # Contra post
    "<h3 style=\"color: #059669; margin-bottom: 8px;\">Contra Post</h3>\n"
    "<p style=\"color: #6b7280; font-size: 13px; margin-bottom: 12px;\">Copy and paste this to your Contra profile.</p>\n"
    "<div style=\"background: #f0fdf4; border-left: 4px solid #059669; padding: 20px; "
    "border-radius: 4px; white-space: pre-line; font-size: 15px; line-height: 1.7;\">\n"
    "{{ $('Collect All Data1').first().json.contraPost }}\n"
    "</div>\n\n"

    "<hr style=\"border: 1px solid #e5e7eb; margin: 24px 0;\">\n\n"

    # Action buttons
    "<p style=\"color: #6b7280; font-size: 13px;\">Review the posts above. "
    "When ready, change status in Post Log to <strong>ready</strong> and the evening publisher will send them.</p>\n\n"

    "</div>"
)

email_node['parameters']['message'] = NEW_EMAIL
print("Updated: Email Preview1 — shows both HCTI card + Kie AI image separately")

# ─────────────────────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────────────────────
with open(FILE, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print("\n=== PATCH COMPLETE ===")

# ── Verify ────────────────────────────────────────────────────────────────────
with open(FILE, 'r', encoding='utf-8') as f:
    v = json.load(f)

def vnode(name): return next(n for n in v['nodes'] if n['name'] == name)

img_html  = vnode('Generate Image1')['parameters']['bodyParameters']['parameters'][0]['value']
collect   = vnode('Collect All Data1')['parameters']['jsCode']
email_msg = vnode('Email Preview1')['parameters']['message']

checks = [
    ("HCTI — no kieImageUrl background",  'kieImageUrl' not in img_html),
    ("HCTI — has title expression",        '$json.title'    in img_html),
    ("HCTI — has category expression",     '$json.category' in img_html),
    ("HCTI — no insight line from post",   'linkedInPost'  not in img_html),
    ("HCTI — no author/company text",      'Abdullah'      not in img_html and 'Trilles' not in img_html),
    ("Collect — has imageUrl (HCTI)",      'imageUrl'       in collect),
    ("Collect — has kieImageUrl",          'kieImageUrl'    in collect),
    ("Email — shows HCTI image",           'Branded Card'   in email_msg),
    ("Email — shows Kie image",            'Kie'            in email_msg),
    ("Email — has LinkedIn post",          'linkedInPost'   in email_msg),
    ("Email — has Contra post",            'contraPost'     in email_msg),
]
print("\nVerification:")
for label, ok in checks:
    print(f"  {'OK' if ok else 'FAIL'} — {label}")
