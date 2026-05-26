"""
Update the Generate Image node HTML template:
  - Remove author byline
  - Show a real insight/stat line pulled from the LinkedIn post
  - Adaptive font size (shorter title = bigger text)
  - Better glow effects and visual hierarchy
  - Only touches the Generate Image node — nothing else
"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILE = r"C:\Users\abdta\Desktop\Portfolio\n8n-workflows\workflow-1a-morning-generator.json"

with open(FILE, 'r', encoding='utf-8') as f:
    wf = json.load(f)

image_node = next(n for n in wf['nodes'] if n['name'] == 'Generate Image')

# ─────────────────────────────────────────────────────────────────────────────
# Expressions used in the template
# All are written so that NO { } braces appear inside the {{ }} blocks
# (only [] and arrow functions without body braces) — this keeps n8n's
# expression parser from getting confused.
# ─────────────────────────────────────────────────────────────────────────────

# Adaptive font size based on title length
FONT_SIZE = "{{ ($json.title||'').length<55 ? '50' : ($json.title||'').length<85 ? '43' : '37' }}"

# Second meaningful line of the LinkedIn post (skips blank lines & short lines)
# Uses [1] — 0-indexed, so this is the 2nd item with length > 35 chars
# Falls back to '' if not found
INSIGHT = "{{ ($json.linkedInPost||'').split('\\n').map(l=>l.trim()).filter(l=>l.length>35)[1]?.slice(0,155)||'' }}"

# ─────────────────────────────────────────────────────────────────────────────
# HTML template
# ─────────────────────────────────────────────────────────────────────────────
NEW_HTML = (
    "=<div style=\"font-family:'Inter',Arial,sans-serif;"
    "background:linear-gradient(135deg,#0a0e1a 0%,#1a1f3a 100%);"
    "color:white;width:1200px;height:628px;display:flex;"
    "flex-direction:column;padding:64px 80px;box-sizing:border-box;"
    "position:relative;overflow:hidden;\">"

    # ── Background glows ──────────────────────────────────────────────────────
    "<div style=\"position:absolute;top:-100px;right:-100px;width:520px;height:520px;"
    "background:radial-gradient(circle,rgba(99,102,241,0.2) 0%,transparent 65%);"
    "border-radius:50%;\"></div>"

    "<div style=\"position:absolute;bottom:-80px;left:-60px;width:420px;height:420px;"
    "background:radial-gradient(circle,rgba(59,130,246,0.13) 0%,transparent 65%);"
    "border-radius:50%;\"></div>"

    "<div style=\"position:absolute;top:38%;right:50px;width:280px;height:280px;"
    "background:radial-gradient(circle,rgba(139,92,246,0.09) 0%,transparent 65%);"
    "border-radius:50%;\"></div>"

    # ── Main content ─────────────────────────────────────────────────────────
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
    f"<div style=\"font-size:{FONT_SIZE}px;font-weight:800;line-height:1.15;"
    "margin-bottom:28px;max-width:860px;word-wrap:break-word;\">{{ $json.title }}</div>"

    # Accent bar
    "<div style=\"width:80px;height:4px;"
    "background:linear-gradient(90deg,#6366f1,#3b82f6);"
    "border-radius:4px;margin-bottom:28px;\"></div>"

    # Insight line pulled from the post
    f"<div style=\"font-size:19px;color:rgba(255,255,255,0.65);"
    "max-width:820px;line-height:1.65;font-weight:400;\">"
    f"{INSIGHT}"
    "</div>"

    "</div>"   # end main content

    # ── Bottom decorative bar ─────────────────────────────────────────────────
    "<div style=\"position:relative;z-index:1;display:flex;align-items:center;"
    "gap:6px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.08);\">"
    "<div style=\"width:32px;height:3px;background:#6366f1;border-radius:2px;\"></div>"
    "<div style=\"width:20px;height:3px;background:#3b82f6;border-radius:2px;opacity:0.6;\"></div>"
    "<div style=\"width:10px;height:3px;background:rgba(255,255,255,0.3);border-radius:2px;\"></div>"
    "</div>"

    "</div>"   # end outer wrapper
)

# ─────────────────────────────────────────────────────────────────────────────
# Apply & save
# ─────────────────────────────────────────────────────────────────────────────
image_node['parameters']['bodyParameters']['parameters'][0]['value'] = NEW_HTML

with open(FILE, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print("Updated: Generate Image HTML template")
print("  - Removed author/company byline")
print("  - Title headline with adaptive font size (37/43/50px)")
print("  - Insight line: 2nd meaningful sentence from the LinkedIn post")
print("  - 3-blob glow background (indigo + blue + violet)")
print("  - Indigo/blue accent bar")
print("  - Decorative bottom bar")
print("  - Nothing else in the workflow changed")

# ── Verify ────────────────────────────────────────────────────────────────────
with open(FILE, 'r', encoding='utf-8') as f:
    verify = json.load(f)

node = next(n for n in verify['nodes'] if n['name'] == 'Generate Image')
html_val = node['parameters']['bodyParameters']['parameters'][0]['value']
checks = [
    ("Starts with =",          html_val.startswith('=')),
    ("Has category expression", '{{ $json.category }}' in html_val),
    ("Has title expression",    '{{ $json.title }}'    in html_val),
    ("Has insight expression",  'linkedInPost'         in html_val),
    ("Adaptive font size",      'length<55'            in html_val),
    ("No author byline",        'Abdullah Tariq'  not  in html_val),
    ("No Trilles AI",           'Trilles AI'      not  in html_val),
]
print("\nVerification:")
for label, ok in checks:
    print(f"  {'OK' if ok else 'FAIL'} — {label}")
