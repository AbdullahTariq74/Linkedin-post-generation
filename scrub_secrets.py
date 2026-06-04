"""Scan workflow JSONs and replace hardcoded credentials with placeholders."""
import json, re, glob, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

for filepath in glob.glob('n8n-workflows/*.json'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Replace Kie AI / any Bearer tokens
    content = re.sub(r'Bearer [a-f0-9A-F]{20,}', 'Bearer YOUR_KIE_AI_API_KEY', content)

    # Replace Tavily API keys
    content = re.sub(r'"api_key":\s*"[a-z0-9\-]{20,}"', '"api_key": "YOUR_TAVILY_API_KEY"', content)
    content = re.sub(r"api_key:\s*'[a-z0-9\-]{20,}'", "api_key: 'YOUR_TAVILY_API_KEY'", content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Scrubbed: {filepath}')
    else:
        print(f'Clean:    {filepath}')
