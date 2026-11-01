# Local AI Chatbot (Lab Codex 3 & 4)

A private, local AI chatbot powered by Ollama, featuring document-based RAG and web search capabilities.

## Features
- **Chat with Qwen**: Private conversations using the `qwen3:1.7b` model.
- **Local RAG**: Upload PDF, DOCX, TXT, or MD files and ask questions about them.
- **Web Search**: Toggle real-time internet search via the Ollama Web Search API.
- **Document Manager**: View, upload, and delete local documents.

## Setup Instructions

### 1. Ollama Setup
Ensure Ollama is installed and running locally. Pull the required models:
```sh
ollama pull qwen3:1.7b
ollama pull nomic-embed-text
```

### 2. Environment Configuration
Create a `.env` file in the root directory and add your Ollama API Key:
```env
OLLAMA_API_KEY=your_api_key_here
```
(Refer to `.env.example` for the format).

### 3. Installation
```sh
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Running the Application
```sh
python app.py
```
The application will be available at `http://127.0.0.1:5001`.

## Project Structure
- `app.py`: Flask backend handling chat, RAG, and web search.
- `templates/`: HTML frontend.
- `static/`: CSS and JavaScript for the UI.
- `uploads/`: (Ignored by Git) Local storage for uploaded documents.
