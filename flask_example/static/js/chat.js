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
            body: JSON.stringify({ message: message, threadId: threadId })
        })
        .then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            function readStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        console.log('Stream complete');
                        return;
                    }

                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n\n');
                    
                    lines.forEach(line => {
                        if (line.startsWith('data: ')) {
                            const eventData = JSON.parse(line.slice(5));
                            handleEvent(eventData);
                        }
                    });

                    readStream();
                });
            }

            readStream();
        })
        .catch(error => console.error('Error:', error));
    }

    function handleEvent(data) {
        if (data.event === 'message') {
            appendMessage('assistant', data.content);
            threadId = data.threadId;
            console.log('Thread ID:', threadId);
        } else if (data.event === 'error') {
            console.error('Error:', data.content);
            appendMessage('assistant', 'An error occurred. Please try again.');
        }
    }
});