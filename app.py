import os
import requests
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory
from PyPDF2 import PdfReader
from docx import Document
from dotenv import load_dotenv

# Explicitly load .env from the application directory
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)

# Local Ollama API (for chat and embeddings)
OLLAMA_LOCAL_URL = "http://localhost:11434"
# Cloud Ollama API (for web search)
OLLAMA_CLOUD_URL = "https://ollama.com/api/web_search"

CHAT_MODEL = "qwen3:1.7b"
EMBED_MODEL = "nomic-embed-text"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Simple local vector store in memory for prototype
vector_store = [] # List of { 'embedding': [], 'text': '', 'filename': '' }

def get_embedding(text):
    try:
        response = requests.post(f"{OLLAMA_LOCAL_URL}/api/embeddings", 
                                json={"model": EMBED_MODEL, "prompt": text}, 
                                timeout=30)
        response.raise_for_status()
        return response.json().get("embedding")
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def extract_text(file_path, filename):
    ext = os.path.splitext(filename)[1].lower()
    text = ""
    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif ext == '.docx':
            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        elif ext in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        return text
    except Exception as e:
        print(f"Extraction error for {filename}: {e}")
        return ""

def chunk_text(text, size=500):
    return [text[i:i+size] for i in range(0, len(text), size)]

def perform_web_search(query):
    if not OLLAMA_API_KEY:
        print("DEBUG: OLLAMA_API_KEY is missing from environment")
        raise Exception("OLLAMA_API_KEY not found in environment. Please check your .env file.")
    
    try:
        headers = {
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "max_results": 5
        }
        
        print(f"DEBUG: Requesting web search for query: {query}")
        response = requests.post(
            OLLAMA_CLOUD_URL, 
            json=payload, 
            headers=headers,
            timeout=30
        )
        
        print(f"DEBUG: Web search response status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        print(f"DEBUG: Successfully retrieved {len(results)} results")
        return results
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: HTTP Error during web search: {e.response.status_code} - {e.response.text}")
        raise e
    except Exception as e:
        print(f"DEBUG: Unexpected error during web search: {type(e).__name__} - {str(e)}")
        raise e

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    save_path = os.path.join("uploads", file.filename)
    file.save(save_path)

    text = extract_text(save_path, file.filename)
    if not text or not text.strip():
        return jsonify({"error": "Could not extract readable text from file"}), 422

    chunks = chunk_text(text)
    indexed_count = 0
    for chunk in chunks:
        embedding = get_embedding(chunk)
        if embedding:
            vector_store.append({
                'embedding': embedding,
                'text': chunk,
                'filename': file.filename
            })
            indexed_count += 1
    
    return jsonify({"message": f"Indexed {indexed_count} chunks from {file.filename}", "chunks": indexed_count})

@app.route("/api/index-existing", methods=["POST"])
def index_existing():
    if not os.path.exists("uploads"):
        return jsonify({"error": "Uploads folder not found"}), 404
        
    files = [f for f in os.listdir("uploads") if os.path.isfile(os.path.join("uploads", f))]
    total_indexed = 0
    
    for filename in files:
        if any(item['filename'] == filename for item in vector_store):
            continue
            
        file_path = os.path.join("uploads", filename)
        text = extract_text(file_path, filename)
        if text and text.strip():
            chunks = chunk_text(text)
            for chunk in chunks:
                embedding = get_embedding(chunk)
                if embedding:
                    vector_store.append({
                        'embedding': embedding,
                        'text': chunk,
                        'filename': filename
                    })
                    total_indexed += 1
                    
    return jsonify({"message": f"Indexed {total_indexed} chunks from existing files."})

@app.route("/api/delete", methods=["POST"])
def delete_file():
    data = request.json
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "Filename required"}), 400
    
    global vector_store
    vector_store = [item for item in vector_store if item['filename'] != filename]
    
    file_path = os.path.join("uploads", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    return jsonify({"message": f"Removed {filename} from index"})

@app.route("/api/files/<filename>")
def serve_file(filename):
    filename = os.path.basename(filename)
    file_path = os.path.join("uploads", filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory("uploads", filename)

@app.route("/api/index-status/<filename>")
def index_status(filename):
    filename = os.path.basename(filename)
    count = sum(1 for item in vector_store if item['filename'] == filename)
    if count > 0:
        return jsonify({"status": f"Indexed - {count} chunks"})
    return jsonify({"status": "Not Indexed"})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])
    use_web_search = data.get("web_search", False)

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    user_query = messages[-1]['content']
    
    context_text = ""
    sources_list = []
    
    # 1. Context Gathering
    is_summarizing = any(phrase in user_query.lower() for phrase in ["summarize", "summary of", "what is the main idea of"])
    is_asking_about_collection = any(phrase in user_query.lower() for phrase in [
        "what documents", "what papers", "my collection", "list my files", 
        "what are the documents", "which files", "what is in my collection"
    ])
    
    if is_asking_about_collection:
        unique_docs = {}
        for item in vector_store:
            fname = item['filename']
            if fname not in unique_docs:
                unique_docs[fname] = item['text'][:200].strip() + "..."
        
        if unique_docs:
            doc_list_str = "\n".join([f"- {name}: {desc}" for name, desc in unique_docs.items()])
            context_text = f"The user's uploaded document collection currently contains these files:\n{doc_list_str}"
        else:
            context_text = "The user's document collection is currently empty."
    
    elif is_summarizing:
        # For summarization, we try to find all chunks belonging to the mentioned document
        target_doc = None
        for fname in [item['filename'] for item in vector_store]:
            if fname.lower() in user_query.lower():
                target_doc = fname
                break
        
        if target_doc:
            # Collect first few and last few chunks to give a representative summary
            doc_chunks = [item['text'] for item in vector_store if item['filename'] == target_doc]
            if doc_chunks:
                # Combine first 3 and last 3 chunks to stay within context window
                summary_ctx = "\n".join(doc_chunks[:3]) + "\n... [content truncated] ...\n" + "\n".join(doc_chunks[-3:])
                context_text = f"Document Content from {target_doc}:\n{summary_ctx}"
                sources_list.append({"title": target_doc, "url": None})
        else:
            # If no specific doc mentioned, try similarity search as fallback
            query_embed = get_embedding(user_query)
            if query_embed and vector_store:
                similarities = []
                for item in vector_store:
                    sim = cosine_similarity(query_embed, item['embedding'])
                    similarities.append((sim, item))
                similarities.sort(key=lambda x: x[0], reverse=True)
                top_chunks = [item for sim, item in similarities[:3] if sim > 0.3]
                if top_chunks:
                    rag_ctx = "\n\n".join([f"Source: {c['filename']}\nContent: {c['text']}" for c in top_chunks])
                    context_text += rag_ctx
                    for c in top_chunks:
                        sources_list.append({"title": c['filename'], "url": None})

    else:
        # Normal Chat / RAG / Web Search
        if use_web_search:
            try:
                search_results = perform_web_search(user_query)
                if search_results:
                    search_ctx = ""
                    for r in search_results:
                        search_ctx += f"Source: {r['title']} ({r['url']})\nContent: {r['content']}\n\n"
                        sources_list.append({"title": r['title'], "url": r['url']})
                    context_text += "--- Web Search Results ---\n" + search_ctx + "\n\n"
            except Exception as e:
                print(f"Web Search integration failure: {str(e)}")
                return jsonify({"error": f"Web search failed: {str(e)}"}), 500

        query_embed = get_embedding(user_query)
        if query_embed and vector_store:
            similarities = []
            for item in vector_store:
                sim = cosine_similarity(query_embed, item['embedding'])
                similarities.append((sim, item))
            
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_chunks = [item for sim, item in similarities[:3] if sim > 0.3]
            
            if top_chunks:
                rag_ctx = ""
                for c in top_chunks:
                    rag_ctx += f"Source: {c['filename']}\nContent: {c['text']}\n\n"
                    sources_list.append({"title": c['filename'], "url": None})
                context_text += "--- Local Documents ---\n" + rag_ctx

    # 2. Prompt Augmentation
    system_prompt = (
        "You are a helpful AI assistant. Use the provided excerpts to answer the user's question. "
        "When using information from a source, explicitly mention the source filename or URL. "
        "If the answer is not in the provided context, say you don't know based on the files/web, but can try answering from general knowledge. "
        "Do not invent content. "
        "Provide your answer in a clear, well-structured format using Markdown (headings, lists, paragraphs). "
        f"\n\nContext:\n{context_text if context_text else 'No specific context available.'}"
    )
    
    rag_messages = [{"role": "system", "content": system_prompt}] + messages

    payload = {
        "model": CHAT_MODEL,
        "messages": rag_messages,
        "stream": False
    }

    try:
        response = requests.post(f"{OLLAMA_LOCAL_URL}/api/chat", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if sources_list:
            # Use a set to avoid repeating filenames in the Sources section
            unique_sources = []
            seen_titles = set()
            for s in sources_list:
                if s['title'] not in seen_titles:
                    unique_sources.append(s)
                    seen_titles.add(s['title'])
            
            sources_md = "\n\n**Sources:**\n"
            for s in unique_sources:
                if s['url']:
                    sources_md += f"- [{s['title']}]({s['url']})\n"
                else:
                    sources_md += f"- {s['title']}\n"
            result['message']['content'] += sources_md
            
        return jsonify(result)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Ollama is not running. Please start 'ollama serve'."}), 503
    except requests.exceptions.RequestException as e:
        print(f"Chat API error: {e}")
        return jsonify({"error": f"Error communicating with Ollama: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
