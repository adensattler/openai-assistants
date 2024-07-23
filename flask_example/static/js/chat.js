document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('messages');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    let threadId = null;

    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (message) {
            appendMessage('user', message);
            sendMessage(message);
            userInput.value = '';
        }
    });

    function appendMessage(role, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = role === 'user' ? 'userMessage' : 'assistantMessage';
        messageDiv.textContent = text;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function sendMessage(message) {
        fetch('/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message, threadId: threadId }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                appendMessage('assistant', 'Error: ' + data.error);
            } else {
                appendMessage('assistant', data.response);
                threadId = data.threadId;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            appendMessage('assistant', 'An error occurred while processing your request.');
        });
    }
});