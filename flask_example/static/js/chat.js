document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('messages');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');

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
            body: JSON.stringify({message: message}),
        })
        .then(response => response.json())
        .then(data => {
            appendMessage('assistant', data.message);
        })
        .catch(error => console.error('Error:', error));
    }
});