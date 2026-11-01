# Repository Guidelines

## Project Structure & Module Organization

- `app.py` defines the Flask application, page route, and `/api/chat` proxy to Ollama.
- `templates/index.html` contains the chat interface.
- `static/chat.js` manages conversation history, form submission, and error feedback; `static/style.css` provides responsive styling.
- `requirements.txt` lists Python dependencies; `README.md` documents setup.
- `.venv/` is an ignored local environment. No test directory currently exists.

## Build, Test, and Development Commands

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

These commands create an isolated environment, install Flask, and start the app at `http://127.0.0.1:5000`. No frontend build step is required.

Run `ollama pull gemma3:1b` to install the model. Start Ollama with `ollama serve` if it is not already running. The backend expects Ollama at `http://127.0.0.1:11434/api/chat`.

## Coding Style & Naming Conventions

Use four spaces for Python indentation and two spaces for HTML and JavaScript. Preserve existing CSS formatting. Use `snake_case` for Python functions, `UPPER_CASE` for constants, and `camelCase` for JavaScript variables and functions. Keep dependencies minimal and frontend code in plain HTML, CSS, and JavaScript. No formatter or linter is configured.

## Testing Guidelines

No automated test framework or coverage threshold is configured. Manually verify sending messages, multi-turn context, Enter versus Shift+Enter, New chat, and recovery after a failed request. Check narrow-screen layouts and missing-model or unavailable-Ollama errors.

For backend changes, use Flask’s test client to exercise input validation and error responses. Mock Ollama for deterministic automated tests; place future tests in `tests/test_*.py`. Document the test runner and command when introducing a suite. Python syntax can be checked with `python -m py_compile app.py`.

## Commit & Pull Request Guidelines

No Git history is available, so no existing commit convention can be inferred. Use concise imperative messages such as `Handle Ollama connection failures`. Keep commits focused.

Pull requests should describe the behavior change, reference related issues when applicable, and report validation performed and any limitations. Include screenshots for visible interface changes.

## Security & Configuration

Keep Flask bound to loopback for local use. Validate incoming messages and render chat text with `textContent`. Conversation history remains in page memory and clears on reload; avoid adding logging of chat content or committing local environments or secrets.
