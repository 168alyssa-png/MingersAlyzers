CookieLab theme for your existing Flask + Ollama + Qwen project

1. Download and unzip CookieLab_Theme_Patch.zip.
2. Copy its three files, cookie-theme.css, cookie-mascot.png and apply_cookie_theme.py, into ~/codex-ollama/ (project root).
3. Open a NEW Terminal window and run:
   cd ~/codex-ollama
   python3 apply_cookie_theme.py
4. Restart Flask (Ctrl+C in the server Terminal, then):
   python3 -m flask --app app run --host 127.0.0.1 --port 5001
5. Visit http://127.0.0.1:5001 and press Command+Shift+R.

What it changes:
- Adds static/cookie-theme.css after existing style.css and installs static/cookie-mascot.png
- Changes the heading/tab labels to CookieLab/Recipe Library
- Adds a visual greeting above the chat window
- Does NOT change chat.js, docs.js, app.py, API keys, uploads, indexes, or model settings.

Test: chat, Search Web, file upload, clickable PDFs, indexing, delete, document Q&A.

If you don't like the theme, restore the original index.html from
.cookie-theme-backups/ and remove the cookie-theme.css link.
