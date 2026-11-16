"""Apply a visual-only CookieLab theme to the existing Flask app.

Run from project root after extracting this ZIP into ~/codex-ollama:
    python3 apply_cookie_theme.py
Creates backups and never edits app.py/chat.js/docs.js.
"""
from pathlib import Path
import shutil
import sys
from datetime import datetime

root = Path(__file__).resolve().parent
html_file = root / 'templates' / 'index.html'
css_file = root / 'static' / 'style.css'
theme_file = root / 'static' / 'cookie-theme.css'
source_theme = root / 'cookie-theme.css'
source_mascot = root / 'cookie-mascot.png'
mascot_file = root / 'static' / 'cookie-mascot.png'
if not all(p.exists() for p in (html_file, css_file, source_theme, source_mascot)):
    sys.exit('Not in the Flask project root. Extract the ZIP into ~/codex-ollama and try again.')

backup_dir = root / '.cookie-theme-backups'
backup_dir.mkdir(exist_ok=True)
now = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(html_file, backup_dir / f'index_{now}.html')
if theme_file.exists():
    shutil.copy2(theme_file, backup_dir / f'cookie_theme_{now}.css')
shutil.copy2(source_theme, theme_file)
shutil.copy2(source_mascot, mascot_file)

html = html_file.read_text(encoding='utf-8')
link_tag = '<link rel="stylesheet" href="/static/cookie-theme.css">'
if link_tag not in html:
    old_link = '<link rel="stylesheet" href="/static/style.css">'
    if old_link not in html:
        sys.exit('Could not find the existing stylesheet link. Theme copied, but HTML was not changed.')
    html = html.replace(old_link, old_link + '\n    ' + link_tag, 1)

replacements = {
    '<title>Local AI Chat</title>': '<title>CookieLab | AI Recipe Assistant</title>',
    '<span class="brand-label">LOCAL AI</span>': '<span class="brand-label">✦ YOUR LOCAL BAKING AI</span>',
    '<h1>Chat with Qwen</h1>': '<h1>CookieLab: Your AI Baking Buddy</h1>',
    '<p class="app-subtitle">A private conversation with your local Ollama model.</p>': '<p class="app-subtitle">From crispy edges to chewy centres — explore sweet ideas with Qwen and your favourite recipes.</p>',
    'data-tab="chat-tab">Chat</button>': 'data-tab="chat-tab">🍪 Recipe Chat</button>',
    'data-tab="docs-tab">Document Collection</button>': 'data-tab="docs-tab">📚 Recipe Library</button>',
    '<h2>Local Documents</h2>': '<h2>Your Recipe Library</h2>',
    '<p>Upload documents to give the AI more context. Supported: PDF, DOCX, TXT, MD.</p>': '<p>Upload your favourite recipes and baking guides to help Qwen make better suggestions. Supports PDF, DOCX, TXT and MD.</p>',
    '<p>Drag & Drop files here</p>': '<p>Drop your recipe files here</p>',
    '<button id="browse-btn">Browse Files</button>': '<button id="browse-btn">Choose Files</button>',
    'placeholder="Type your message..."': 'placeholder="Ask for chewier cookies, less sugar, baking tips..."',
    'id="send-btn">Send</button>': 'id="send-btn">Ask Qwen</button>',
}
for before, after in replacements.items():
    html = html.replace(before, after)

intro = '''<div class="chat-intro" aria-label="CookieLab baking assistant">
                        <span class="chat-intro-icon" aria-hidden="true">👩‍🍳</span>
                        <div class="chat-intro-text"><strong>Let's bake something wonderful!</strong><span>Ask about ingredients, texture, sweetness or recipe changes.</span></div>
                    </div>'''
if 'class="chat-intro"' not in html:
    target = '<div id="chat-container">'
    if target in html:
        html = html.replace(target, target + '\n                    ' + intro, 1)

html_file.write_text(html, encoding='utf-8')
ignore = root / '.gitignore'
if ignore.exists():
    content = ignore.read_text(encoding='utf-8')
    if '.cookie-theme-backups/' not in content:
        ignore.write_text(content.rstrip() + '\n.cookie-theme-backups/\n', encoding='utf-8')

print('CookieLab theme installed!')
print('Updated only templates/index.html, static/cookie-theme.css, static/cookie-mascot.png and .gitignore.')
print('Your original index.html backup is in .cookie-theme-backups/.')
print('No Flask API, JavaScript, document storage, or AI code was modified.')
print('Restart Flask and hard-refresh the browser (Command+Shift+R).')
