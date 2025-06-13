const chatLog = document.getElementById('chat-log');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const imageInput = document.getElementById('image-input');
const uploadBtn = document.getElementById('upload-btn');

let conversationHistory = [];
const BACKEND_URL = "http://localhost:8000";

// Helper to append a message to the chat log
function appendMessage(content, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = sender === 'user' ? 'user-msg' : 'agent-msg';
    msgDiv.textContent = content;
    chatLog.appendChild(msgDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Handle file upload button
uploadBtn.addEventListener('click', () => {
    imageInput.click();
});

imageInput.addEventListener('change', async () => {
    if (imageInput.files.length > 0) {
        const file = imageInput.files[0];
        appendMessage(`[Image uploaded: ${file.name}]`, 'user');
        const formData = new FormData();
        formData.append('file', file);
        formData.append('message', userInput.value.trim());
        appendMessage('Analyzing image...', 'agent');
        try {
            const res = await fetch(`${BACKEND_URL}/image`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.extracted_text) {
                appendMessage(`[Extracted text]: ${data.extracted_text}`, 'agent');
            }
            appendMessage(data.response, 'agent');
            conversationHistory.push(userInput.value.trim() + "\n[Diagram Analysis]: " + (data.extracted_text || ""));
        } catch (err) {
            appendMessage('Error analyzing image.', 'agent');
        }
    }
});

// Handle chat form submit
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;
    appendMessage(text, 'user');
    conversationHistory.push(text);
    userInput.value = '';
    appendMessage('Thinking...', 'agent');
    try {
        const res = await fetch(`${BACKEND_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: conversationHistory.slice(0, -1) })
        });
        const data = await res.json();
        // Remove the placeholder 'Thinking...' message
        const lastMsg = chatLog.querySelector('.agent-msg:last-child');
        if (lastMsg && lastMsg.textContent === 'Thinking...') {
            lastMsg.remove();
        }
        appendMessage(data.response, 'agent');
    } catch (err) {
        appendMessage('Error contacting backend.', 'agent');
    }
});
