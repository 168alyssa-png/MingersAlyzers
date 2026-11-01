const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatWindow = document.getElementById('chat-window');
const webSearchCheckbox = document.getElementById('web-search-checkbox');

let messages = [];

function appendMessage(role, text, isError = false) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    
    if (isError) {
        msgDiv.classList.add('error');
        msgDiv.textContent = text;
    } else {
        msgDiv.classList.add(role);
        if (role === 'assistant') {
            // Use marked.parse for safe Markdown rendering
            // This handles bold, lists, headings and a lot more
            msgDiv.innerHTML = marked.parse(text);
        } else {
            msgDiv.textContent = text;
        }
    }
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    const useWebSearch = webSearchCheckbox.checked;

    appendMessage('user', text);
    messages.push({ role: 'user', content: text });
    userInput.value = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                messages: messages,
                web_search: useWebSearch 
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'An unknown error occurred');
        }

        const assistantText = data.message.content;
        appendMessage('assistant', assistantText);
        messages.push({ role: 'assistant', content: assistantText });

    } catch (err) {
        appendMessage('error', 'Error: ' + err.message, true);
    }
});
