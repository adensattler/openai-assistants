document.addEventListener('DOMContentLoaded', function () {
    const messagesContainer = document.getElementById('messages');
    const initialMessageContainer = document.getElementById('initialMessage');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    let threadId = null;

    // Add the initial message
    const initialMessage = `
### Welcome to Saucy's Employee Assistance Chatbot!

I’m here to help you prepare our delicious menu items and assist you with any questions about running the restaurant. You can ask me how to cook specific dishes, prepare orders, or handle restaurant operations. Here are some examples of what you can ask:

#### Cooking Instructions:
- "How do I make Sweet Baby Baked Beans?"
- "What’s the recipe for Green Chili Macaroni?"
- "How do I cook ribs?"

#### Preparing Orders:
- "What comes with the Wing Plate?"
- "How do I prepare a Three Meat Plate?"
- "What sides go with the Hotlink Plate?"

#### General Operations:
- "How do I set up the grill for cooking hotlinks?"
- "What’s the best way to season the catfish?"
- "How do I clean the deep fryer?"

#### Example Questions:
- "Can you give me the recipe for Teriyaki Parmesan Corn?"
- "How long should I bake the ribs?"
- "What’s included in the Two Meat Plate?"

Feel free to ask any questions you have, and I’ll provide you with the information you need to ensure our customers enjoy their meals. Let's get cooking!
    `;

    initialMessageContainer.innerHTML = marked.parse(initialMessage);

    chatForm.addEventListener('submit', function (e) {
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

        if (role === 'assistant') {
            messageDiv.innerHTML = marked.parse(text)
        } else {
            messageDiv.textContent = text
        }

        // messageDiv.textContent = text;
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