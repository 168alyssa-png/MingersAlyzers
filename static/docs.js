const DB_NAME = 'OllamaDocsDB';
const STORE_NAME = 'documents';

async function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);
        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

async function saveFileLocally(file) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    return new Promise((resolve, reject) => {
        const request = store.add({
            name: file.name,
            type: file.type || 'unknown',
            size: file.size,
            timestamp: Date.now()
        });
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
}

async function getAllFiles() {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    return new Promise((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

async function deleteFileLocally(id) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    return new Promise((resolve, reject) => {
        const request = store.delete(id);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
}

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');
const docsList = document.getElementById('docs-list');
const docsTable = document.getElementById('docs-table');
const emptyState = document.getElementById('empty-state');
const feedback = document.getElementById('upload-feedback');

const ALLOWED_TYPES = [
    'application/pdf', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain', 
    'text/markdown'
];
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt', '.md'];

function formatSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showFeedback(text, isError = false) {
    feedback.textContent = text;
    feedback.className = isError ? 'feedback-error' : 'feedback-success';
    setTimeout(() => { feedback.textContent = ''; }, 5000);
}

async function updateUI() {
    const files = await getAllFiles();
    docsList.innerHTML = '';
    if (files.length === 0) {
        emptyState.style.display = 'block';
        docsTable.style.display = 'none';
    } else {
        emptyState.style.display = 'none';
        docsTable.style.display = 'table';
        files.forEach(file => {
            const row = document.createElement('tr');
            
            // Fix: Create the cell using HTML string, but keep a reference for updating
            row.innerHTML = `
                <td><a href="/api/files/${encodeURIComponent(file.name)}" target="_blank" class="doc-link">${file.name}</a></td>
                <td>${formatSize(file.size)}</td>
                <td class="status-cell">Checking...</td>
                <td><button class="remove-btn" data-id="${file.id}">&times;</button></td>
            `;
            
            docsList.appendChild(row);
            
            const cell = row.querySelector('.status-cell');
            
            // Async check indexing status with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

            fetch(`/api/index-status/${encodeURIComponent(file.name)}`, { signal: controller.signal })
                .then(res => {
                    clearTimeout(timeoutId);
                    if (!res.ok) throw new Error('Server error');
                    return res.json();
                })
                .then(data => {
                    cell.textContent = data.status;
                })
                .catch((err) => {
                    console.error(`Status check failed for ${file.name}:`, err);
                    cell.textContent = err.name === 'AbortError' ? 'Timeout' : 'Failed';
                });
        });
        
        document.querySelectorAll('.remove-btn').forEach(btn => {
            btn.onclick = async (e) => {
                const id = parseInt(e.target.getAttribute('data-id'));
                const allFiles = await getAllFiles();
                const fileObj = allFiles.find(f => f.id === id);
                if (!fileObj) return;
                const filename = fileObj.name;
                
                try {
                    const resp = await fetch('/api/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filename })
                    });
                    if (!resp.ok) throw new Error('Backend delete failed');
                } catch (e) {
                    console.error('Backend delete error:', e);
                }

                await deleteFileLocally(id);
                updateUI();
            };
        });
    }
}

async function handleFiles(files) {
    const fileList = Array.from(files);
    let uploadedCount = 0;
    let errorCount = 0;

    for (const file of fileList) {
        const isAllowed = ALLOWED_TYPES.includes(file.type) || 
                         ALLOWED_EXTENSIONS.some(ext => file.name.toLowerCase().endsWith(ext));
        
        if (isAllowed) {
            try {
                await saveFileLocally(file);
                
                const formData = new FormData();
                formData.append('file', file);
                
                const resp = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (!resp.ok) throw new Error('Indexing failed');
                
                uploadedCount++;
            } catch (e) {
                console.error(e);
                errorCount++;
            }
        } else {
            errorCount++;
        }
    }

    if (uploadedCount > 0 && errorCount === 0) {
        showFeedback(`Successfully indexed ${uploadedCount} file(s).`);
    } else if (uploadedCount > 0 && errorCount > 0) {
        showFeedback(`Indexed ${uploadedCount} file(s), but ${errorCount} failed.`, true);
    } else {
        showFeedback('No valid files were uploaded.', true);
    }
    updateUI();
}

browseBtn.onclick = () => fileInput.click();
fileInput.onchange = (e) => handleFiles(e.target.files);
dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add('dragover'); };
dropZone.ondragleave = () => { dropZone.classList.remove('dragover'); };
dropZone.ondrop = (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
};

updateUI();
